import abc
from typing import Optional

from ..models import Candle, Signal


class AbstractStrategy(abc.ABC):
    name: str = "abstract"

    @abc.abstractmethod
    def on_candle(self, candle: Candle) -> Optional[Signal]:
        ...

