from typing import Union

from slab.messaging import DRoutineBaseParams, DRoutine, OK


class FooDRoutineParams(DRoutineBaseParams):
    bar: int = 100


class FooDRoutine(DRoutine):
    TIMEOUT = 2
    params_class = FooDRoutineParams

    def run(self, params: FooDRoutineParams) -> Union[int, float]:
        return OK

    def on_timeout(self, timeout) -> Union[int, float]:
        return OK
