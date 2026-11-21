"""What the Jetson health panel reports: one reading per metric, each with its status."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CoreReading",
    "CpuReading",
    "DiskReading",
    "GpuReading",
    "HealthStatus",
    "MemoryReading",
    "ModelReading",
    "PowerReading",
    "SystemHealthSnapshot",
    "TemperatureReading",
]

HealthStatus = Literal["ok", "warn", "critical", "unknown"]


class CoreReading(BaseModel):
    """One CPU core: its busy share since the previous sample and its clock."""

    model_config = ConfigDict(frozen=True)

    index: int = Field(description="Core number, counted from 0.")
    usage_percent: float | None = Field(
        description="None when the sample is unreadable."
    )
    freq_mhz: int | None = Field(
        description="Current clock; None when cpufreq does not say."
    )


class CpuReading(BaseModel):
    """All cores together, then each core."""

    model_config = ConfigDict(frozen=True)

    usage_percent: float | None
    per_core: list[CoreReading]
    status: HealthStatus


class MemoryReading(BaseModel):
    """RAM shared by the CPU and the GPU. Available memory is what the models can still use."""

    model_config = ConfigDict(frozen=True)

    total_mb: float
    available_mb: float
    used_percent: float
    swap_total_mb: float
    swap_used_mb: float
    status: HealthStatus


class GpuReading(BaseModel):
    """The integrated GPU: how busy it is and its clock now and at most."""

    model_config = ConfigDict(frozen=True)

    load_percent: float | None
    freq_mhz: int | None
    max_freq_mhz: int | None
    status: HealthStatus


class TemperatureReading(BaseModel):
    """One thermal zone of the SoC, in degrees Celsius."""

    model_config = ConfigDict(frozen=True)

    zone: str
    celsius: float
    status: HealthStatus


class PowerReading(BaseModel):
    """Power drawn through one monitored power rail (the board input and its parts)."""

    model_config = ConfigDict(frozen=True)

    rail: str
    milliwatts: int


class DiskReading(BaseModel):
    """The partition that holds the database."""

    model_config = ConfigDict(frozen=True)

    total_gb: float
    free_gb: float
    free_percent: float
    status: HealthStatus


class ModelReading(BaseModel):
    """A language model Ollama holds in memory, with the share of it on the GPU."""

    model_config = ConfigDict(frozen=True)

    name: str
    gpu_percent: int | None = Field(description="None when Ollama does not say.")


class SystemHealthSnapshot(BaseModel):
    """One sample of the appliance. Every metric is None (or empty) when it cannot be read."""

    model_config = ConfigDict(frozen=True)

    sampled_at: str = Field(description="UTC time of the sample, ISO 8601.")
    cpu: CpuReading
    memory: MemoryReading | None
    gpu: GpuReading | None
    temperatures: list[TemperatureReading]
    power: list[PowerReading]
    disk: DiskReading | None
    uptime_seconds: float | None
    load_average: list[float] | None = Field(description="1, 5 and 15 minutes.")
    models: list[ModelReading]
    voices: list[str] = Field(
        description="Canonical names of the voice engines loaded now."
    )
