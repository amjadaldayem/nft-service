from typing import Union, List

from pydantic import Field

from slab.messaging import DRoutine, OK, DRoutineBaseParams


class SMETransactionSignatures(DRoutineBaseParams):
    signatures: List[str] = Field(default_factory=list)


class SMEIndexerDRoutine(DRoutine):
    params_class = SMETransactionSignatures

    def run(self, params: SMETransactionSignatures) -> Union[int, float]:
        return OK

    def on_timeout(self, timeout) -> Union[int, float]:
        return OK
