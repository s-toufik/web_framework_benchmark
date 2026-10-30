import asyncio
import json
import tempfile
from pathlib import Path

from shop_benchmark.adapter.oha.oha_output import measurement_of
from shop_benchmark.domain.endpoint import Endpoint
from shop_benchmark.domain.load_profile import LoadProfile
from shop_benchmark.domain.measurement import Measurement


class LoadGeneratorFailed(Exception):
    pass


class OhaLoadGenerator:
    def __init__(self, base_url: str, executable: str = "oha") -> None:
        self._base_url = base_url.rstrip("/")
        self._executable = executable

    async def run(
        self, endpoint: Endpoint, profile: LoadProfile, duration_seconds: float
    ) -> Measurement:
        with tempfile.TemporaryDirectory() as folder:
            command = self.command(endpoint, profile, duration_seconds, Path(folder))
            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise LoadGeneratorFailed(
                f"{' '.join(command)} exited with {process.returncode}: {stderr.decode().strip()}"
            )
        return measurement_of(json.loads(stdout))

    def command(
        self, endpoint: Endpoint, profile: LoadProfile, duration_seconds: float, folder: Path
    ) -> list[str]:
        command = [
            self._executable,
            "--no-tui",
            "--output-format",
            "json",
            "--wait-ongoing-requests-after-deadline",
            "-z",
            f"{round(duration_seconds * 1_000)}ms",
            "-c",
            str(profile.connections),
            "-m",
            endpoint.method,
        ]
        if profile.rate_per_second is not None:
            command += ["-q", str(profile.rate_per_second), "--latency-correction"]
        if endpoint.body is not None:
            body = folder / "body"
            body.write_bytes(endpoint.body)
            command += ["-D", str(body), "-T", endpoint.content_type or "application/octet-stream"]
        return [*command, f"{self._base_url}{endpoint.path}"]
