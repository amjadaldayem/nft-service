import logging
from typing import Union

from slab.messaging import DRoutine, OK, DRoutineBaseParams

logger = logging.getLogger(__name__)


class NftCollectionInputParam(DRoutineBaseParams):
    update_authority: str = ''


class NftCollectionDRoutine(DRoutine):
    TIMEOUT = 180
    params_class = NftCollectionInputParam

    def run(self, params: NftCollectionInputParam) -> Union[int, float]:
        return OK

    def on_timeout(self, timeout) -> Union[int, float]:
        return OK
