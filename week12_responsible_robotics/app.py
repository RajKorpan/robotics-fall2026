from __future__ import annotations
import argparse
from lab.autosave import autosave_responses,load_responses
from lab.navigation import current_stage,render_progress
from lab.session import initialize_session
from lab_config import LAB
from pages import background,concepts,final_submission,intro,missions,playground
PAGES={"intro":intro.render,"concepts":concepts.render,"background":background.render,"playground":playground.render,"lab":missions.render,"final_submission":final_submission.render}
PASSING={
 "mission_1":{"data_collected":"event features only","processing":"local","store_raw_video":False,"retention_hours":24,"consent":"just-in-time opt-in","deletion_enabled":True,"anonymize_logs":True,"role_based_access":True},
 "mission_2":{"threshold":.55,"intervention":"alternate sensor","abstain_margin":.08,"human_review":True},
 "mission_3":{"max_speed_near_people":.20,"personal_space_m":.80,"confidence_threshold":.75,"emergency_stop":True,"confirm_consequential":True,"visual_feedback":True,"audio_feedback":True,"text_controls":True,"physical_stop":True,"local_fallback":True,"fallback":"stop and request help"},
}
def run_smoke_test():
    from missions import MISSIONS
    for mission_id,mission in MISSIONS.items():
        result=mission.run(PASSING[mission_id]); check=mission.evaluate(result); assert result.traces and check.passed,(mission_id,result.metrics); print(f"{mission_id}: PASS — {result.metrics}")
    print("Week 12 lab smoke test passed.")
def run_app():
    import streamlit as st
    st.set_page_config(page_title=LAB.title,page_icon="⚖️",layout="wide"); initialize_session(st)
    if not st.session_state["responses"]:
        saved=load_responses(); st.session_state["responses"]=dict(saved.get("responses",{}))
        if saved.get("student") and not any(st.session_state["student"].values()): st.session_state["student"]=dict(saved["student"])
    render_progress(st); PAGES[current_stage(st)](st)
    try: path=autosave_responses(st); st.sidebar.caption(f"Responses auto-saved to {path.parent.name}/")
    except OSError as error: st.sidebar.error(f"Autosave failed: {error}")
def main():
    parser=argparse.ArgumentParser(description=LAB.title); parser.add_argument("--smoke-test",action="store_true"); args=parser.parse_args(); run_smoke_test() if args.smoke_test else run_app()
if __name__=="__main__": main()

