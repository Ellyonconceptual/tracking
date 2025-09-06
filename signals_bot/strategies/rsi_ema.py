from typing import Dict, Optional

from ..indicators import RollingSeries, compute_ema, compute_rsi
from ..models import Candle, Signal, SignalSide
from .base import AbstractStrategy


class RsiEmaStrategy(AbstractStrategy):
    name = "rsi_ema"

    def __init__(
        self,
        rsi_period: int = 14,
        ema_fast: int = 9,
        ema_slow: int = 21,
        rsi_overbought: float = 70.0,
        rsi_oversold: float = 30.0,
        min_history: int = 50,
        expiry_seconds: int = 300,
    ) -> None:
        self._rsi_period = rsi_period
        self._ema_fast = ema_fast
        self._ema_slow = ema_slow
        self._rsi_overbought = rsi_overbought
        self._rsi_oversold = rsi_oversold
        self._min_history = min_history
        self._expiry_seconds = expiry_seconds
        self._closes: Dict[str, RollingSeries] = {}

    def _series(self, key: str) -> RollingSeries:
        if key not in self._closes:
            maxlen = max(self._min_history, self._ema_slow + 5)
            self._closes[key] = RollingSeries(maxlen=maxlen)
        return self._closes[key]

    def on_candle(self, candle: Candle) -> Optional[Signal]:
        series = self._series(f"{candle.symbol}:{candle.timeframe}")
        series.append(candle.close)
        values = series.values()
        if len(values) < self._min_history:
            return None
        ema_fast = compute_ema(values, self._ema_fast)
        ema_slow = compute_ema(values, self._ema_slow)
        rsi = compute_rsi(values, self._rsi_period)
        if ema_fast is None or ema_slow is None or rsi is None:
            return None

        side: Optional[SignalSide] = None
        reason = ""
        if ema_fast > ema_slow and rsi < self._rsi_oversold:
            side = SignalSide.CALL
            reason = f"EMA{self._ema_fast}>{self._ema_slow} & RSI<{self._rsi_oversold:.0f}"
        elif ema_fast < ema_slow and rsi > self._rsi_overbought:
            side = SignalSide.PUT
            reason = f"EMA{self._ema_fast}<{self._ema_slow} & RSI>{self._rsi_overbought:.0f}"
        if side is None:
            return None

        confidence = min(1.0, abs(ema_fast - ema_slow) / max(1e-9, candle.close) * 100 + abs(50 - rsi) / 100)
        expiry_ms = candle.timestamp_ms + self._expiry_seconds * 1000
        return Signal(
            symbol=candle.symbol,
            timeframe=candle.timeframe,
            side=side,
            confidence=confidence,
            reason=reason,
            price=candle.close,
            timestamp_ms=candle.timestamp_ms,
            expiry_timestamp_ms=expiry_ms,
            strategy_name=self.name,
        )

