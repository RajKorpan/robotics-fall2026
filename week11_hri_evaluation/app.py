from __future__ import annotations
import argparse
from lab.autosave import load,save
from lab.navigation import LABELS,current_stage,render_progress,set_stage
from lab.session import initialize
from lab_config import LAB
from pages import concepts,final,intro,mission_1,mission_2,mission_3,preflight

PAGES={"intro":intro.render,"concepts":concepts.render,"preflight":preflight.render,"mission_1":mission_1.render,"mission_2":mission_2.render,"mission_3":mission_3.render,"final":final.render}


def sample_trials(version, improved=False):
    scenarios=("clear_request","no_response","correction","ambiguous_request","alternate_modality"); rows=[]
    for i,name in enumerate(scenarios):
        rows.append({"scenario_id":name,"task_success": improved or i not in (2,4),"intent_understood":improved or i!=0,"listening_state_clear":improved or i not in (1,4),"recovered_without_facilitator":improved or i!=2,"predictability_rating":5 if improved else 3,"feedback_rating":5 if improved else 3,"access_barrier":False if improved else i==4,"safety_stop":False,"completion_time_s":18-i if improved else 24+i,"note":"Non-identifying observation of interface behavior."})
    return {"schema_version":1,"design_version":version,"participant_code":"P-7K4Q","consent_confirmed":True,"recording_used":False,"trials":rows}


def run_smoke_test():
    from evaluation.contracts import baseline_requirements,prototype_requirements,redesign_requirements
    prototype={"observed_states":["IDLE","ANNOUNCE","APPROACH","LISTENING","CONFIRMING","ACTING","COMPLETE","ERROR"],"motion_enabled":False,"stop_tested":True,"dry_runs":2}; baseline=sample_trials("baseline"); redesign=sample_trials("redesign",True); comparison={"baseline":baseline,"redesign":redesign,"design_changes":["persistent listening cue","explicit recovery text"]}
    assert all(r.passed for r in prototype_requirements(prototype)); assert all(r.passed for r in baseline_requirements(baseline)); assert all(r.passed for r in redesign_requirements(comparison)); print("Week 11 lab smoke test passed.")


def run_app():
    import streamlit as st
    st.set_page_config(page_title=LAB.title,page_icon="🤝",layout="wide"); initialize(st); saved=load()
    if saved and not st.session_state.get("loaded_autosave"):
        for key in ("student","responses","completed_missions","evidence"):
            if key in saved: st.session_state[key]=saved[key]
        st.session_state["loaded_autosave"]=True
    render_progress(st); completed=set(st.session_state["completed_missions"]); identity=all(v.strip() for v in st.session_state["student"].values()); ready=bool(st.session_state["evidence"].get("preflight",{}).get("ready")); access={"intro":True,"concepts":identity,"preflight":identity,"mission_1":ready or "mission_1" in completed,"mission_2":"mission_1" in completed,"mission_3":"mission_2" in completed,"final":"mission_3" in completed}
    with st.sidebar.expander("Lab navigation",expanded=True):
        for stage in LAB.stages:
            if st.button(LABELS[stage],key="nav."+stage,disabled=not access[stage] or stage==current_stage(st),width="stretch"): set_stage(st,stage)
    PAGES[current_stage(st)](st)
    try: save(st); st.sidebar.caption("Progress auto-saved locally")
    except OSError as error: st.sidebar.error(f"Autosave failed: {error}")


def main():
    parser=argparse.ArgumentParser(description=LAB.title); parser.add_argument("--smoke-test",action="store_true"); args=parser.parse_args(); run_smoke_test() if args.smoke_test else run_app()
if __name__=="__main__": main()

