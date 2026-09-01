# Week 10 — Foundation Models for Robotics

An individual, self-contained Streamlit lab about using broad but fallible language and vision-language capabilities inside a bounded robotics architecture.

## Central question

> If a foundation model is unreliable, what architecture allows us to use it safely anyway?

Students do not train a model and do not need ROS, an API key, an account, or network access. A versioned course response bank produces reproducible language plans and visual interpretations with deliberate ambiguity, hallucinated capabilities, missing prerequisites, false positives, false negatives, and unsafe recommendations. These are instructional fixtures—not benchmark claims about a particular commercial model.

## Learning sequence

1. **Concepts:** separate plausible output from executable, grounded, complete, safe, and authorized output.
2. **System model:** place schema, grounding, state, policy, human confirmation, fallback, and runtime monitoring between model proposals and actuators.
3. **Sandbox:** inspect the response banks and test thresholds or verification controls without affecting submission evidence.
4. **Mission 1 — Language to plan:** evaluate six requests and preserve the original plans; locate capability hallucinations, ambiguity, and missing prerequisites.
5. **Mission 2 — Vision and language:** compare eight controlled scenes spanning low light, occlusion, ambiguity, unusual objects, misleading context, and partial views; analyze confidence and recommendation failures.
6. **Mission 3 — Safety and authority:** configure an independent verifier and pass twelve cases containing unsafe requests, conflicts, uncertainty, unavailable actions, and consequential choices.
7. **Synthesis:** defend a bounded-autonomy architecture and identify residual risk.

## Run

```powershell
cd week10_foundation_models
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```


## Required final reflection

After the technical work, complete the individual [final reflection](../FINAL_REFLECTION.md). Respond to any or all of the five prompts in 1–300 words. A blank response or a response over 300 words cannot finalize the submission. The app saves the response as `student_submission/final_reflection.md`, separate from technical syntheses and mission explanations.


On macOS/Linux, activate with `source .venv/bin/activate`.

## What students manipulate

- the confidence threshold used to accept visual interpretations;
- grounding and prerequisite validators;
- an explicit robot-action allowlist;
- human confirmation for consequential actions; and
- uncertain-output fallback behavior.

The final verification interface returns exactly one disposition:

```text
EXECUTE  — bounded, validated action may enter the skill layer
CONFIRM  — a person must resolve ambiguity or authorize consequence
ABSTAIN  — evidence is insufficient; stop and request clarification
REJECT   — action/circumstance violates capability, state, or policy
```

Confidence is deliberately insufficient by itself. High-confidence proposals can still be ungrounded or prohibited, and valid lower-confidence proposals may need abstention.

## Submission

This is an **individual lab**. Submit `student_submission/` plus the individual Git commit. The generated directory contains:

- every original controlled model output and disposition;
- mission settings and metrics;
- visual scene SVG artifacts;
- requirement results and 40+ word mission explanations;
- a 200–300 word final synthesis; and
- `manifest.json`.

## Instructor notes

The course bank is intentionally inspectable. This prevents API drift, expense, privacy exposure, and unequal results from obscuring the systems lesson. If an instructor adds a live-model extension, keep it ungraded, record model/provider/version/date and exact prompts, prohibit sensitive images, and retain the frozen bank as the graded baseline.

Do not describe a passing verifier as proof of safety. It passes twelve specified tests. Ask students which distributions, sensor failures, tool side effects, prompt/context attacks, timing failures, and human factors remain outside the evidence.

## Maintainer checks

```powershell
python app.py --smoke-test
python -m unittest discover -s tests -v
python -m compileall -q .
```
