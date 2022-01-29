import functools
from itertools import filterfalse, tee
from typing import Tuple, Iterable


def compose(*functions):
    return functools.reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)


def partition(pred, iterable) -> Tuple[Iterable, Iterable]:
    """
    Partition the iterable into two parts, with the `pred` = true the first part;
    false the second part
    Args:
        pred:
        iterable:

    Returns:
        iterable
    """
    t1, t2 = tee(iterable)
    return filter(pred, t2), filterfalse(pred, t1)
