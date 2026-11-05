# Lab 9: Investigating Foundation Models for Robotics

This individual lab combines live local language and vision experiments with model-directed robot skills in a small 2D simulator. Models generate new answers on the student's CPU. No external inference service, API key or model training is used. Initial software and model downloads require internet access. Subsequent generation uses local files.

## Start

You can use the shared course Docker environment. From the repository root in Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\ros_course.ps1 lab week10_foundation_models
```

On macOS/Linux, run `bash scripts/ros_course.sh lab week10_foundation_models`. Open http://localhost:8501. This starts the Python guide without requiring a ROS workspace build. Use the updated launcher in your checkout. An image rebuild is not required for this launcher update.

Alternatively, run locally with Python.

From this folder on Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On macOS/Linux use `python3 -m venv .venv` and `source .venv/bin/activate`, then the same pip and Streamlit commands. The course Docker Python environment can also run the app.

On Preflight select **Prepare local models**, wait for the download to finish, then select **Run preflight**. Preflight actually generates an answer with each model. Installation uses an isolated CPU environment in the user's native cache, leaving ROS dependencies unchanged. Model checkpoints persist under this lab's ignored `runtime/models/` directory. A replacement container may need its isolated Python environment prepared again.

Terminal alternative, from the Lab 9 folder using the guide's Python: `python scripts/setup_local_models.py`. In the course desktop use `/opt/course-venv/bin/python scripts/setup_local_models.py`. Setup and integration tests are verified on Python 3.12 in the Linux course container. CPU runtime and memory should be checked on other hardware before setting class-wide timing expectations.

## Learning sequence

1. Preflight checks Python packages, files, saving, and actual generation with both downloaded local models.
2. Six connected guided activities explain model roles, grounding, demonstrations and embodiment, adaptation, action execution, and validation. Concrete examples, labeled scene regions, visual comparisons and executable experiments connect each concept to the missions. Tutorials do not require written submissions.
3. Mission 1 generates all three supplied robot-request answers, displays them together, then unlocks a required student-written improved request and its generated answer. Students finish with one analysis question.
4. Mission 2 follows the same sequence using one multi-object workbench photograph and three different questions about identification, location and task choice. The exact photograph stays fixed for the student's improved question.
5. Mission 3 compares three prompts on the same 13 by 9 warehouse maze. The model chooses UP, DOWN, LEFT, RIGHT or STOP one step at a time. Automatic checks block walls and restrict the following choice to a free neighboring direction or STOP. Students write and run a fourth prompt, compare paths and endings, then answer one question. Every run starts from the same map and position.
6. One technical synthesis integrates the missions. The separate individual reflection uses the standard course prompts and 1 to 300 word limit.

## Evidence provenance

- Mission 1 uses `HuggingFaceTB/SmolLM2-360M-Instruct`. Mission 2 uses `HuggingFaceTB/SmolVLM-500M-Instruct`. Exact revisions are pinned in `lab/local_config.py`, and both model cards specify Apache 2.0 licensing.
- Every mission run generates a new response from local weights. The same prompts can produce the same answer because decoding is greedy. Model weights stay frozen.
- Mission 3 uses the same language checkpoint as Mission 1 with a directional command grammar. The model receives the full text map, coordinates, object locations, neighboring-cell status and recent actions. The grammar controls format, not which move is correct. No planner selects or repairs model moves.
- The two missions use different models and tasks. Their results are not a controlled comparison isolating the effect of adding images.
- References and guided examples are authored teaching materials. They are not presented as model outputs. The vision model receives the chosen image and student question, not the reference answer.
- The directional grid simulator executes locally. Its state transitions are ordinary Python, not a learned VLA controller.
- Every Mission 3 action stores the exact model input, raw output, movement check and before/after coordinates. Every run lasts 50 steps. A blocked move or STOP holds the position for one step, then generation continues. Goal visits are recorded without ending the run. These are simulated outcomes, not physical navigation or safety results.
- Numerical action decoding and controlled condition traces are synthetic instructional exercises, not learned policy rollouts.
- The guided model-role activity includes one authentic author-published OpenVLA clip. See [attribution and limitations](assets/policy_recordings/README.md).
- Videos do not include raw actions or inference timing. The lab does not invent those measurements or claim its selected videos form a controlled benchmark.

## Saving and recovery

Responses and major controls autosave atomically when edits are applied. Press Ctrl+Enter or click outside a text field to apply an edit. Navigation synchronizes pending widget values before saving. Each generated result retains its prompt, raw response, model revision, decoding settings and duration. Vision attempts include a copy and SHA-256 hash of the exact input image. Check and save retains the selected experiment history and explanation. New runs or edited analysis make completion out of date. Replacing a checked run archives its previous snapshot. Downstream completion depends on the exact upstream run.

Restarting restores answers and evidence, then requests a fresh preflight before resuming. The sidebar cannot bypass preflight or the six guided activities. Prior-version submissions are preserved and old answers are loaded where available, but they are not silently marked complete under new requirements.

Finalization writes one complete ZIP and a SHA-256 manifest. Inspect the files, keep a backup, commit and push `week10_foundation_models/student_submission/`, then submit the commit link. Student evidence is not gitignored.

Cancelled, empty or failed generations do not satisfy trial requirements. Incorrect but successfully generated answers do count, since evaluating their limitations is part of the experiment. The UI shows progress and permits cancellation. Loaded models stay available in local worker processes until idle shutdown.

## Maintainer verification

```bash
python app.py --smoke-test
python -m unittest discover -s tests -v
# Use the isolated model Python printed by setup for this real inference check:
python scripts/check_local_inference.py
python scripts/check_robot_inference.py
```

App tests use isolated temporary submission folders. They do not populate or clear student work. `LAB9_SUBMISSION_DIR` can select an isolated location for manual QA. Do not commit instructor solutions or test responses.
