from __future__ import annotations
import argparse
from lab.autosave import load_state,save
from lab.navigation import LABELS,current_stage,render_progress,set_stage
from lab.session import initialize
from lab_config import LAB
from pages import concepts,final,intro,mission_1,mission_2,mission_3,preflight
PAGES={"intro":intro.render,"concepts":concepts.render,"preflight":preflight.render,"mission_1":mission_1.render,"mission_2":mission_2.render,"mission_3":mission_3.render,"final":final.render}
def run_smoke_test():
    from evaluation.metrics import evaluate_rows,threshold_sweep
    from evaluation.behavior import BehaviorConfig,DEFAULT_SCENARIOS,evaluate_scenarios
    from missions import mission_1 as m1,mission_2 as m2,mission_3 as m3
    conditions=("normal","dim","glare","far","occluded","rotated","cluttered","distractor");rows=[{"condition":name,"expected":name!="distractor","detected":name not in ("far","distractor"),"confidence":.85 if name not in ("far","distractor") else .2,"latency_ms":12} for name in conditions];metrics=evaluate_rows(rows)
    responses={**{f"mission_1.{key}":"Evidence-based explanation of parameter effects, condition outcomes, image evidence, and a specific failure. "*2 for key in m1.REFLECTIONS},**{f"mission_2.{key}":"Evidence-based comparison of precision, recall, confidence thresholds, errors, limitations, and safety. "*2 for key in m2.REFLECTIONS}}
    classical={"rows":rows,"metrics":metrics};learned={"rows":rows,"metrics":metrics,"threshold_sweep":threshold_sweep(rows),"selected_threshold":.5};assert m1.evaluate(classical,responses,4).passed;assert m2.evaluate(learned,responses,4).passed
    behavior={"config":BehaviorConfig().__dict__,"result":evaluate_scenarios(DEFAULT_SCENARIOS,BehaviorConfig())};responses.update({f"mission_3.{key}":"Evidence-based system trace, environmental breakdown analysis, safe fallback, and deployment limitation. "*2 for key in m3.REFLECTIONS});assert m3.evaluate(behavior,responses,2).passed;print("Week 8 lab smoke test passed.")
def run_streamlit_app():
    import streamlit as st
    st.set_page_config(page_title=LAB.title,page_icon="📷",layout="wide");initialize(st);saved=load_state()
    if saved and not st.session_state.get("loaded_autosave"):
        for key in ("student","responses","completed_missions","checked_evidence_ids","evidence"):
            if key in saved:st.session_state[key]=saved[key]
        st.session_state["loaded_autosave"]=True
    render_progress(st);completed=set(st.session_state["completed_missions"]);identity=all(str(value).strip() for value in st.session_state["student"].values());preflight_ready=bool(st.session_state["evidence"].get("preflight",{}).get("ready"));access={"intro":True,"concepts":identity,"preflight":identity,"mission_1":preflight_ready or "mission_1" in completed,"mission_2":"mission_1" in completed,"mission_3":"mission_2" in completed,"final":"mission_3" in completed}
    with st.sidebar.expander("Lab navigation",expanded=True):
        for stage in LAB.stages:
            if st.button(LABELS[stage],key=f"nav.{stage}",disabled=not access[stage] or stage==current_stage(st),width="stretch"):set_stage(st,stage)
    PAGES[current_stage(st)](st)
    try:save(st);st.sidebar.caption("Progress auto-saved locally")
    except OSError as error:st.sidebar.error(f"Autosave failed: {error}")
def main():
    parser=argparse.ArgumentParser(description=LAB.title);parser.add_argument("--smoke-test",action="store_true");args=parser.parse_args();run_smoke_test() if args.smoke_test else run_streamlit_app()
if __name__=="__main__":main()
