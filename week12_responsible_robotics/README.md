# Week 12 — Responsible Robotics by Design

An individual, self-contained Streamlit lab in which students translate responsible-robotics concerns into executable system configuration and measurable behavior.

## Central distinction

An ethics audit asks what could go wrong. This lab asks:

> What will you change in the system, what consequence do you predict, and what evidence shows that the change meets a stated requirement?

The system is a configurable assistive/service robot with perception, user-related data, autonomous decisions, interaction, and bounded actions. Students revise designs until explicit tests pass; passing is bounded evidence, not a universal certification.

## Learning sequence

1. **Concepts:** translate privacy, fairness, safety, accessibility, and human-control concerns into requirements and tests.
2. **Architecture:** trace sensing through data policy, perception, abstention/review, safety/access policy, and action.
3. **Sandbox:** manipulate policies without affecting submission evidence.
4. **Mission 1 — Privacy by design:** minimize collection, keep raw processing local, prevent raw-video storage, limit retention and access, require meaningful consent, and enable deletion while preserving useful assistance detection.
5. **Mission 2 — Fairness and performance:** inspect four subgroup/condition confusion patterns and test threshold, calibration-data, alternate-sensor, abstention, and human-review interventions.
6. **Mission 3 — Safety, accessibility, and human control:** configure speed, distance, action confidence, emergency stop, consequential-action confirmation, redundant feedback/control modalities, and local fallback.
7. **Synthesis:** explain how these choices changed the architecture and who retains authority.

## Run

```powershell
cd week12_responsible_robotics
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On macOS/Linux, activate with `source .venv/bin/activate`.

No ROS installation, API key, account, or network connection is required.

## Mission 1 requirements

The course scenario asks whether someone may need assistance. A passing design:

- collects event features rather than identifiable raw imagery;
- processes raw sensor input locally and stores no raw video;
- retains event records for no more than 24 hours;
- uses just-in-time opt-in;
- provides deletion, identifier removal, and role-based access; and
- retains at least 0.80 simulated task utility.

The utility and privacy-risk values are course-model outputs for comparison, not empirical deployment guarantees.

## Mission 2 dataset and limits

The frozen 32-sample dataset has four labeled conditions: well-lit, low-light, darker-scene, and mobility-aid-present. The labels describe test conditions, not inherent human categories. Students compare true-positive rate, false-positive rate, TPR disparity, automated coverage, human-review workload, and overall accuracy.

The simulated reviewer resolves fixture abstentions correctly. That simplifying assumption makes routing trade-offs visible but overstates real review reliability. Students must identify it in their analysis. A passing run requires:

- worst-group TPR ≥ 0.75;
- worst-group FPR ≤ 0.25;
- TPR disparity ≤ 0.20;
- at least 0.50 automated coverage in every group; and
- review workload ≤ 0.35.

These thresholds are assignment requirements for this scenario, not universal definitions of fairness.

## Mission 3 scenarios

Eight checks cover a nearby person, personal space, uncertain perception, emergency stop, consequential action, interaction without sound, interaction without vision, and network/model loss. A valid design must pass every scenario and preserve four complementary feedback/control affordances.

Course values such as 0.20 m/s and 0.80 m are scenario-specific design constraints. Real systems require contextual safety engineering, standards, stakeholder participation, and validation beyond this lab.

## Submission

This is an **individual lab**. Submit `student_submission/` and the individual Git commit. The generated evidence includes:

- exact settings for every passing design;
- row-level checks and subgroup sample decisions;
- aggregate utility, privacy, fairness, workload, safety, and access metrics;
- 40+ word mission explanations;
- a 250–350 word final synthesis; and
- `manifest.json`.

## Maintainer checks

```powershell
python app.py --smoke-test
python -m unittest discover -s tests -v
python -m compileall -q .
```

