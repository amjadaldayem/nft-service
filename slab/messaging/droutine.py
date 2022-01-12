"""
High level DRoutine module, taking use of the lower level `messages` structures.
"""
import abc
import inspect
import logging
import signal
from typing import Optional, Union, Iterable, Type

from orjson import orjson
from pydantic import BaseModel

from slab import messaging
from slab.errors import notify_error

logger = logging.getLogger(__name__)

OK = -1


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class DRoutineBaseParams(BaseModel):
    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class DRoutine(abc.ABC):
    """
    Distributed routine. Supposed to run off in a separate worker via some queuing
    mechanism.
    """
    VTT = 3  # Small amount of seconds to add to the TIMEOUT to set as the visibility timeout

    TIMEOUT = 15

    queue = None
    task_name = None
    # Class of the `params`,
    # - None: if no params to pass
    # - DRoutineBaseParams: any derived class from DRoutineBaseParams
    params_class = DRoutineBaseParams

    def __call__(self, params: Optional[DRoutineBaseParams] = None, delay=0, timeout=None):
        if not self.queue:
            raise IOError(
                "Queue not set. Please call register to bind a queue to this task."
            )

        self.validate_params(params)

        self.queue.send_message_dict(
            {'params': params.json() if params else None},
            message_attributes={
                'task_name': {
                    'DataType': 'String',
                    'StringValue': self.task_name
                },
                'timeout': {
                    'DataType': 'Number',
                    'StringValue': str(timeout or self.TIMEOUT)
                }
            },
            delay=delay,
        )

    @classmethod
    def validate_params(cls, params):
        if cls.params_class:
            if not isinstance(params, cls.params_class):
                raise TypeError(
                    "The passed in params class type does not match `params_class`."
                )
        else:
            if params:
                raise TypeError("No params allowed since `params_class` is None.")

    @abc.abstractmethod
    def run(self, params: Optional[DRoutineBaseParams]) -> Union[int, float]:
        """

        Args:
            params: Note that we only support `value types`, such as dataclass
                namedtuple, datetime etc in the params dict. Other complex objects
                are not guaranteed to work correctly.

        Returns:
            Any value < 0 (use constant OK) will mark the message to be deleted
            from the queue. If 0, will immeidately make the message visible back
            in the queue. If any value > 0, will change the visibility timeout
            for the message.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def on_timeout(self, timeout) -> Union[int, float]:
        """

        Args:
            timeout:

        Returns:
            Any value < 0 (use constant OK) will mark the message to be deleted
            from the queue. If 0, will immeidately make the message visible back
            in the queue. If any value > 0, will change the visibility timeout
            for the message.
        """
        logger.warning("Task %s timed out (%s).", timeout)
        return OK


class Registry:

    def __init__(self):
        self.task_classes = {}

    def register(self, task_name, t):
        self.task_classes[task_name] = t

    def unregister(self, task_name):
        if task_name in self.task_classes:
            del self.task_classes[task_name]


registry = Registry()


def map_droutines_to_queue(queue: messaging.CQueue, *droutines: Iterable[Type[DRoutine]]):
    for cls in droutines:
        cls.task_name = inspect.getmodule(cls).__name__ + '.' + cls.__name__
        attributes = queue.attributes
        queue_visibility_timeout = int(attributes['VisibilityTimeout'])
        cls.queue = queue
        registry.register(cls.task_name, cls)
        logger.info("Registered DRoutine %s on %s", cls.task_name, queue)
        if queue_visibility_timeout < cls.TIMEOUT:
            logger.warning(
                "Default visibility timeout for %s is %s, which is "
                "shorter than the set TIMEOUT value %s for DRoutine %s",
                queue.url,
                queue_visibility_timeout,
                cls.TIMEOUT,
                cls.task_name
            )


def handle_task_timeout(instance, ret, task_timeout, sig, frame):
    ret[0] = instance.on_timeout(task_timeout)


def handler_func(queue: messaging.CQueue, message: messaging.CMessage, worker_type):
    signal.alarm(0)
    message_attributes = message.message_attributes
    metadata = {
        'message': {
            'id': message.id,
            'sender_id': message.sender_id,
            'body': message.body,
            'message_attributes': message_attributes
        }
    }
    if 'task_name' not in message_attributes:
        error_message = f"Task name not found in message. Skipping."
        # Deletes the message
        notify_error(
            messaging.MessagingException(error_message),
            metadata=metadata
        )
        return True
    try:
        task_name = message_attributes['task_name']['StringValue']
    except KeyError:
        task_name = None
    if task_name not in registry.task_classes:
        error_message = "Task name not found in registry. Please make sure to" \
                        "call init() method for the task class."
        # Deletes the message
        notify_error(
            messaging.MessagingException(error_message),
            metadata=metadata
        )
        return True

    task_class = registry.task_classes[task_name]

    # Just remove the message and fail early if the message validation
    # fails.
    try:
        serialized_params = message.body['params']
        params = (
            task_class.params_class.parse_raw(serialized_params)
            if task_class.params_class else None
        )
        task_class.validate_params(params)
    except Exception as e:
        notify_error(e, metadata=metadata)
        return False

    queue_visibility_timeout = int(queue.attributes['VisibilityTimeout'])
    try:
        task_timeout = int(message_attributes['timeout']['StringValue'])
        visibility_timeout_override = task_timeout + task_class.VTT
        default_vt = (visibility_timeout_override == queue_visibility_timeout)
    except KeyError:
        default_vt = True
        visibility_timeout_override = queue_visibility_timeout
        task_timeout = task_class.TIMEOUT
        logger.info(
            "Timeout override not found for this run of %s."
            "Using default.",
            task_name, task_timeout
        )

    instance = task_class()
    ret = -1

    def _handle_task_timeout(sig, frame):
        raise TimeoutError

    if not default_vt:
        # Saves 1 API call here, if the visibility timeout is the same
        message.change_visibility(visibility_timeout_override)
    try:
        signal.signal(
            signal.SIGALRM,
            _handle_task_timeout
        )
        signal.alarm(task_timeout)
        ret = instance.run(params)
    except TimeoutError:
        ret = instance.on_timeout(task_timeout)
    except Exception as e:
        # At this point we wait for the message visibility timeout to
        # let it retry
        signal.alarm(0)
        notify_error(e, metadata=metadata)
        return False

    if ret >= 0:
        message.change_visibility(ret)
        return False
    else:
        return True


def droutine_worker_start(queues: Iterable[messaging.CQueue], max_messages_to_receive, worker_type):
    messaging.message_loop(
        queues,
        handler_func=handler_func,
        worker_type=worker_type,
        max_messages_to_receive=max_messages_to_receive,
        shutdown=messaging.shutdown_on([
            signal.SIGINT,
            signal.SIGTERM,
        ])
    )
