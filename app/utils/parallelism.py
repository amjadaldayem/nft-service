import asyncio
from typing import Coroutine, Any, Union, Callable, List, Tuple

import multiprocess as mp


class ProcessManager:
    """
    Wraps a Process, so we could "restart" it easily with `start` method.
    """

    def __init__(self, target, args):
        self.target = target
        self.args = args
        self.process = None

    def start(self):
        """
        (Re)starts a new process with the given target and args

        Returns:

        """
        self.process = mp.Process(target=self.target, args=self.args)
        self.process.start()
        return self.process


async def _coro_wrapper(coro: Coroutine, i: int, input_data: Any):
    output = await coro(input_data)
    return i, output


async def retriable_map(coro: callable,
                        input_list: List[Any],
                        success_test: Callable = lambda a: a,
                        max_retries=1,
                        wait_strategy: Union[int, str] = 1,
                        loop=None) -> Tuple[List[Any], List[Any]]:
    """
    Map the `input_list` with `coro` and runs success_test on each of the results.

    If the `success_test` fails on an item in the results, push it back to a list
    for retry. Then do another round of retry on those specific failed items.

    Args:
        coro: The function object that returns a Coroutine
        input_list:
        success_test: A callable takes a single input and returns Tuple of (Any, bool)
        max_retries:
        wait_strategy: If int, then the number of seconds to wait before next round
            of retry otherwise if `backoff`, will sleep for 1 seconds for the first
            retry, then 2 seconds, and so on to 2 ** (max_retries)
        loop:

    Returns:
        Tuple of an output list and a list containing all failed input. Note that
        the output list (1st element in tuple) is *always* the same length as input
        list, failed entries will be set to None as placeholders.
    """
    if max_retries < 0:
        raise ValueError("Max retries has to be something greater than -1.")

    loop = loop or asyncio.get_running_loop()
    input_len = len(input_list)
    ret = [None] * input_len
    failed_retriable = {i for i in range(input_len)}
    max_tries = max_retries + 1
    tries = 0
    while tries < max_tries:
        task_list = [
            _coro_wrapper(coro, i, input_data)
            for i, input_data in enumerate(input_list)
            if i in failed_retriable
        ]
        results = await asyncio.gather(*task_list, loop=loop)

        for i, output_data in results:
            o, good = success_test(output_data)
            if good:
                ret[i] = o
                failed_retriable.remove(i)

        if failed_retriable:
            if isinstance(wait_strategy, (int, float)):
                await asyncio.sleep(wait_strategy)
            elif wait_strategy == 'backoff':
                await asyncio.sleep(2 ** tries)
            else:
                await asyncio.sleep(1)
        tries += 1
    return ret, [input_list[i] for i in sorted(failed_retriable)]
