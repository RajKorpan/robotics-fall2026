from __future__ import annotations

from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
_COMPONENTS: dict[str, Any] = {}


def tutorial_component(st, name: str, initial_state: dict[str, Any], *, key: str) -> dict[str, Any]:
    component = _COMPONENTS.get(name)
    if component is None:
        component = st.components.v1.declare_component(
            f"week01_{name}",
            path=str(ROOT / "components" / name),
        )
        _COMPONENTS[name] = component
    value = component(initial_state=initial_state, key=key, default=initial_state)
    return dict(value) if isinstance(value, dict) else dict(initial_state)
