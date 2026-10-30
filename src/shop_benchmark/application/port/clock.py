from typing import Protocol


class Clock(Protocol):
    def now(self) -> str: ...

    async def sleep(self, seconds: float) -> None: ...
