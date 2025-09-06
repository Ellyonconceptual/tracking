import abc

from ..models import Signal


class AbstractSignalSink(abc.ABC):
    @abc.abstractmethod
    async def emit(self, signal: Signal) -> None:
        ...

