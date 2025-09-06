import asyncio
from dataclasses import dataclass
from typing import Dict, List

from .models import Candle, InstrumentSubscription, Signal
from .data_provider.base import AbstractMarketDataProvider
from .strategies.base import AbstractStrategy
from .sinks.base import AbstractSignalSink


@dataclass
class _SubscriptionState:
    instrument: InstrumentSubscription
    queue: asyncio.Queue


class SignalEngine:
    def __init__(
        self,
        provider: AbstractMarketDataProvider,
        strategies: List[AbstractStrategy],
        sinks: List[AbstractSignalSink],
    ) -> None:
        self._provider = provider
        self._strategies = strategies
        self._sinks = sinks
        self._subs: Dict[str, _SubscriptionState] = {}
        self._tasks: List[asyncio.Task] = []

    async def add_subscription(self, symbol: str, timeframe: str, initial_price: float) -> None:
        sub = InstrumentSubscription(symbol=symbol, timeframe=timeframe, initial_price=initial_price)
        q: asyncio.Queue[Candle] = asyncio.Queue()
        self._subs[symbol] = _SubscriptionState(instrument=sub, queue=q)
        await self._provider.subscribe(sub, q)

    async def start(self) -> None:
        self._tasks.append(asyncio.create_task(self._provider.run()))
        for symbol, state in self._subs.items():
            self._tasks.append(asyncio.create_task(self._consume(symbol, state)))

    async def stop(self) -> None:
        await self._provider.stop()
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def _consume(self, symbol: str, state: _SubscriptionState) -> None:
        while True:
            candle = await state.queue.get()
            signals: List[Signal] = []
            for strategy in self._strategies:
                maybe_signal = strategy.on_candle(candle)
                if maybe_signal is not None:
                    signals.append(maybe_signal)
            for sink in self._sinks:
                for sig in signals:
                    await sink.emit(sig)

