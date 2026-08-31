from evaluation.contracts import navigation_requirements
REFLECTIONS = ("plan_execution", "recovery", "measurement")
def evaluate(evidence): return navigation_requirements(evidence or {})

