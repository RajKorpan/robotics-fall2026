# Local-Only Operation

The PID odometry lab should be run on a student's or instructor's own machine.

## Why It Is Not A Streamlit Cloud App

Streamlit Community Cloud is useful for demos, but this lab depends on local generated work:

- Students create submission artifacts during a run.
- Generated files are written to the Git-ready `student_submission/` folder.
- Hosted Streamlit filesystems are not a reliable long-term place to collect class work.
- Multiple students using one hosted app would need authentication, per-student storage, and a backend collection service.

Without that backend, a hosted app can demonstrate the activity but should not be treated as the source of record for student submissions.

## Recommended Collection Model

Use local execution plus external submission:

1. Student runs the lab locally with `streamlit run ...`.
2. Student completes the PID and odometry tasks.
3. Student saves the complete `student_submission/` folder.
4. Student commits and pushes that folder, then submits the GitHub commit link.

The ZIP export remains available as a backup when a GitHub commit link cannot be used.

## What To Preserve

For grading and feedback, preserve the exported files rather than screenshots alone. The most useful artifacts are:

- machine-readable run metadata, such as `submission.json`
- the student's explanation, such as `explanation.md`
- run data, such as `learning_curve.csv`
- a visual replay, such as `run.gif`

These files let instructors check both the final behavior and the reasoning behind the controller and odometry choices.
