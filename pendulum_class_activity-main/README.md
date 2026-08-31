# Live RL Pendulum Activity

This is a one-file live coding activity for teaching Q-learning and Deep Q-learning with the CartPole inverted pendulum.

The main file is `pendulum_rl_live.py`. The reward function is near the top so learners can change it and immediately compare what happens.

## Setup

From a terminal:

```bash
cd rl_pendulum_activity
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate with:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PyTorch does not install cleanly on a newer Python version, make the venv with Python 3.11 or 3.12.

## Run

```bash
streamlit run pendulum_rl_live.py
```

Open the local URL Streamlit prints in the terminal.

## Streamlit Community Cloud

This folder is ready to deploy as its own GitHub repo.

1. Push `rl_pendulum_activity/` to GitHub.
2. Create a new Streamlit Community Cloud app from that repo.
3. Use `pendulum_rl_live.py` as the main file.
4. Share the deployed app URL with students.

See `STREAMLIT_CLOUD.md` for the short deployment checklist.

## Quick Check

```bash
python pendulum_rl_live.py --smoke-test
```

That command runs tiny Q-learning and DQN training jobs without opening the web app.

## Student Submissions

Students should run the app from a cloned repo and complete the missions locally.
There is no GIF upload or manual save step. The app automatically saves written
responses throughout the activity and saves the actual replay GIF after every
training run. A checked mission is kept current as the student completes its
explanations.

The app writes Git-ready files under `student_submission/`:

- `autosave/responses.json` and `autosave/responses.md` for check-ins and written answers
- `<mission>/run.gif` for the latest actual replay or mission-check run
- `<mission>/latest_run.json` for the latest training configuration and evaluation
- `<mission>/submission.json` for the checked mission record
- `<mission>/explanation.md`
- `<mission>/learning_curve.csv`

The **Continue to next mission** button only advances the activity after all four
mission explanations are complete; it does not perform the save. After finishing
the lab, commit and push the submission folder, then submit the GitHub commit link:

```bash
git add student_submission
git commit -m "Submit pendulum lab"
git push
```

## Additional Local Labs

This repo also includes a separate local-only robotics lab:

```bash
streamlit run pid_odometry_lab/app.py
```

That lab teaches open-loop control, PID tuning, and differential-drive odometry.
It is designed for local runs and Git-ready automatic submission artifacts, not
Streamlit Cloud submission collection.

## Live Lecture Flow

1. Start with Q-learning and the baseline reward.
2. Build rewards as `reward += normalized signal * number`, then retrain and compare the learning curve.
3. Use the observation/action lab to hide velocity, swap `theta` for `sin(theta)` and `cos(theta)`, or add a zero-force action.
4. Try a fixed starting state to see whether training changes when every episode starts from the same pose.
5. Open `pendulum_rl_live.py` and edit `reward_function(...)`, `observation_function(...)`, or `action_function(...)` directly.
6. Switch to DQN after the audience understands action values.
7. Use "What the agent learned" to compare the Q-table's buckets with the DQN's continuous value map.
8. Use the evaluation rollout to connect the return curve to the physical balancing behavior.
