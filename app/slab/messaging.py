# -*- coding: utf-8 -*-
import datetime
import logging
import signal
import threading
import time
from operator import attrgetter
from typing import List, Tuple, Optional

import boto3
import msgpack as msgpack
import orjson

logger = logging.getLogger(__name__)

SIGNAL_NAMES = {
    signal.SIGINT: "SIGINT",
    signal.SIGTERM: "SIGTERM",
}


class MessagingException(Exception):

    def __init__(self, *args):
        super(MessagingException, self).__init__(*args)


def _unregistered(queue: 'CQueue', message: 'CMessage'):
    logger.warning(
        'Handler not registered for queue %s. Message received: %s .',
        queue,
        orjson.dumps(message).decode('utf8')
    )


unregistered = _unregistered


class CMessage(object):
    """
    Thin wrapper of SQS message. Only exposing minimal properties methods that
    matter.
    """

    def __init__(self, sqs_message):
        self._message = sqs_message
        self._body = msgpack.loads(self._message.body)
        # Sender Id
        # For an IAM user, returns the IAM user ID,
        #   for example ABCDEFGHI1JKLMNOPQ23R
        # For an IAM role, returns the IAM role ID,
        #   for example ABCDE1F2GH3I4JK5LMNOP:i-a123b456
        self._sender_id = self._message.attributes['SenderId']
        # In milliseconds
        self._sent_timestamp = self._message.attributes['SentTimestamp']

        approx_receive_count = self._message.attributes.get(
            "ApproximateReceiveCount"
        )
        try:
            self._approximate_receive_count = int(approx_receive_count)
        except TypeError:
            self._approximate_receive_count = None

        self._md5_of_body = self._message.md5_of_body

    def change_visibility(self, seconds):
        """
        Extends the message visibility timeout by certain seconds.
        Args:
            seconds (int): If set to 0, it will kick back the message.

        Returns:

        """

        self._message.change_visibility(VisibilityTimeout=seconds)

    def delete(self):
        """
        Deletes the message from the queue.
        Returns:

        """
        self._message.delete()

    @property
    def body(self):
        """

        Returns:
            dict: the content of the message
        """
        return self._body

    @property
    def id(self):
        return self._message.message_id

    @property
    def sender_id(self):
        return self._sender_id

    @property
    def sent_timestamp(self):
        """
        Epoch timestamp in milliseconds
        Returns:

        """
        return self._sent_timestamp

    @property
    def sent_time(self):
        epoch = self.sent_timestamp / 1000
        dt = datetime.datetime.fromtimestamp(epoch)
        return time.mktime(dt.timetuple())

    @property
    def md5(self):
        return self._md5_of_body


class CQueue(object):

    def __init__(self,
                 url,
                 name,
                 priority=50,
                 endpoint=None):
        """

        Args:
            url (str):
                URL to the SQS queue
            name (str):
                Identifier for this queue in the current worker. Not the actual
                queue name.
            priority (int):
                The priority for the queue, higher priority queue gets higher
                probability of being polled.
        """
        # You should either have Role based permissions setup or
        # have the correct AWS credentials file or env vars setup, with Region
        sqs = boto3.session.Session().resource('sqs', endpoint_url=endpoint)
        self._queue_url = url
        self._queue = sqs.Queue(url)
        self._name = name
        self._priority = priority

    def receive_one_message(self, visibility_timeout=None, poll_wait=0):
        """

        Args:
            visibility_timeout (int|None):
            poll_wait (int)
        Returns:
            CMessage | None
        """
        kwargs = {
            'AttributeNames': ['SenderId',
                               'SentTimestamp',
                               'ApproximateReceiveCount'],
            'MessageAttributeNames': ['all'],
            'MaxNumberOfMessages': 1,
            'WaitTimeSeconds': poll_wait,
        }
        if visibility_timeout is not None:
            kwargs['VisibilityTimeout'] = visibility_timeout

        # meta_data = {"queue": {"name": self.name, "url": self._queue_url}}

        sqs_messages = self._queue.receive_messages(**kwargs)

        if visibility_timeout == 0:
            # Simply releasing the message back to queue, return nothing
            return None

        return CMessage(sqs_messages[0]) if sqs_messages else None

    def send_message_dict(self, message_dict, delay=0):
        """
        Sends a dict message body.
        Args:
            message_dict (dict):
                Message body, a dict.
            delay (int):
                Seconds to delay.
        Returns:
            dict: {
                    'MD5OfMessageBody': 'string',
                    'MD5OfMessageAttributes': 'string',
                    'MessageId': 'string',
                    'SequenceNumber': 'string'
                  }
        """
        return self._queue.send_message(
            MessageBody=msgpack.dumps(message_dict),
            DelaySeconds=delay
        )

    @property
    def priority(self):
        return self._priority

    @property
    def name(self):
        return self._name

    @property
    def url(self):
        return self._queue.url

    @property
    def messages_in_queue(self):
        """
        No throws
        Returns:
         """
        resp = self._queue.meta.client.get_queue_attributes(
            QueueUrl=self.url,
            AttributeNames=[
                'ApproximateNumberOfMessages',
                'ApproximateNumberOfMessagesNotVisible',
            ],
        )
        attrs = resp.get('Attributes')

        visible_messages = int(attrs.get("ApproximateNumberOfMessages", 0))
        in_flight_messages = int(
            attrs.get(
                "ApproximateNumberOfMessagesNotVisible", 0
            )
        )

        return visible_messages + in_flight_messages

    @property
    def dlq(self) -> 'CQueue':
        return self._dlq

    @classmethod
    def get_or_create(cls,
                      visibility_timeout: int,
                      retention: datetime.timedelta,
                      namespace: str = '',
                      dlq_url: str = 'auto'):
        """
        TODO: Implement this one!!
        Args:
            visibility_timeout:
            retention:
            namespace:
            dlq_url:

        Returns:

        """

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u'Queue={name} Priority={priority} Url={url};'.format(
            name=self.name, priority=self.priority, url=self._queue_url)


class PolicyBase(object):

    def __init__(self, queues):
        self._queues = queues

    def next_queue_and_message(self) -> Tuple[CQueue, CMessage]:
        raise NotImplementedError()


class StrictPriorityPolicy(PolicyBase):

    def __init__(self, queues):
        super(StrictPriorityPolicy, self).__init__(queues)
        self._queues.sort(key=attrgetter('priority'), reverse=True)

    def next_queue_and_message(self):
        # Use longer long poll timeout if there is only one queue
        # otherwise user a shorter loop with multiple queues
        poll_wait = 20 if len(self._queues) == 1 else 2
        for q in self._queues:
            message = q.receive_one_message(poll_wait=poll_wait)
            if message:
                return q, message
        return None, None


class WeightedPolicy(PolicyBase):

    def __init__(self, queues):
        super(WeightedPolicy, self).__init__(queues)

    def next_queue_and_message(self):
        raise NotImplementedError('This is a placeholder.')


# Public API

async def single_loop(poller, handler_func, worker_type):
    chosen_queue, message = poller.next_queue_and_message()
    msg_received = 0
    msg_processed = 0

    if not message:
        return msg_received, msg_processed

    msg_received = 1

    logger.debug('Received message from %s (%s)',
                 chosen_queue.name,
                 chosen_queue.url)
    logger.debug('Message id=%s, content=%s',
                 message.id,
                 str(message.body))

    f = handler_func(chosen_queue, message, worker_type)

    msg_processed = 1

    # Removes the message from SQS queue
    if f:
        message.delete()

    return msg_received, msg_processed


async def message_loop(queues: List[CQueue],
                       handler_func: callable,
                       poll_policy_class=StrictPriorityPolicy,
                       shutdown: threading.Event = None,
                       worker_type: str = None):
    """
    Starts a message loop and call related handler functions.

    Examples:

        def foo(queue, message, worker_type):
            # ... Your code logic
            return True
        ...

        queues = [
            Queue(name='test_queue_high',
                url='http://localhost:9324/queue1,
                priority=90,
                handler_func=foo),
        ]


        shutdown = await shutdown_on([
            signal.SIGINT,
            signal.SIGTERM,
        ])

        await message_loop(
            queues=queues,
            shutdown=shutdown,
            handler_func=foo,
            worker_type='foo_worker'
        )


    Args:
        queues:
        handler_func: Callback function with signature (queue, message, worker_type)
        poll_policy_class (StrictPriorityPolicy | WeightedPolicy):
        shutdown (threading.Event): a threading.Event() to signal shutdown.
        worker_type: (str)
    Returns:

    """
    shutdown = shutdown or threading.Event()

    poll_policy_instance = poll_policy_class(queues)  # noqa

    msgs_received, msgs_processed = 0, 0

    for queue in queues:
        logger.info(u'Polling %s', str(queue))

    loop_counter = 0
    while True:
        if shutdown.wait(0):
            logger.info("Shutdown flag is set. Shutting down...")
            break

        loop_counter += 1
        msg_received, msg_processed = await single_loop(
            poll_policy_instance,
            handler_func,
            worker_type
        )

        msgs_received += msg_received
        msgs_processed += msg_processed

    return msgs_received, msgs_processed


async def shutdown_on(signals):
    """Returns a threading.Event() that will get set when any of the given
    signals are triggered.

    Args:
        signals (list): A list of signals to handle.

    Returns:
        threading.Event
    """
    shutdown = threading.Event()

    def cancel_execution(signum, frame):  # noqa
        signame = SIGNAL_NAMES.get(signum, signum)
        logger.info("Signal %s received, quitting "
                    "(this can take some time)...", signame)
        shutdown.set()

    for s in signals:
        signal.signal(s, cancel_execution)

    return shutdown
