from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from lab.models import RunResult
from simulation.core import simulate_feedback
from simulation.metrics import feedback_metrics


def run_feedback_mission(mission_id: str, settings: dict) -> RunResult:
    trace = simulate_feedback(**settings)
    return RunResult(
        run_id=str(uuid4()),
        mission_id=mission_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        settings=settings,
        metrics=feedback_metrics(trace),
        traces=trace,
    )

