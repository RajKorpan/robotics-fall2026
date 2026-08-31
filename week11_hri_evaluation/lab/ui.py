def response(st, key, prompt, minimum=40, height=130):
    value = st.text_area(prompt, value=st.session_state["responses"].get(key, ""), key="field."+key, height=height); st.session_state["responses"][key] = value; st.caption(f"{len(value.split())} words; minimum {minimum}")
def responses_ready(st, keys, minimum=40): return all(len(st.session_state["responses"].get(k, "").split()) >= minimum for k in keys)
def render_checks(st, checks):
    for r in checks: (st.success if r.passed else st.error)(f"{'✓' if r.passed else '✗'} {r.label} — observed: {r.actual}; expected: {r.expected}")

