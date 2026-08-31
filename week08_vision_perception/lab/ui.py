from lab.session import response, set_response
def text_response(st, key, label, height=110):
    value = st.text_area(label, value=str(response(st, key, "")), height=height, key=f"widget.{key}"); set_response(st, key, value); return value
def render_check(st, check):
    st.dataframe([{"Requirement": item.label, "Actual": item.actual, "Expected": item.expected, "Status": "Pass" if item.passed else "Not yet"} for item in check.requirements], hide_index=True, width="stretch")
    (st.success if check.passed else st.warning)(check.summary if check.passed else "The mission is not complete yet.")
