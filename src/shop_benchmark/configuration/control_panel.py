import json
from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, Field

from shop_benchmark.domain.load_profile import LoadProfile
from shop_benchmark.workload.catalog import Workload


class TargetSettings(BaseModel):
    base_url: str
    timeout_seconds: Annotated[float, Field(gt=0)] = 30


class ProfileSettings(BaseModel):
    name: str
    connections: Annotated[int, Field(ge=1)]
    duration_seconds: Annotated[float, Field(gt=0)]
    rate_per_second: Annotated[int | None, Field(ge=1)] = None

    def to_domain(self) -> LoadProfile:
        return LoadProfile(self.name, self.connections, self.duration_seconds, self.rate_per_second)


class LoadSettings(BaseModel):
    oha: str = "oha"
    warmup_seconds: Annotated[float, Field(ge=0)] = 5
    pause_seconds: Annotated[float, Field(ge=0)] = 2
    profiles: Annotated[list[ProfileSettings], Field(min_length=1)]


class WorkloadSettings(BaseModel):
    sku: str = "SKU-00042"
    order_lines: Annotated[int, Field(ge=1, le=20)] = 5
    upload_bytes: Annotated[int, Field(ge=1)] = 65_536
    note_lines: Annotated[int, Field(ge=1)] = 25

    def to_domain(self) -> Workload:
        return Workload(self.sku, self.order_lines, self.upload_bytes, self.note_lines)


class ProbeSettings(BaseModel):
    enabled: bool = True
    interval_seconds: Annotated[float, Field(gt=0)] = 0.25


class ControlPanel(BaseModel):
    target: TargetSettings
    load: LoadSettings
    workload: WorkloadSettings = WorkloadSettings()
    probe: ProbeSettings = ProbeSettings()
    endpoints: list[str] = []
    output_dir: str = "reports/benchmark"

    @classmethod
    def load_file(cls, path: Path) -> ControlPanel:
        return cls.model_validate(json.loads(path.read_text()))


class Overrides(BaseModel):
    base_url: str | None = None
    duration_seconds: float | None = None
    warmup_seconds: float | None = None
    connections: int | None = None
    endpoints: list[str] | None = None
    profiles: list[str] | None = None
    output_dir: str | None = None

    def apply(self, panel: ControlPanel) -> ControlPanel:
        data: dict[str, Any] = panel.model_dump()
        if self.base_url:
            data["target"]["base_url"] = self.base_url
        if self.warmup_seconds is not None:
            data["load"]["warmup_seconds"] = self.warmup_seconds
        if self.profiles:
            data["load"]["profiles"] = [
                p for p in data["load"]["profiles"] if p["name"] in self.profiles
            ]
        for profile in data["load"]["profiles"]:
            if self.duration_seconds is not None:
                profile["duration_seconds"] = self.duration_seconds
            if self.connections is not None:
                profile["connections"] = self.connections
        if self.endpoints:
            data["endpoints"] = self.endpoints
        if self.output_dir:
            data["output_dir"] = self.output_dir
        return ControlPanel.model_validate(data)
