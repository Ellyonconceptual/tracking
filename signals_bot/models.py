from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SignalSide(str, Enum):
    CALL = "CALL"
    PUT = "PUT"


@dataclass
class Candle:
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp_ms: int


@dataclass
class InstrumentSubscription:
    symbol: str
    timeframe: str
    initial_price: float


@dataclass
class Signal:
    symbol: str
    timeframe: str
    side: SignalSide
    confidence: float
    reason: str
    price: float
    timestamp_ms: int
    expiry_timestamp_ms: int
    strategy_name: Optional[str] = None

