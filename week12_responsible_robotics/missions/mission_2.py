from lab.models import MissionCheck,MissionDefinition,ReflectionPrompt,RequirementResult
from simulation.fairness import run_fairness
def render_controls(st):
    return {"threshold":st.slider("Detection threshold",.30,.80,.55,.05),"intervention":st.selectbox("Performance intervention",["none","additional calibration data","alternate sensor"]),"abstain_margin":st.slider("Abstain within ±",0.0,.20,.0,.02),"human_review":st.checkbox("Route abstentions to trained human review",False)}
def evaluate(result):
    m=result.metrics; requirements=[RequirementResult("coverage","All 32 subgroup samples",m["samples"]==32,m["samples"],"32"),RequirementResult("tpr","Worst-group true-positive rate",m["worst_group_tpr"]>=.75,m["worst_group_tpr"],">= 0.75"),RequirementResult("fpr","Worst-group false-positive rate",m["worst_group_fpr"]<=.25,m["worst_group_fpr"],"<= 0.25"),RequirementResult("gap","TPR disparity",m["tpr_gap"]<=.20,m["tpr_gap"],"<= 0.20"),RequirementResult("automation","Minimum automated coverage",m["minimum_automated_coverage"]>=.50,m["minimum_automated_coverage"],">= 0.50"),RequirementResult("workload","Human-review rate",m["review_rate"]<=.35,m["review_rate"],"<= 0.35")]; return MissionCheck(all(r.passed for r in requirements),"The intervention meets stated subgroup performance, coverage, and review-workload criteria.",requirements)
MISSION=MissionDefinition("mission_2","Mission 2 — Fairness and performance","Inspect subgroup errors, then change sensing/data, thresholds, abstention, and review behavior until every group meets explicit requirements.",render_controls,run_fairness,evaluate,(
 ReflectionPrompt("diagnosis","Compare all four subgroup confusion patterns before intervention. Which errors matter for the assistance task and why?"),
 ReflectionPrompt("intervention","Explain the causal mechanism and assumptions of your selected intervention. Why is changing a threshold alone insufficient here?"),
 ReflectionPrompt("tradeoffs","Use disparity, coverage, false-positive, and review-rate evidence to discuss who benefits, who bears costs, and what remains uncertain."),))

