from collections import deque
from typing import Deque, List, Optional


class RollingSeries:
    def __init__(self, maxlen: int) -> None:
        self._values: Deque[float] = deque(maxlen=maxlen)

    def append(self, value: float) -> None:
        self._values.append(value)

    def values(self) -> List[float]:
        return list(self._values)

    def is_ready(self, length: int) -> bool:
        return len(self._values) >= length


def compute_ema(values: List[float], period: int) -> Optional[float]:
    if len(values) < period or period <= 0:
        return None
    k = 2 / (period + 1)
    ema_value = values[0]
    for v in values[1:]:
        ema_value = v * k + ema_value * (1 - k)
    return ema_value


def compute_rsi(values: List[float], period: int) -> Optional[float]:
    if len(values) <= period or period <= 0:
        return None
    gains: List[float] = []
    losses: List[float] = []
    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gains.append(max(0.0, change))
        losses.append(max(0.0, -change))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

