from __future__ import annotations
import argparse
from lab.autosave import load_state, save
from lab.navigation import LABELS, current_stage, render_progress, set_stage
from lab.session import initialize
from lab_config import LAB
from pages import concepts, final, intro, mission_1, mission_2, mission_3, preflight
PAGES = {"intro": intro.render, "concepts": concepts.render, "preflight": preflight.render, "mission_1": mission_1.render, "mission_2": mission_2.render, "mission_3": mission_3.render, "final": final.render}

def run_smoke_test():
    from analysis.map_metrics import analyze_pixels, quality_score
    from analysis.localization import trial_passes
    from missions import mission_1 as m1, mission_2 as m2, mission_3 as m3
    pixels = [205] * 100 + [254] * 750 + [0] * 150; metrics = analyze_pixels(40, 25, 255, pixels, .05); metrics["known_fraction"] = .6
    first = {"strategy": "perimeter_then_interior", "metrics": metrics, "quality_score": max(50, quality_score(metrics))}; second = {"strategy": "room_by_room", "metrics": {**metrics, "known_fraction": .65}, "quality_score": 70}
    responses = {**{f"mission_1.{key}": "A detailed evidence-based explanation of the ROS displays, map metrics, causes, and limitations. " * 2 for key in m1.REFLECTIONS}, **{f"mission_2.{key}": "A detailed comparison of strategies, numerical metrics, visible structure, and loop closure evidence. " * 2 for key in m2.REFLECTIONS}}
    assert m1.evaluate(first, responses, True, True).passed; assert m2.evaluate(first, second, responses).passed
    base = {"sample_count": 40, "duration": 20, "convergence_time": 2, "final_covariance": .1, "settled_position_spread": .03, "pose_jump": .02, "scan_retention": 1.0}
    trials = {"good_initial_pose": {"metrics": base}, "incorrect_initial_pose": {"metrics": {**base, "pose_jump": .8}}, "ambiguous_location": {"metrics": {**base, "final_covariance": .22}}, "degraded_sensor": {"metrics": {**base, "final_covariance": .3, "scan_retention": .5}}}
    responses.update({f"mission_3.{key}": "A detailed interpretation of localization evidence, uncertainty, failure, stakeholders, and safe fallbacks. " * 2 for key in m3.REFLECTIONS})
    assert all(trial_passes(key, value["metrics"]) for key, value in trials.items()); assert m3.evaluate(trials, responses).passed
    print("Week 6 lab smoke test passed.")

def run_streamlit_app():
    import streamlit as st
    st.set_page_config(page_title=LAB.title, page_icon="🗺️", layout="wide"); initialize(st)
    saved = load_state()
    if saved and not st.session_state.get("loaded_autosave"):
        for key in ("student", "responses", "completed_missions", "checked_evidence_ids", "evidence"):
            if key in saved: st.session_state[key] = saved[key]
        st.session_state["loaded_autosave"] = True
    render_progress(st); completed = set(st.session_state["completed_missions"]); identity = all(str(value).strip() for value in st.session_state["student"].values())
    preflight_ready = bool(st.session_state["evidence"].get("preflight", {}).get("ready"))
    access = {"intro": True, "concepts": identity, "preflight": identity, "mission_1": preflight_ready or "mission_1" in completed, "mission_2": "mission_1" in completed, "mission_3": "mission_2" in completed, "final": "mission_3" in completed}
    with st.sidebar.expander("Lab navigation", expanded=True):
        for stage in LAB.stages:
            if st.button(LABELS[stage], key=f"nav.{stage}", disabled=not access[stage] or stage == current_stage(st), width="stretch"): set_stage(st, stage)
    PAGES[current_stage(st)](st)
    try: save(st); st.sidebar.caption("Progress auto-saved locally")
    except OSError as error: st.sidebar.error(f"Autosave failed: {error}")

def main():
    parser = argparse.ArgumentParser(description=LAB.title); parser.add_argument("--smoke-test", action="store_true"); args = parser.parse_args(); run_smoke_test() if args.smoke_test else run_streamlit_app()
if __name__ == "__main__": main()
