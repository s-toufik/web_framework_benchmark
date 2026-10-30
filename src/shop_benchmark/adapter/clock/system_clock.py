import asyncio
from datetime import datetime


class SystemClock:
    def now(self) -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)
