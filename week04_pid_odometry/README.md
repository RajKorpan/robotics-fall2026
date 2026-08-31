# Week 4 — PID and Odometry

This lab is a local Streamlit activity for exploring two core robotics ideas:

- **PID control:** how proportional, integral, and derivative terms change a robot's response to tracking error.
- **Odometry:** how a robot estimates position and heading from wheel motion, and how small errors accumulate over time.

Students run the lab on their own computer, tune controllers, inspect simulated motion, and export submission files for an instructor to review.

## Run Locally

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run week04_pid_odometry/app.py
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then run the same `pip` commands and the Streamlit command below. Streamlit prints a local URL, usually `http://localhost:8501`, which opens the lab in a browser.

```bash
streamlit run week04_pid_odometry/app.py
```

## Local Only

This lab is intended for local classroom and homework use. It is **not intended for Streamlit Community Cloud hosting**.

Reasons:

- Student work is generated on the machine running the app.
- Streamlit Cloud's server filesystem should not be treated as durable class storage.
- A hosted class-wide submission workflow would need an external backend such as an LMS, database, object store, or form service.
- Local runs make it easier for students to inspect generated files and for instructors to collect exact artifacts.

For more detail, see [LOCAL_ONLY.md](LOCAL_ONLY.md).

## Submissions

Students complete the lab locally. At each passed mission they can attach multiple
GIFs of their interactive work, then use **Save to submissions folder** to collect
the GIFs, written answers, settings, plots, and data under `student_submission/`.

A typical downloaded submission may include:

- `submission.json` with settings, scores, and metadata
- `explanation.md` with the student's written answers
- `baseline_trials.csv`, `pid_run.csv`, and `odometry_run.csv`
- `baseline_plot.png`, `pid_plot.png`, and `odometry_plot.png`
- `manifest.json` describing the files in the export
- `activity_gifs/*.gif` showing the interactive activities

After the final export, students commit and push that folder and submit the GitHub
commit link:

```bash
git add student_submission
git commit -m "Submit PID and odometry lab"
git push
```

The ZIP controls remain available as backup exports.

## What Students Learn

By the end of the lab, students should be able to:

- Describe the role of the P, I, and D terms in a feedback controller.
- Predict what happens when gains are too small, too large, or poorly balanced.
- Compare overshoot, settling time, steady-state error, and oscillation across controller settings.
- Explain how wheel encoder measurements can be integrated into an odometry estimate.
- Identify why odometry drifts when wheel radius, track width, timing, or sensor readings are imperfect.
- Connect controller quality to odometry quality: a poorly tuned controller can create motion that is harder to estimate and verify.
- Use plots, replayed motion, and exported run data to justify a control design.

## Suggested Student Workflow

1. Start with the default controller and observe the baseline motion.
2. Change one PID gain at a time and record what changes.
3. Compare the desired path with the estimated odometry path.
4. Look for drift, overshoot, oscillation, and steady-state error.
5. Tune the controller until the robot follows the target more reliably.
6. Write a short explanation connecting the chosen gains to the observed behavior.
7. Save the submission folder, commit it, push it, and submit the GitHub commit link.

## Instructor Notes

Keep collection outside Streamlit unless a dedicated backend has been added. For workshops, the simplest reliable flow is:

1. Students clone or download the repo.
2. Students run the Streamlit lab locally.
3. Students save their completed artifacts under `student_submission/`.
4. Students commit and push that folder, then submit the GitHub commit link.

This keeps grading artifacts tied to each student and avoids relying on temporary server-side files.
