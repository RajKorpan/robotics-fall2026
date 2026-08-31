from lab.models import MissionCheck, MissionDefinition, ReflectionPrompt, RequirementResult
from simulation.language import run_language_suite


def render_controls(st):
    st.info("The response bank is frozen so every student analyzes the same original outputs. Do not rewrite the requests or plans before recording them.")
    return {"response_bank": st.selectbox("Controlled model version", ["course-fm-1.0"])}
def evaluate(result):
    m = result.metrics; requirements = [
        RequirementResult("coverage", "All requests evaluated", m["requests_tested"] == 6, m["requests_tested"], "6"),
        RequirementResult("ungrounded", "Grounding failures exposed", m["ungrounded_plans"] >= 4, m["ungrounded_plans"], ">= 4"),
        RequirementResult("capability", "Hallucinated capabilities exposed", m["hallucinated_capability_cases"] >= 2, m["hallucinated_capability_cases"], ">= 2"),
        RequirementResult("prerequisite", "Missing prerequisites exposed", m["missing_prerequisite_cases"] >= 2, m["missing_prerequisite_cases"], ">= 2"),
    ]; return MissionCheck(all(r.passed for r in requirements), "The plan suite exposes capability, grounding, ambiguity, and prerequisite failures.", requirements)
MISSION = MissionDefinition("mission_1", "Mission 1 — Language to robot plan", "Evaluate whether generated action sequences are executable, grounded in the known world, and complete enough to authorize.", render_controls, run_language_suite, evaluate, (
    ReflectionPrompt("case_analysis", "Analyze two failed plans step by step. Identify the first invalid assumption and its downstream consequence."),
    ReflectionPrompt("executable_vs_reasonable", "Explain why syntactically executable, grounded, reasonable, and safe are different claims."),
    ReflectionPrompt("better_interface", "Specify what world state, capabilities, or clarification interface the model needed before planning."),
))

