import abc
import asyncio
from typing import Protocol

from ..models import Candle, InstrumentSubscription


class AbstractMarketDataProvider(abc.ABC):
    @abc.abstractmethod
    async def subscribe(self, subscription: InstrumentSubscription, queue: "asyncio.Queue[Candle]") -> None:
        ...

    @abc.abstractmethod
    async def run(self) -> None:
        ...

    @abc.abstractmethod
    async def stop(self) -> None:
        ...

