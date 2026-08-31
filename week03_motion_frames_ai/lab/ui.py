from __future__ import annotations

from lab.models import MissionCheck
from lab.session import response, set_response


def text_response(st, key: str, label: str, *, height: int = 100, disabled: bool = False) -> str:
    value = st.text_area(label, value=str(response(st, key, "")), height=height, disabled=disabled, key=f"widget.{key}")
    if not disabled:
        set_response(st, key, value)
    return value


def render_check(st, check: MissionCheck) -> None:
    st.dataframe(
        [{"Requirement": item.label, "Actual": item.actual, "Expected": item.expected, "Status": "Pass" if item.passed else "Not yet"} for item in check.requirements],
        hide_index=True,
        width="stretch",
    )
    (st.success if check.passed else st.warning)(check.summary if check.passed else "The mission is not complete yet.")

