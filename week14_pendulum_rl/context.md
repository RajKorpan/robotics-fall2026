# Context for next CLI session

## Repo purpose

This repo is a Streamlit teaching app for reinforcement learning with the CartPole inverted pendulum. Students first learn RL concepts, then design observations, actions, and rewards, train agents, inspect learning curves/policy maps, and complete gated missions.

## Entry points

- Main app: `pendulum_rl_live.py`
- Run app: `.venv/bin/streamlit run pendulum_rl_live.py`
- Non-interactive health check: `.venv/bin/python pendulum_rl_live.py --smoke-test`
- Deploy notes: `README.md`, `STREAMLIT_CLOUD.md`
- Local custom Streamlit components:
  - `drag_canvas/index.html` for drag/drop reward, observation, and action builders
  - `pendulum_playground/index.html` for the pendulum intro interaction
  - `rl_concepts/index.html` for the RL concepts mini-game/slides
- Cached/generated demo assets: `assets/demo_assets.pkl`
- Generated student submissions go under `submissions/`; this directory is gitignored.

## Important code structure

- Live-coding hooks near the top:
  - `observation_function(...)`
  - `action_function(...)`
  - `reward_function(...)`
- Reward builder/evaluator:
  - `reward_signal_observations(...)`
  - `reward_term_value(...)`
  - `evaluate_reward_tokens(...)`
  - `normalize_reward_builder_items(...)`
- Environment/training:
  - `TrainSettings`, `TrainingResult`
  - `make_env(...)`, `reset_env(...)`, `step_cartpole_with_force(...)`
  - `train_q_learning(...)`, `train_dqn(...)`, `train_agent(...)`
  - `evaluate_policy(...)`, `policy_value_grid(...)`, `make_policy_value_figure(...)`
- Lesson pages:
  - `render_intro_page`
  - `render_rl_concepts_page`
  - `render_background_page`
  - `render_pendulum_intro_page`
  - `render_observation_slideshow_page`
  - `render_action_slideshow_page`
  - `render_reward_slideshow_page`
  - `render_algorithm_demo_page`
  - `run_streamlit_app`
- Lab controls:
  - `sidebar_settings(...)`
  - `behavior_controls(...)`
  - `reward_controls(...)`
  - `ethical_controls(...)`
  - `render_evaluation(...)`
  - `render_policy_visualization(...)`
- Mission flow:
  - `MISSION_ORDER = ("mission_1", "mission_2", "mission_3")`
  - `mission_context(...)`
  - `mission_check_result(...)`
  - `save_mission_submission(...)`
  - Instructor password defaults to `pendulum-master` unless overridden by Streamlit secrets or `PENDULUM_MASTER_PASSWORD`.

## Student flow

Landing page offers "Start tutorial" or "Skip to activity".

Guided stages:
1. RL concepts mini-game
2. Background: observations/actions/reward function
3. Pendulum intro playground
4. Observation demo
5. Action demo
6. Reward demo
7. Algorithm demo: Q-table vs DQN
8. Lab

Lab flow:
1. Mission banner describes current goal.
2. Sidebar sets algorithm/training episodes/learning speed/exploration/advanced settings. Some missions force algorithm.
3. Students drag observations into the observation box.
4. Students drag action force bubbles into the action box.
5. Students drag reward/math blocks into the reward function.
6. "Train agent" trains Q-learning or DQN, shows replay, learning curve, metrics, and policy map.
7. Mission check evaluates the latest trained model. Passing missions unlocks the next mission and saves explanations/GIF/JSON.

## Mission gates

- Mission 1: forced Q-learning; pass if eval balances at least 100 steps.
- Mission 2: forced DQN; pass if eval balances at least 100 steps and mean absolute cart position is under 25% of half-track.
- Mission 3: ethical exploration enabled/locked; pass if latest settings include `animal_distance` observation and eval balances at least 100 steps.
- Bonus mode unlocks after all missions and includes one-term reward, swing-up, and pole-length challenges.

## Verification done on 2026-07-06

- Worktree was clean before adding this file.
- `rg` is not installed in this environment; use `find`/`grep`.
- Smoke test passed:
  - `.venv/bin/python pendulum_rl_live.py --smoke-test`
  - Q-learning and DQN each ran 4 tiny episodes and passed.
- Streamlit server required sandbox escalation for local socket binding and was started at `http://127.0.0.1:8501`.
- Streamlit `AppTest` ran these stages without exceptions:
  - `rl_concepts`
  - `background`
  - `pendulum_intro`
  - `observation_demo`
  - `action_demo`
  - `reward_demo`
  - `algorithm_demo`
  - `lab`
- AppTest also exercised the lab by setting observations/actions/reward state, clicking "Train agent", and confirming the post-training sections render: Evaluation, Learning curve, What the agent learned, Mission check.
- A very short 20-episode Q-learning test run produced a Q-table and metrics, but it was intentionally too short to pass Mission 1 reliably.
- Headless Chrome screenshots of the live Streamlit server only captured Streamlit's skeleton loader, not the hydrated UI. Treat AppTest as the reliable interaction check from this session.

## Notes / quirks

- The default lab builders start empty for each mission so students must choose observations, actions, and reward blocks.
- `DEFAULT_REWARD_TERMS` is empty; training is blocked with a warning if reward terms are empty.
- Mission submissions currently present in the local `submissions/` directory are ignored by git. The existing local Mission 3 JSON appears stale relative to the current mission gate because it lacks `animal_distance`.
- DQN is CPU-cap-aware for hosted/network sessions; Q-learning is the faster workshop path.
- Demo assets are precomputed in `assets/demo_assets.pkl`; `python pendulum_rl_live.py --precompute` can regenerate them.

## Update later on 2026-07-06

Branch/worktree:
- Working branch: `educational-checkins-local-export`.
- Do not merge to `main` until the user reviews the localhost app.

Changes added:
- Added reusable reflective check-in helpers in `pendulum_rl_live.py`:
  - `reflective_checkin_state_key`
  - `reflective_checkin_response`
  - `render_reflective_checkin`
- Wired reflective questions into:
  - background/design overview
  - pendulum intro
  - completed observation demo
  - completed action demo
  - reward demo/math transition
  - algorithm Q-table/DQN transition
  - Mission 3 ethical observation section
  - evaluation replay
  - policy map view
- Added local-first submission export:
  - `build_mission_submission_payload`
  - `render_submission_markdown`
  - `learning_curve_csv`
  - `build_mission_export_zip`
  - `render_student_identity`
- Mission pass UI now offers `Download submission ZIP` with `submission.json`, `explanation.md`, `learning_curve.csv`, `manifest.json`, and `run.gif` when available.
- Local cloned runs can still save gitignored files to `submissions/<mission>/`.
- Hosted/network sessions warn that Streamlit server-side files are not reliable collection storage and tell students to download/upload the ZIP externally.
- README and Streamlit Cloud notes now explain the ZIP submission workflow.

Verification for this update:
- `.venv/bin/python -m py_compile pendulum_rl_live.py` passed.
- `.venv/bin/python pendulum_rl_live.py --smoke-test` passed.
- Streamlit `AppTest` rendered these stages with no exceptions: `background`, `pendulum_intro`, `observation_demo`, `action_demo`, `reward_demo`, `algorithm_demo`, `lab`.
- Direct ZIP-builder check confirmed expected files: `submission.json`, `explanation.md`, `learning_curve.csv`, `manifest.json`, `run.gif`.

Follow-up after user feedback:
- Reflection cards are now required gates instead of optional prompts.
- `render_reflective_checkin(..., required=True)` shows a completion hint and radio choices no longer auto-select an answer.
- Continue buttons are disabled until required reflections are answered on:
  - `background`
  - `pendulum_intro`
  - completed observation demo
  - completed action demo
  - reward demo
  - algorithm demo
- Lab mission checks are disabled until the replay and policy-map check-ins are answered.
- Mission 3 also requires the ethical-observation reflection before mission check.
- Mission ZIP download/unlock is disabled until all four mission explanation text areas are answered.
- Re-ran `.venv/bin/python -m py_compile pendulum_rl_live.py` and `.venv/bin/python pendulum_rl_live.py --smoke-test`; both passed.
- AppTest confirmed Continue buttons are disabled with blank reflections and enabled when answers are present.

Grid-game connection pass:
- Added `render_grid_game_bridge(...)` and `GRID_GAME_BRIDGE_STYLE` in `pendulum_rl_live.py`.
- Added "Back to the grid game" bridge cards to:
  - Background
  - Pendulum intro
  - Observation demo
  - Action demo
  - Reward demo
  - Q-table vs DQN
  - Lab observation/action controls
  - Mission 3 ethical controls
- Updated explanatory copy to reuse the grid-game Q-learning language:
  - Q-table = the grid-game notebook
  - observations = notebook rows / row keys
  - actions = notebook columns
  - rewards = nudges that raise/lower Q-values
  - learning curve = the grid-game score graph
  - replay/policy map = reading the learned notebook
  - DQN = estimating notebook Q-values without storing every row
- Re-ran `.venv/bin/python -m py_compile pendulum_rl_live.py` and `.venv/bin/python pendulum_rl_live.py --smoke-test`; both passed.
- AppTest rendered `background`, `pendulum_intro`, `observation_demo`, `action_demo`, `reward_demo`, `algorithm_demo`, and `lab` with no exceptions and confirmed one grid-game bridge on each.

## PID/Odometry lab added

New directory:
- `pid_odometry_lab/`

Files:
- `pid_odometry_lab/app.py`: local Streamlit app for open-loop baseline, PID, odometry, and final ZIP export.
- `pid_odometry_lab/sim_core.py`: reusable simulation helpers from worker agent; includes PID controller, first-order/heading plants, differential-drive odometry, encoder conversions, path helpers, and metrics.
- `pid_odometry_lab/README.md`: run/local submission instructions.
- `pid_odometry_lab/LOCAL_ONLY.md`: explains why this lab should not rely on Streamlit Cloud for submission collection.

Run command:

```bash
streamlit run pid_odometry_lab/app.py
```

Flow:
1. Intro check-in comparing PID to the RL pendulum lab.
2. Open-loop baseline: same motor command under normal, low-battery, and high-friction conditions; required check-in before PID.
3. PID control: tune `Kp`, `Ki`, `Kd`, and target; mission requires final error < 0.08 m, overshoot < 0.25 m, settling time < 4.5 s, plus required check-ins.
4. Odometry: tune estimated wheel radius and track width; mission requires final position error < 0.15 m and heading error < 8 deg, plus required check-ins.
5. Final export: required final reflection, then ZIP download.

ZIP export includes:
- `submission.json`
- `explanation.md`
- `baseline_trials.csv`
- `pid_run.csv`
- `odometry_run.csv`
- `baseline_plot.png`
- `pid_plot.png`
- `odometry_plot.png`
- `manifest.json`

Verification:
- `.venv/bin/python -m py_compile pid_odometry_lab/app.py pid_odometry_lab/sim_core.py` passed.
- AppTest rendered `intro`, `baseline`, `pid`, `odometry`, and `export` with no exceptions.
- Manual metric check found achievable mission values: PID passes around `Kp=2.5`, `Ki=0`, `Kd=1.5`; odometry passes around wheel radius `0.051`, track width `0.332`.
- Remove `pid_odometry_lab/__pycache__` after Python verification runs.

## RL pendulum automatic submission pipeline

- Removed the visible activity-GIF uploader and mission ZIP-download workflow.
- Tutorial check-ins, student identity fields, and mission explanations now save
  automatically to `student_submission/autosave/responses.json` and
  `student_submission/autosave/responses.md` on Streamlit reruns. New responses
  are merged with earlier ones and the accumulated record is reloaded after an
  app restart, so Streamlit widget cleanup cannot erase prior-page answers.
- Every completed training run automatically writes its actual policy replay to
  `student_submission/<activity>/run.gif`, along with `latest_run.json` and
  `learning_curve.csv`.
- After a mission check passes, its evaluation GIF, checked settings/metrics,
  learning curve, and explanations are automatically kept current in
  `student_submission/<mission>/`.
- The mission button is now only **Continue to next mission**. It unlocks after
  all four explanation prompts are complete; saving does not depend on clicking it.
- A new training run invalidates the previous mission check, and advancing clears
  the previous mission's policy/replay so stale results cannot appear in the next
  mission.
- Autosave failures are surfaced in the UI instead of being silently reported as
  successful.

Verification for this update:

- `.venv/bin/python -m py_compile pendulum_rl_live.py` passed.
- An isolated temporary-directory test confirmed automatic creation of seven
  expected answer, replay, mission, and learning-curve artifacts without touching
  a student's real submission folder.
- A second test trained a tiny Q-learning policy, rendered its real replay GIF,
  autosaved it, and verified the saved bytes exactly matched the generated replay.
- A navigation/restart test confirmed that answers from an earlier page remain in
  the submission after its widget keys disappear and after a fresh session loads.
- `.venv/bin/python pendulum_rl_live.py --smoke-test` passed for both Q-learning
  and DQN.
