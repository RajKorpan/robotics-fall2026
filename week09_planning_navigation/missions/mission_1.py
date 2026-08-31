from evaluation.contracts import plan_requirements
REFLECTIONS = ("prediction", "comparison", "failure")
def evaluate(evidence): return plan_requirements(evidence or {})

