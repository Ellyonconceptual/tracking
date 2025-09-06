from typing import Any, Dict, List

from .data_provider.synthetic import SyntheticMarketDataProvider
from .data_provider.base import AbstractMarketDataProvider
from .strategies.base import AbstractStrategy
from .strategies.rsi_ema import RsiEmaStrategy
from .sinks.base import AbstractSignalSink
from .sinks.console import ConsoleSink


def build_provider(cfg: Dict[str, Any]) -> AbstractMarketDataProvider:
    name = (cfg.get("name") or "synthetic").lower()
    if name == "synthetic":
        return SyntheticMarketDataProvider(
            interval_ms=int(cfg.get("interval_ms", 1000)),
            seed=cfg.get("seed"),
        )
    raise ValueError(f"Unknown provider: {name}")


def build_strategies(items: List[Dict[str, Any]]) -> List[AbstractStrategy]:
    strategies: List[AbstractStrategy] = []
    for it in items:
        name = (it.get("name") or "").lower()
        params = it.get("parameters", {})
        if name == "rsi_ema":
            strategies.append(
                RsiEmaStrategy(
                    rsi_period=int(params.get("rsi_period", 14)),
                    ema_fast=int(params.get("ema_fast", 9)),
                    ema_slow=int(params.get("ema_slow", 21)),
                    rsi_overbought=float(params.get("rsi_overbought", 70)),
                    rsi_oversold=float(params.get("rsi_oversold", 30)),
                    min_history=int(params.get("min_history", 50)),
                    expiry_seconds=int(params.get("expiry_seconds", 300)),
                )
            )
        else:
            raise ValueError(f"Unknown strategy: {name}")
    return strategies


def build_sinks(items: List[Dict[str, Any]]) -> List[AbstractSignalSink]:
    sinks: List[AbstractSignalSink] = []
    for it in items:
        name = (it.get("name") or "").lower()
        params = it.get("parameters", {})
        if name == "console":
            sinks.append(ConsoleSink(pretty=bool(params.get("pretty", True))))
        else:
            raise ValueError(f"Unknown sink: {name}")
    return sinks

