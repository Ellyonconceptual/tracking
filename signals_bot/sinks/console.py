from datetime import datetime, timezone
from typing import Optional

from rich.console import Console
from rich.table import Table

from ..models import Signal, SignalSide
from .base import AbstractSignalSink


class ConsoleSink(AbstractSignalSink):
    def __init__(self, pretty: bool = True) -> None:
        self._pretty = pretty
        self._console = Console()

    async def emit(self, signal: Signal) -> None:
        if not self._pretty:
            self._console.print(signal)
            return
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Time")
        table.add_column("Symbol")
        table.add_column("Side")
        table.add_column("Price")
        table.add_column("Conf")
        table.add_column("Expiry")
        table.add_column("Reason")
        dt = datetime.fromtimestamp(signal.timestamp_ms / 1000, tz=timezone.utc)
        expiry = datetime.fromtimestamp(signal.expiry_timestamp_ms / 1000, tz=timezone.utc)
        side_str = "[green]CALL[/]" if signal.side == SignalSide.CALL else "[red]PUT[/]"
        table.add_row(
            dt.strftime("%H:%M:%S"),
            signal.symbol,
            side_str,
            f"{signal.price:.5f}",
            f"{signal.confidence:.2f}",
            expiry.strftime("%H:%M:%S"),
            signal.reason,
        )
        self._console.print(table)

