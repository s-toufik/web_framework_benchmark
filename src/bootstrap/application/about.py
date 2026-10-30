import platform
import sys
from dataclasses import dataclass
from importlib.metadata import version
from typing import Final

from src import APPLICATION_NAME, APPLICATION_VERSION

SERVERS: Final[tuple[str, ...]] = ("granian", "uvicorn", "hypercorn")


@dataclass(frozen=True, slots=True)
class About:
    service: str
    version: str
    framework: str
    framework_version: str
    python: str
    server: str

    @classmethod
    def of(cls, framework: str) -> About:
        return cls(
            service=APPLICATION_NAME,
            version=APPLICATION_VERSION,
            framework=framework,
            framework_version=version(framework),
            python=platform.python_version(),
            server=next((server for server in SERVERS if server in sys.modules), "unknown"),
        )
