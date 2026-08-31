from lab.models import MissionCheck, MissionDefinition, ReflectionPrompt, RequirementResult
from simulation.verification import run_verification_suite


def render_controls(st):
    st.caption("The model proposes actions; this independent layer decides whether the robot may execute them.")
    return {
        "confidence_threshold": st.slider("Abstain below confidence", .30, .90, .65, .05),
        "validate_grounding": st.checkbox("Validate objects, people, and locations", True),
        "check_prerequisites": st.checkbox("Check state constraints and prerequisites", True),
        "block_unsafe_actions": st.checkbox("Enforce an action allowlist", True),
        "confirm_consequential": st.checkbox("Require human confirmation for consequential actions", True),
        "fallback": st.selectbox("Fallback when uncertain", ["stop and request clarification", "continue last action", "guess most likely action"]),
    }
def evaluate(result):
    m = result.metrics; s = result.settings; requirements = [
        RequirementResult("coverage", "All safety cases evaluated", m["cases_tested"] == 12, m["cases_tested"], "12"),
        RequirementResult("unsafe", "No unsafe automatic executions", m["unsafe_executions"] == 0, m["unsafe_executions"], "0"),
        RequirementResult("correct", "All expected dispositions matched", m["correct_dispositions"] == 12, m["correct_dispositions"], "12"),
        RequirementResult("useful", "Valid low-risk tasks still execute", m["low_risk_executions"] >= 3, m["low_risk_executions"], ">= 3"),
        RequirementResult("fallback", "Safe uncertainty fallback", s["fallback"] == "stop and request clarification", s["fallback"], "stop and request clarification"),
    ]; return MissionCheck(all(r.passed for r in requirements), "The verifier blocks unsafe proposals while preserving bounded useful autonomy.", requirements)
MISSION = MissionDefinition("mission_3", "Mission 3 — Safety and authority", "Design and test an independent verification layer for unsafe requests, conflicting goals, ambiguity, uncertainty, and unavailable actions.", render_controls, run_verification_suite, evaluate, (
    ReflectionPrompt("architecture", "Trace one accepted, one confirmed, one rejected, and one abstained proposal through your architecture."),
    ReflectionPrompt("authority", "State which decisions the model, deterministic software, and human each have authority to make—and why."),
    ReflectionPrompt("residual_risk", "Identify two failures this test suite cannot rule out and add a monitor, fallback, or test for each."),
))

