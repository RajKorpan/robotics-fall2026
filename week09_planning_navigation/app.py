from __future__ import annotations
import argparse
from lab.autosave import load_state, save
from lab.navigation import LABELS, current_stage, render_progress, set_stage
from lab.session import initialize
from lab_config import LAB
from pages import concepts, final, intro, mission_1, mission_2, mission_3, preflight

PAGES = {"intro": intro.render, "concepts": concepts.render, "preflight": preflight.render, "mission_1": mission_1.render, "mission_2": mission_2.render, "mission_3": mission_3.render, "final": final.render}


def run_smoke_test():
    from evaluation.contracts import human_aware_requirements, navigation_requirements, plan_requirements
    plans = {"rows": [{"goal_id": k, "expected_reachable": e, "status": "succeeded" if e else "failed", "waypoint_count": 8 if e else 0, "path_length_m": 1.0 if e else 0, "minimum_clearance_m": .2 if e else None} for k, e in (("open_short", True), ("detour", True), ("narrow", True), ("occupied_goal", False), ("blocked_goal", False))]}
    nav = {"rows": [{"condition": c, "status": "succeeded", "collision_events": 0} for c in ("open", "narrow", "unexpected_obstacle", "open", "unexpected_obstacle")]}
    social = {"policy": {"required_clearance_m": .75, "maximum_nearby_speed_mps": .12}, "baseline": {"scenario_id": "s", "goal_id": "g", "metrics": {"minimum_person_clearance_m": .1}}, "redesign": {"scenario_id": "s", "goal_id": "g", "status": "succeeded", "metrics": {"minimum_person_clearance_m": .8, "maximum_speed_near_people_mps": .1}}, "parameter_changes": ["keepout", "speed"]}
    assert all(r.passed for r in plan_requirements(plans)); assert all(r.passed for r in navigation_requirements(nav)); assert all(r.passed for r in human_aware_requirements(social)); print("Week 9 lab smoke test passed.")


def run_app():
    import streamlit as st
    st.set_page_config(page_title=LAB.title, page_icon="🧭", layout="wide"); initialize(st)
    saved = load_state()
    if saved and not st.session_state.get("loaded_autosave"):
        for key in ("student", "responses", "completed_missions", "evidence"):
            if key in saved: st.session_state[key] = saved[key]
        st.session_state["loaded_autosave"] = True
    render_progress(st)
    completed = set(st.session_state["completed_missions"]); identity = all(v.strip() for v in st.session_state["student"].values()); preflight_ready = bool(st.session_state["evidence"].get("preflight", {}).get("ready"))
    access = {"intro": True, "concepts": identity, "preflight": identity, "mission_1": preflight_ready or "mission_1" in completed, "mission_2": "mission_1" in completed, "mission_3": "mission_2" in completed, "final": "mission_3" in completed}
    with st.sidebar.expander("Lab navigation", expanded=True):
        for stage in LAB.stages:
            if st.button(LABELS[stage], key=f"nav.{stage}", disabled=not access[stage] or stage == current_stage(st), width="stretch"): set_stage(st, stage)
    PAGES[current_stage(st)](st)
    try: save(st); st.sidebar.caption("Progress auto-saved locally")
    except OSError as error: st.sidebar.error(f"Autosave failed: {error}")


def main():
    parser = argparse.ArgumentParser(description=LAB.title); parser.add_argument("--smoke-test", action="store_true"); args = parser.parse_args(); run_smoke_test() if args.smoke_test else run_app()


if __name__ == "__main__": main()
