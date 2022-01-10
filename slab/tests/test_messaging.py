import asyncio
import unittest
from typing import Union
from unittest import mock

import boto3
import moto

from slab import messaging
from slab.messaging import (
    DRoutine,
    OK,
    droutine_worker_start,
    map_droutines_to_queue,
    DRoutineBaseParams
)


class FooDRoutineParams(DRoutineBaseParams):
    bar: int = 10


class FooDRoutine(DRoutine):
    TIMEOUT = 2
    params_class = FooDRoutineParams

    def run(self, params: FooDRoutineParams) -> Union[int, float]:
        return OK

    def on_timeout(self, timeout) -> Union[int, float]:
        return OK


class BarDRoutine(DRoutine):
    TIMEOUT = 2
    params_class = None

    def run(self, params=None) -> Union[int, float]:
        return OK

    def on_timeout(self, timeout) -> Union[int, float]:
        return OK


class MessagesTestCase(unittest.TestCase):

    def asyncSetUp(self) -> None:
        self.mock_sqs = moto.mock_sqs()
        self.mock_sqs.start()
        sqs = boto3.resource('sqs')
        sqs_client = sqs.meta.client
        # Creates a few queues
        resp = sqs_client.create_queue(
            QueueName="DefaultQueue",
            Attributes={
                'VisibilityTimeout': '5'
            }
        )
        self.default_queue = messaging.CQueue(
            url=resp.get('QueueUrl'),
            name='default'
        )

    def asyncTearDown(self) -> None:
        self.mock_sqs.stop()

    def test_send_message(self):
        pass


class DRoutineTestCase(unittest.TestCase):

    async def asyncSetUp(self) -> None:
        self.mock_sqs = moto.mock_sqs()
        self.mock_sqs.start()
        sqs = boto3.resource('sqs')
        sqs_client = sqs.meta.client
        # Creates a few queues
        resp = sqs_client.create_queue(
            QueueName="DefaultQueue",
            Attributes={
                'VisibilityTimeout': '5'
            }
        )
        self.default_queue = messaging.CQueue(
            url=resp.get('QueueUrl'),
            name='default'
        )
        # Initialize! Don't forget
        map_droutines_to_queue(
            self.default_queue,
            FooDRoutine,
            BarDRoutine
        )

    async def asyncTearDown(self) -> None:
        self.mock_sqs.stop()

    async def test_droutine_registry(self):
        self.assertIsNotNone(FooDRoutine.queue)

    @mock.patch('slab.messaging.droutine.notify_error')
    @mock.patch.object(FooDRoutine, 'on_timeout')
    @mock.patch.object(FooDRoutine, 'run')
    async def test_call_droutine_missing_args(self, mock_run, mock_on_timeout, mock_notify_error):
        mock_run.return_value = OK
        mock_on_timeout.return_value = OK
        with self.assertRaises(TypeError):
            FooDRoutine()()

    # @mock.patch('slab.messaging.droutine.notify_error')
    # @mock.patch.object(FooDRoutine, 'on_timeout')
    # @mock.patch.object(FooDRoutine, 'run')
    # async def test_run_droutine_wrong_params_types(self, mock_run, mock_on_timeout, mock_notify_error):
    #     mock_run.return_value = OK
    #     mock_on_timeout.return_value = OK
    #     with self.assertRaises(TypeError):
    #         FooDRoutine()()
    #     droutine_worker_start(
    #         queues=[self.default_queue],
    #         max_messages_to_receive=1,
    #         worker_type='default'
    #     )
    #     mock_notify_error.assert_called_once_with()
    #     mock_run.assert_not_called()
    #     mock_on_timeout.assert_not_called()
    #     # No messages should be in the queue anymore
    #     self.assertEqual(self.default_queue.messages_in_queue, 0)

    @mock.patch.object(FooDRoutine, 'on_timeout')
    @mock.patch.object(FooDRoutine, 'run')
    async def test_call_droutine_with_args(self, mock_run, mock_on_timeout):
        mock_run.return_value = OK
        mock_on_timeout.return_value = OK

        args = FooDRoutineParams(bar=20)

        FooDRoutine()(params=args)
        droutine_worker_start(
            queues=[self.default_queue],
            max_messages_to_receive=1,
            worker_type='default'
        )
        mock_run.assert_called_once_with(args)
        mock_on_timeout.assert_not_called()
        # No messages should be in the queue anymore
        self.assertEqual(self.default_queue.messages_in_queue, 0)

    @mock.patch.object(FooDRoutine, 'on_timeout')
    @mock.patch.object(FooDRoutine, 'run')
    async def test_call_droutine(self, mock_run, mock_on_timeout):
        mock_run.return_value = OK
        mock_on_timeout.return_value = OK

        params = FooDRoutineParams()

        FooDRoutine()(params=params)
        droutine_worker_start(
            queues=[self.default_queue],
            max_messages_to_receive=1,
            worker_type='default'
        )
        mock_run.assert_called_once_with(params)
        mock_on_timeout.assert_not_called()
        # No messages should be in the queue anymore
        self.assertEqual(self.default_queue.messages_in_queue, 0)

    @mock.patch('slab.messaging.droutine.notify_error')
    @mock.patch.object(FooDRoutine, 'on_timeout')
    @mock.patch.object(FooDRoutine, 'run')
    async def test_run_droutine_exception_notify_error_called(self,
                                                              mock_run,
                                                              mock_on_timeout,
                                                              mock_notify_error):
        class BadRun(Exception):
            pass

        async def raise_during_run(params):
            raise BadRun("O!")

        mock_run.side_effect = raise_during_run

        params = FooDRoutineParams()
        FooDRoutine()(params=params)
        droutine_worker_start(
            queues=[self.default_queue],
            max_messages_to_receive=1,
            worker_type='default'
        )

        mock_run.assert_called_once_with(params)
        mock_on_timeout.assert_not_called()
        mock_notify_error.assert_called_once()
        # Ensures that the message is popped back to the queue (it should)
        asyncio.sleep(FooDRoutine.TIMEOUT + FooDRoutine.VTT + 1)
        self.assertEqual(self.default_queue.messages_in_queue, 1)
        mock_on_timeout.assert_not_called()

    @mock.patch.object(FooDRoutine, 'on_timeout')
    @mock.patch.object(FooDRoutine, 'run')
    async def test_fire_task_timeout_delete_message(self, mock_run, mock_on_timeout):
        async def timeout_during_run(params):
            asyncio.sleep(FooDRoutine.TIMEOUT + 1)
            return OK

        mock_run.side_effect = timeout_during_run
        mock_on_timeout.return_value = OK

        params = FooDRoutineParams()

        FooDRoutine()(params=params)
        droutine_worker_start(
            queues=[self.default_queue],
            max_messages_to_receive=1,
            worker_type='default'
        )

        mock_run.assert_called_once_with(params)
        mock_on_timeout.assert_called_once_with(FooDRoutine.TIMEOUT)
        asyncio.sleep(0.1)
        # The message got deleted because `on_timeout` returns < 0
        self.assertEqual(self.default_queue.messages_in_queue, 0)

    @mock.patch.object(FooDRoutine, 'on_timeout')
    @mock.patch.object(FooDRoutine, 'run')
    async def test_fire_task_timeout_no_delete_message(self, mock_run, mock_on_timeout):
        async def timeout_during_run(params):
            asyncio.sleep(FooDRoutine.TIMEOUT + 1)
            return OK

        mock_run.side_effect = timeout_during_run
        mock_on_timeout.return_value = 0  # Returns the message to queue immediately

        params = FooDRoutineParams()

        FooDRoutine()(params=params)
        droutine_worker_start(
            queues=[self.default_queue],
            max_messages_to_receive=1,
            worker_type='default'
        )

        mock_run.assert_called_once_with(params)
        mock_on_timeout.assert_called_once_with(FooDRoutine.TIMEOUT)
        asyncio.sleep(0.1)
        self.assertEqual(self.default_queue.messages_in_queue, 1)

    @mock.patch.object(BarDRoutine, 'on_timeout')
    @mock.patch.object(BarDRoutine, 'run')
    async def test_call_droutine_no_params(self, mock_run, mock_on_timeout):
        mock_run.return_value = OK
        mock_on_timeout.return_value = OK

        BarDRoutine()()
        droutine_worker_start(
            queues=[self.default_queue],
            max_messages_to_receive=1,
            worker_type='default'
        )
        mock_run.assert_called_once_with(None)
        mock_on_timeout.assert_not_called()
        # No messages should be in the queue anymore
        self.assertEqual(self.default_queue.messages_in_queue, 0)

    @mock.patch.object(BarDRoutine, 'on_timeout')
    @mock.patch.object(BarDRoutine, 'run')
    @mock.patch.object(FooDRoutine, 'on_timeout')
    @mock.patch.object(FooDRoutine, 'run')
    async def test_call_multiple_droutines(self,
                                           mock_foo_run,
                                           mock_foo_on_timeout,
                                           mock_bar_run,
                                           mock_bar_on_timeout):
        mock_foo_run.return_value = OK
        mock_foo_on_timeout.return_value = OK
        mock_bar_run.return_value = OK
        mock_bar_on_timeout.return_value = OK

        params = FooDRoutineParams()
        asyncio.gather(
            FooDRoutine()(params=params),
            BarDRoutine()()
        )
        droutine_worker_start(
            queues=[self.default_queue],
            max_messages_to_receive=2,
            worker_type='default'
        )
        mock_foo_run.assert_called_once_with(params)
        mock_bar_run.assert_called_once_with(None)
        mock_foo_on_timeout.assert_not_called()
        mock_bar_on_timeout.assert_not_called()
        # No messages should be in the queue anymore
        self.assertEqual(self.default_queue.messages_in_queue, 0)
