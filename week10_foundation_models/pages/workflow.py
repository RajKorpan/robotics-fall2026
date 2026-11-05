"""Shared compact figures, persisted fields and explicit navigation."""
import html

from lab.evidence import root, saved_run, save_progress
from lab.drafts import current, capture_inputs


def field(st, key, label, height=130):
    import streamlit as host
    if not host.session_state.get("field_hint_shown"):
        st.caption("Press Ctrl+Enter or click outside a text field to apply and autosave your edit. Check and save retains the complete experiment.")
        host.session_state["field_hint_shown"] = True
    keys = list(host.session_state.get("response_widgets", []))
    if key not in keys:
        host.session_state["response_widgets"] = keys + [key]
    if key not in host.session_state:
        host.session_state[key] = host.session_state["responses"].get(key, "")
    def changed():
        capture_inputs(host.session_state)
        try:
            save_progress(host.session_state)
        except OSError as error:
            host.session_state["save_error"] = str(error)
    value = st.text_area(label, key=key, height=height, on_change=changed)
    host.session_state["responses"][key] = value
    return value


def meaningful(*answers):
    return all(len(a.strip().split()) >= 15 for a in answers)


def trajectory_svg(rows, scale=1):
    points = " ".join(f'{245 + float(r["x_m"]) / scale * 110:.1f},{145 - float(r["y_m"]) / scale * 110:.1f}' for r in rows)
    target = ""
    if rows and "target_x_m" in rows[0]:
        x = 245 + rows[0]["target_x_m"] * 110 / scale
        y = 145 - rows[0]["target_y_m"] * 110 / scale
        target = f'<circle cx="{x}" cy="{y}" r="8" fill="none" stroke="#dc2626" stroke-width="3"/><text x="{x+12}" y="{y}" font-family="sans-serif" font-size="13">target</text>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="520" height="290" viewBox="0 0 520 290"><defs><marker id="tip" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6" fill="#2563eb"/></marker></defs><rect width="520" height="290" fill="#f1f5f9"/><path d="M245 25 V260 M110 145 H455" fill="none" stroke="#64748b"/><polyline points="{points}" fill="none" stroke="#2563eb" stroke-width="3" marker-end="url(#tip)"/>{target}<text x="425" y="175" font-family="sans-serif">x (m)</text><text x="255" y="30" font-family="sans-serif">y (m)</text><text x="250" y="162" font-size="12">0</text><text x="350" y="162" font-size="12">{scale}</text><text x="255" y="40" font-size="12">{scale}</text><text x="255" y="255" font-size="12">-{scale}</text></svg>')




def locked(st, previous):
    if not current(previous, st.session_state):
        st.info("Review changes and save " + previous.replace("_", " ").title() + " before beginning this investigation. Your earlier evidence is retained.")
        from lab.navigation import bottom_nav
        bottom_nav(st, previous, None)
        return True
    return False


def saved_status(st, mission):
    if current(mission, st.session_state):
        st.success("Saved evidence matches these answers, settings and earlier mission results.")
    elif saved_run(mission):
        st.warning("You have changes that are not in the saved experiment. Review them and select Check and save again before continuing. Earlier evidence is retained.")
