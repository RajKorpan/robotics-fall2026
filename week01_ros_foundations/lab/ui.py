from __future__ import annotations

from lab.models import MissionCheck
from lab.session import response, set_response


def text_response(st, key: str, label: str, *, help: str = "", height: int = 100) -> str:
    value = st.text_area(
        label,
        value=str(response(st, key, "")),
        help=help or None,
        height=height,
        key=f"widget.{key}",
    )
    set_response(st, key, value)
    return value


def choice_response(st, key: str, label: str, options: list[str]) -> str:
    prior = str(response(st, key, ""))
    values = ["Select an answer", *options]
    index = values.index(prior) if prior in values else 0
    value = st.selectbox(label, values, index=index, key=f"widget.{key}")
    stored = "" if value == values[0] else value
    set_response(st, key, stored)
    return stored


def render_check(st, check: MissionCheck) -> None:
    rows = [
        {
            "Requirement": item.label,
            "Actual": str(item.actual),
            "Expected": str(item.expected),
            "Status": "Pass" if item.passed else "Not yet",
        }
        for item in check.requirements
    ]
    st.dataframe(rows, hide_index=True, width="stretch")
    if check.passed:
        st.success(check.summary)
    else:
        st.warning("The mission is not complete yet. Review the requirements above.")
