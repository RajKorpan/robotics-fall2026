def text_response(st, key, prompt, minimum_words=35, height=120):
    value = st.text_area(prompt, value=st.session_state["responses"].get(key, ""), key=f"field.{key}", height=height)
    st.session_state["responses"][key] = value; st.caption(f"{len(value.split())} words; minimum {minimum_words}")


def render_requirements(st, requirements):
    for item in requirements:
        (st.success if item.passed else st.error)(f"{'✓' if item.passed else '✗'} {item.label} — observed: {item.actual}; expected: {item.expected}")


def reflections_ready(responses, keys, minimum=35): return all(len(str(responses.get(key, "")).split()) >= minimum for key in keys)

