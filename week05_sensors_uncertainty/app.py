from __future__ import annotations

import argparse

from lab.autosave import load_state, save
from lab.navigation import LABELS, current_stage, render_progress, set_stage
from lab.session import initialize
from lab_config import LAB
from pages import concepts, final, intro, mission_1, mission_2, mission_3

PAGES = {"intro": intro.render, "concepts": concepts.render, "mission_1": mission_1.render, "mission_2": mission_2.render, "mission_3": mission_3.render, "final": final.render}


def run_smoke_test():
    from missions import mission_1 as m1, mission_2 as m2, mission_3 as m3
    from simulation.scenarios import evaluate_rule, fusion_dataset, run_pipeline
    from simulation.sensors import profile_for_seed, sample_metrics, static_samples
    seed = 2026; name, config = profile_for_seed(seed); metrics = sample_metrics(static_samples(2.0, 240, config, seed), 2.0)
    responses = {"mission_1.mean": metrics["mean"], "mission_1.variance": metrics["variance"], "mission_1.bias": metrics["bias"], "mission_1.median": metrics["median"], "mission_1.dropouts": metrics["dropout_count"], "mission_1.outliers": metrics["outlier_count"], "mission_1.profile": name, **{f"mission_1.{key}": "A substantive explanation grounded in numerical evidence and consequences. " * 2 for key in m1.REFLECTIONS}}
    assert m1.evaluate(metrics, name, responses).passed
    data = fusion_dataset(seed); attempts = []
    for method, window, weight in (("Moving average", 3, .25), ("Median", 3, .25), ("Exponential", 3, .25)):
        attempts.append({"attempt": len(attempts) + 1, **run_pipeline(data, method, window, .5, weight)})
    responses.update({f"mission_2.{key}": "A substantive comparison using measured error, availability, and response delay. " * 2 for key in m2.REFLECTIONS})
    assert any(m2.evaluate(attempts, index, responses).passed for index in range(len(attempts)))
    policies = {}
    for context in ("Warehouse", "Assistive"):
        settings = {"threshold": .75 if context == "Warehouse" else .95, "margin": .1 if context == "Warehouse" else .2, "weight_a": .35, "confirmations": 1, "filter_method": "Median", "window": 3, "missing_policy": "Stop"}
        policies[context] = evaluate_rule(settings, context, seed)
    responses.update({f"mission_3.{key}": "A context-sensitive explanation of error costs, stakeholders, limits, and additional testing. " * 2 for key in m3.REFLECTIONS})
    assert m3.evaluate(policies, responses).passed
    print("Week 5 lab smoke test passed.")


def run_streamlit_app():
    import streamlit as st
    st.set_page_config(page_title=LAB.title, page_icon="📡", layout="wide"); initialize(st)
    saved = load_state()
    if saved and not st.session_state.get("loaded_autosave"):
        for key in ("student", "responses", "completed_missions", "checked_evidence_ids", "mission_2_attempts", "mission_3_results"):
            if key in saved: st.session_state[key] = saved[key]
        st.session_state["loaded_autosave"] = True
    render_progress(st)
    completed = set(st.session_state["completed_missions"])
    identity_ready = all(str(value).strip() for value in st.session_state["student"].values())
    access = {"intro": True, "concepts": identity_ready, "mission_1": identity_ready, "mission_2": "mission_1" in completed, "mission_3": "mission_2" in completed, "final": "mission_3" in completed}
    with st.sidebar.expander("Lab navigation", expanded=True):
        for stage in LAB.stages:
            if st.button(LABELS[stage], key=f"nav.{stage}", disabled=not access[stage] or stage == current_stage(st), width="stretch"): set_stage(st, stage)
    PAGES[current_stage(st)](st)
    try: save(st); st.sidebar.caption("Progress auto-saved locally")
    except OSError as error: st.sidebar.error(f"Autosave failed: {error}")


def main():
    parser = argparse.ArgumentParser(description=LAB.title); parser.add_argument("--smoke-test", action="store_true"); args = parser.parse_args()
    run_smoke_test() if args.smoke_test else run_streamlit_app()


if __name__ == "__main__": main()
