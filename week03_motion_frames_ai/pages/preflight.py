from __future__ import annotations

from lab.evidence import preflight
from lab.navigation import set_stage


def render(st) -> None:
    st.title("Environment preflight")
    st.code("./scripts/course_preflight.sh", language="bash")
    result = preflight()
    checks = result.get("checks", [])
    if checks:
        st.dataframe(checks, hide_index=True, width="stretch")
        ready = all(item.get("passed") for item in checks)
        (st.success if ready else st.error)("Environment ready." if ready else "Resolve failed checks before continuing.")
    else:
        ready = False
        st.info("Run the preflight, then refresh.")
    if st.button("Refresh"):
        st.rerun()
    if st.button("Continue to Mission 1", type="primary", disabled=not ready):
        set_stage(st, "mission_1")

