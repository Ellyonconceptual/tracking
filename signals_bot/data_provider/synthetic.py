import asyncio
import math
import random
import time
from dataclasses import dataclass
from typing import Dict, Tuple

from ..models import Candle, InstrumentSubscription
from .base import AbstractMarketDataProvider


@dataclass
class _SeriesState:
    price: float
    t0: float


class SyntheticMarketDataProvider(AbstractMarketDataProvider):
    def __init__(self, interval_ms: int = 1000, seed: int | None = None) -> None:
        self._interval_ms = interval_ms
        if seed is not None:
            random.seed(seed)
        self._subs: Dict[str, Tuple[InstrumentSubscription, asyncio.Queue]] = {}
        self._states: Dict[str, _SeriesState] = {}
        self._running = False

    async def subscribe(self, subscription: InstrumentSubscription, queue: "asyncio.Queue[Candle]") -> None:
        self._subs[subscription.symbol] = (subscription, queue)
        self._states[subscription.symbol] = _SeriesState(price=subscription.initial_price, t0=time.time())

    async def run(self) -> None:
        self._running = True
        while self._running:
            now_ms = int(time.time() * 1000)
            for symbol, (sub, q) in self._subs.items():
                state = self._states[symbol]
                # Drift + mean-reverting noise + periodic component
                dt = max(1, self._interval_ms) / 1000.0
                periodic = 0.001 * math.sin((time.time() - state.t0) * 2 * math.pi / 60)
                noise = random.gauss(0, 0.0005)
                drift = 0.0001
                ret = drift + periodic + noise
                new_price = max(0.0001, state.price * (1 + ret))
                high = max(state.price, new_price)
                low = min(state.price, new_price)
                volume = abs(ret) * 1000
                candle = Candle(
                    symbol=symbol,
                    timeframe=sub.timeframe,
                    open=state.price,
                    high=high,
                    low=low,
                    close=new_price,
                    volume=volume,
                    timestamp_ms=now_ms,
                )
                state.price = new_price
                await q.put(candle)
            await asyncio.sleep(self._interval_ms / 1000.0)

    async def stop(self) -> None:
        self._running = False

