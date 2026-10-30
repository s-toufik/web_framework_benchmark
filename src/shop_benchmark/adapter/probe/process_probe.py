import asyncio
import contextlib
from collections.abc import Awaitable

import psutil

from shop_benchmark.domain.server_usage import ServerUsage

MEGABYTE: float = 1024 * 1024


class ProcessProbe:
    def __init__(self, port: int, interval_seconds: float) -> None:
        self._port = port
        self._interval = interval_seconds

    async def during[T](self, work: Awaitable[T]) -> tuple[T, ServerUsage | None]:
        processes = self.server_processes()
        if not processes:
            return await work, None
        samples: list[tuple[float, float]] = []
        sampler = asyncio.create_task(self._sample(processes, samples))
        try:
            result = await work
        finally:
            sampler.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await sampler
        return result, ServerUsage.of(samples)

    def server_processes(self) -> list[psutil.Process]:
        listening = [process for process in psutil.process_iter() if self._listens(process)]
        pids = {process.pid for process in listening}
        roots = [process for process in listening if process.ppid() not in pids]
        if not roots:
            return []
        root = roots[0]
        return [root, *root.children(recursive=True)]

    async def _sample(
        self, processes: list[psutil.Process], samples: list[tuple[float, float]]
    ) -> None:
        for process in processes:
            with contextlib.suppress(psutil.Error):
                process.cpu_percent(None)
        while True:
            await asyncio.sleep(self._interval)
            cpu, memory = 0.0, 0.0
            for process in processes:
                with contextlib.suppress(psutil.Error):
                    cpu += process.cpu_percent(None)
                    memory += process.memory_info().rss
            samples.append((cpu, memory / MEGABYTE))

    def _listens(self, process: psutil.Process) -> bool:
        try:
            return any(
                connection.status == psutil.CONN_LISTEN
                and connection.laddr
                and connection.laddr.port == self._port
                for connection in process.net_connections(kind="tcp")
            )
        except psutil.Error:
            return False


class NoProbe:
    async def during[T](self, work: Awaitable[T]) -> tuple[T, ServerUsage | None]:
        return await work, None
