# Robotics Lab Template

This directory is a runnable starting point for new robotics labs. It preserves the common instructional and submission structure of the reinforcement-learning and PID/odometry labs while separating shared infrastructure from topic-specific code.

## Run

```powershell
cd lab-template
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Run the noninteractive verification with:

```powershell
python app.py --smoke-test
python -m unittest discover -s tests -v
```

The default instructor password is `instructor`. Set `LAB_INSTRUCTOR_PASSWORD` to override it.

## Create a new lab

1. Copy this directory and rename it for the topic.
2. Edit `LAB` in `lab_config.py`.
3. Replace the instructional copy in `pages/` and `content/`.
4. Put domain calculations in `simulation/`; keep them independent of Streamlit.
5. Implement the controls, run function, evaluation rules, and reflections in each `missions/mission_*.py` file.
6. Add specialized browser interactions under `components/` only when ordinary Streamlit controls are insufficient.
7. Add one known passing and one known failing test case for every mission.

## Boundaries

- `pages/` teaches and renders.
- `missions/` defines challenges and deterministic gates.
- `simulation/` computes behavior and metrics.
- `lab/` owns navigation, state, autosave, instructor access, and submissions.
- `components/` contains optional custom HTML/JavaScript interactions.

Every experiment produces a `RunResult`. Every gate produces a `MissionCheck`. The shared mission page connects those two contracts and saves only the exact run that passed.

## Submission output

The app writes:

```text
student_submission/
├── autosave/
│   ├── responses.json
│   └── responses.md
├── mission_1/
│   ├── latest_run.json
│   ├── submission.json
│   ├── explanation.md
│   └── run.csv
├── mission_2/
├── mission_3/
├── final_reflection.md
└── manifest.json
```

Binary evidence such as GIFs can be placed in `RunResult.artifacts`; the submission layer writes it to the mission's `activity_gifs/` directory.


## Required final reflection

After the technical work, complete the individual [final reflection](../FINAL_REFLECTION.md). Respond to any or all of the five prompts in 1–300 words. A blank response or a response over 300 words cannot finalize the submission. The app saves the response as `student_submission/final_reflection.md`, separate from technical syntheses and mission explanations.
