from lab.models import MissionCheck,MissionDefinition,ReflectionPrompt,RequirementResult
from simulation.privacy import run_privacy
def render_controls(st):
    st.caption("The robot estimates whether someone may need assistance. Configure the minimum data lifecycle that supports this purpose.")
    return {"data_collected":st.selectbox("Data collected",["continuous video","cropped person images","event features only","no sensing"]),"processing":st.radio("Raw processing",["cloud","local"],horizontal=True),"store_raw_video":st.checkbox("Store raw video",True),"retention_hours":st.slider("Retention (hours)",0,720,168),"consent":st.selectbox("Consent",["notice only","opt-out","just-in-time opt-in","none"]),"deletion_enabled":st.checkbox("User-accessible deletion",False),"anonymize_logs":st.checkbox("Remove identifiers from logs",False),"role_based_access":st.checkbox("Role-based access to logs",False)}
def evaluate(result):
    m=result.metrics; requirements=[RequirementResult("privacy","All privacy requirements",m["requirements_passed"]==m["requirements_total"],f"{m['requirements_passed']}/{m['requirements_total']}","8/8"),RequirementResult("utility","Assistance detection remains usable",m["task_utility"]>=.80,m["task_utility"],">= 0.80"),RequirementResult("risk","Residual course risk score",m["privacy_risk_score"]<=1,m["privacy_risk_score"],"<= 1")]; return MissionCheck(all(r.passed for r in requirements),"The design meets the stated privacy requirements without eliminating the assistance function.",requirements)
MISSION=MissionDefinition("mission_1","Mission 1 — Privacy by design","Choose what the robot collects, where it processes data, what it stores, who can access it, and how people consent or delete records.",render_controls,run_privacy,evaluate,(
 ReflectionPrompt("necessity","Explain why the selected data is necessary and proportionate to the assistance purpose. Name data you deliberately excluded."),
 ReflectionPrompt("lifecycle","Trace one observation from collection through processing, logging, retention, access, and deletion."),
 ReflectionPrompt("tradeoff","Use utility and risk results to explain the trade-off. Identify a privacy failure the checks do not cover."),))

