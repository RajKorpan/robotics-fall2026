from lab.evidence import evidence_id, student_seed
from lab.navigation import set_stage
from lab.session import complete_mission
from lab.submissions import save_mission
from lab.ui import render_check, text_response
from missions.mission_3 import evaluate
from simulation.scenarios import evaluate_rule


def _controls(st, context):
    slug = context.lower(); defaults = {"Warehouse": (0.75, 0.10), "Assistive": (0.95, 0.20)}; threshold, margin = defaults[context]
    st.markdown(f"#### {context} robot")
    if context == "Warehouse": st.caption("A low-speed cart operates in a controlled aisle. Stops delay work, but moving when too close can damage equipment.")
    else: st.caption("A mobile assistive robot operates near people with varied mobility. A false-safe decision can cause injury; repeated unnecessary stops can also reduce access and trust.")
    c1, c2, c3 = st.columns(3)
    settings = {
        "threshold": c1.slider("Unsafe distance (m)", 0.55, 1.25, threshold, 0.05, key=f"{slug}.threshold"),
        "margin": c2.slider("Caution margin (m)", 0.0, 0.45, margin, 0.05, key=f"{slug}.margin"),
        "weight_a": c3.slider("Weight on Sensor A", 0.0, 1.0, 0.35, 0.05, key=f"{slug}.weight"),
        "filter_method": c1.selectbox("Filter", ["Raw/hold last", "Moving average", "Median", "Exponential"], index=2, key=f"{slug}.filter"),
        "window": c2.slider("Window", 1, 11, 3, 2, key=f"{slug}.window"),
        "confirmations": c3.slider("Unsafe readings before STOP", 1, 4, 1, key=f"{slug}.confirm"),
        "missing_policy": st.selectbox("If both sensors are missing", ["Stop", "Insufficient evidence", "Move"], key=f"{slug}.missing"),
    }
    if st.button(f"Test {context} policy", key=f"test.{slug}"):
        results = dict(st.session_state["mission_3_results"]); results[context] = evaluate_rule(settings, context, student_seed(st.session_state["student"]["course_id"], f"mission_3_{slug}")); st.session_state["mission_3_results"] = results
    result = st.session_state["mission_3_results"].get(context)
    if result:
        st.dataframe([{**{key: round(value, 4) for key, value in result["metrics"].items()}, "overall": "Pass" if result["passed"] else "Revise"}], hide_index=True, width="stretch")
        st.dataframe(result["scenarios"], hide_index=True, width="stretch")
        st.caption(f"Required: false-safe ≤ {result['criteria']['false_safe_limit']:.0%}; unnecessary-stop ≤ {result['criteria']['unnecessary_stop_limit']:.0%}; max detection delay ≤ {result['criteria']['delay_limit']} s; zero collision events.")


def render(st):
    st.header("Mission 3 — Decide under uncertainty")
    st.write("Design two policies for the question **Is it safe to move forward?** Test every policy against the same seven scenarios. A false-safe means MOVE while the true distance is unsafe; an unnecessary stop means STOP when the path is clearly safe.")
    tabs = st.tabs(["Warehouse", "Assistive"])
    with tabs[0]: _controls(st, "Warehouse")
    with tabs[1]: _controls(st, "Assistive")
    text_response(st, "mission_3.error_costs", "Who bears the cost of false-safe and unnecessary-stop errors in each context? Explain why neither metric can simply be ignored.")
    text_response(st, "mission_3.context_comparison", "Compare your two final policies. Identify at least two parameter differences and justify them with the context and test metrics.")
    text_response(st, "mission_3.limitations", "What does this simulation fail to represent? Name one stakeholder you would consult and one additional test you would run before deployment.")
    if st.button("Check Mission 3", type="primary"):
        results = st.session_state["mission_3_results"]; check = evaluate(results, st.session_state["responses"]); st.session_state["m3.check"] = check
        if check.passed:
            eid = evidence_id("mission_3", results); complete_mission(st, "mission_3", eid); save_mission("mission_3", {"evidence_id": eid, "context_results": results}, st.session_state["responses"])
    if st.session_state.get("m3.check"): render_check(st, st.session_state["m3.check"])
    if "mission_3" in st.session_state["completed_missions"] and st.button("Continue to submission"): set_stage(st, "final")
