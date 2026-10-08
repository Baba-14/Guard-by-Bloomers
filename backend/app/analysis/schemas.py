"""Internal types shared by Guard's independent analyzers and risk engine."""

from dataclasses import dataclass, field
from typing import Literal


SignalSource = Literal["rule", "url", "jev", "database"]


@dataclass(frozen=True, slots=True)
class EvidenceSignal:
    key: str
    label: str
    weight: int
    confidence: float
    source: SignalSource
    evidence: str

    @property
    def contribution(self) -> int:
        return round(self.weight * max(0.0, min(1.0, self.confidence)))


@dataclass(slots=True)
class ProviderMetadata:
    provider: str
    model: str | None = None
    status: Literal["used", "disabled", "unavailable", "failed"] = "disabled"
    answers: dict = field(default_factory=dict)
    usage: dict = field(default_factory=dict)
    latency_ms: int | None = None
    error: str | None = None


@dataclass(slots=True)
class AnalysisOutcome:
    level: Literal["Low Risk", "Caution", "High Risk", "Unable to Determine"]
    score: int
    confidence: float
    signals: list[EvidenceSignal]
    explanation: str
    recommended_action: str
    pattern: str
    provider: ProviderMetadata
    check_id: str | None = None
