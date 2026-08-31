from evaluation.contracts import human_aware_requirements
REFLECTIONS = ("appropriateness", "redesign", "tradeoff")
def evaluate(evidence): return human_aware_requirements(evidence or {})

