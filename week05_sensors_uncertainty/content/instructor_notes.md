# Instructor notes — Week 5

## Design intent

This is a 2.5–3 hour individual lab. It is deliberately independent of ROS so students can focus on the epistemic problem: a robot acts on measurements, not ground truth. Each Course ID produces deterministic data, allowing students to resume work and instructors to reproduce results while discouraging answer copying.

## Suggested timing

| Activity | Time |
|---|---:|
| Introduction and playground | 20–25 min |
| Mission 1: characterize | 35–45 min |
| Mission 2: filter and fuse | 45–55 min |
| Mission 3: decisions | 45–55 min |
| Synthesis and artifact check | 15–20 min |

## Mission evidence

Mission 1 checks estimates against computed statistics with stated tolerances. The assigned sensor emphasizes one defect—bias, noise, quantization, or outliers—but may include minor dropout and noise so diagnosis requires judgment. Ask students why a larger sample reduces uncertainty in a mean but does not remove systematic bias.

Mission 2 uses a shared truth trajectory and two complementary sensors. Sensor A is fast, noisy, and outlier-prone. Sensor B is slower and biased but steadier. Students must log at least three configurations and explicitly compare moving average with median. The maximum-error allowance is wider than the RMSE allowance because the trajectory includes a deliberate abrupt transition; delay and RMSE prevent students from “solving” the task through excessive smoothing.

Mission 3 evaluates seven cases, including conflict and simultaneous dropout. A passing missing-data policy must stop or declare insufficient evidence. The assistive context has a stricter false-safe and delay criterion. Written prompts make students identify who bears each error cost rather than treating the task as numerical optimization alone.

## Assessment suggestion (100 points)

- Mission 1 measurements and diagnosis: 25
- Mission 2 experimental method and final pipeline: 25
- Mission 3 policy performance and context comparison: 30
- Final synthesis: 15
- Artifact completeness and clarity: 5

Automated gates establish minimum completeness, not writing quality. Review whether claims cite the student's own metrics, whether parameter choices are causally explained, and whether the sociotechnical analysis names concrete stakeholders and limitations.

## Facilitation and accessibility

- Students work individually, but whole-class discussion of concepts is appropriate before work begins.
- Do not grade a particular “correct” policy parameter set; many sets can satisfy the evidence criteria.
- The CSV outputs support students who prefer external calculation tools.
- Plots are supplemented with tables and textual metric labels; completion never relies on color identification alone.
- If a student changes their Course ID, their deterministic scenario changes. Have them restore the original ID rather than redo calculations.

## Resetting a local attempt

Move `student_submission/` to a safe backup location, then relaunch the app. Do not delete it until the student confirms the backup is usable.
