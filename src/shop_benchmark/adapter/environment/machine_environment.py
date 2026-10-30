import os
import platform
import subprocess
from pathlib import Path

from shop_benchmark.domain.environment import Environment


class MachineEnvironment:
    def __init__(self, oha: str) -> None:
        self._oha = oha

    def describe(self) -> Environment:
        return Environment(
            machine=platform.node(),
            cpu=_cpu(),
            cores=os.cpu_count() or 0,
            system=f"{platform.system()} {platform.release()} ({platform.machine()})",
            load_generator=_output([self._oha, "--version"]) or self._oha,
        )


def _cpu() -> str:
    if platform.system() == "Darwin":
        return _output(["sysctl", "-n", "machdep.cpu.brand_string"]) or platform.processor()
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    return platform.processor() or platform.machine()


def _output(command: list[str]) -> str:
    try:
        return subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip()
    except OSError, subprocess.CalledProcessError:
        return ""
