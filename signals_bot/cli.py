import argparse
import asyncio
import signal
from pathlib import Path
from typing import Any, Dict

import yaml

from .engine import SignalEngine
from .factories import build_provider, build_strategies, build_sinks


def load_config(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


async def _run(config_path: Path) -> None:
    config = load_config(config_path)
    provider = build_provider(config.get("provider", {}))
    strategies = build_strategies(config.get("strategies", []))
    sinks = build_sinks(config.get("sinks", []))

    engine = SignalEngine(provider=provider, strategies=strategies, sinks=sinks)
    for instrument in config.get("instruments", []):
        symbol = instrument["symbol"]
        timeframe = instrument.get("timeframe", "1m")
        initial_price = float(instrument.get("initial_price", 100.0))
        await engine.add_subscription(symbol=symbol, timeframe=timeframe, initial_price=initial_price)

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _handle_sigterm() -> None:
        stop_event.set()

    for s in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(s, _handle_sigterm)

    await engine.start()
    await stop_event.wait()
    await engine.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run real-time options signal bot")
    parser.add_argument("--config", type=str, required=True, help="Path to YAML config file")
    args = parser.parse_args()
    asyncio.run(_run(Path(args.config)))


if __name__ == "__main__":
    main()

