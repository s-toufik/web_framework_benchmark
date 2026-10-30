from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Environment:
    machine: str
    cpu: str
    cores: int
    system: str
    load_generator: str
