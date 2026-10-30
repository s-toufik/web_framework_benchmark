from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Service:
    name: str
    version: str
    framework: str
    framework_version: str
    python: str
    server: str

    @property
    def title(self) -> str:
        return f"{self.framework} {self.framework_version}"
