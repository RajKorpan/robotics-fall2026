# Lab 9 verification

## Current scope

Three supplied prompts followed by a required own-prompt experiment in each mission. M1 and M2 retain all three original outputs visibly before unlocking the improved-request section. M2 uses the fixed multi-object workbench photograph. M3 uses a 13 by 9 maze with only UP, DOWN, LEFT, RIGHT and STOP. Automatic movement checks replace the separate ask/check interface.

## Automated checks

On November 5, 2026, all 43 tests and the app smoke test passed inside the course Linux container. Run `python -m unittest discover -s tests -q` and `python app.py --smoke-test` from this folder.

Tests cover progressive reveal after zero, one, two, three and four completed answers, required custom prompts, raw outputs, image hashes, cancellation and errors, navigation gates, restart recovery, history, current evidence signatures, finalization and ZIP manifest hashes. Robot tests cover directional movement, wall and boundary blocking with subsequent recovery, single-step STOP, continuation after goal arrival, exact termination at step 50, sticky goal-visit records, stale proposals, a feasible 28-move maze route, deterministic replay, tampered steps and automatic receipts. Test fixtures are explicitly labeled and do not constitute actual model results.

## Actual inference

Both inference-check scripts ran with downloaded pinned weights on CPU and Hugging Face networking disabled. The language/vision script completed eight actual generations. The new image elicited a tool-identification error, a correct right-side spatial relationship, and an unsupported tool-selection claim. The student-written question also produced an erroneous relation. These examples demonstrate why the lab does not gate completion on accuracy or assume a revised prompt always helps.

The updated directional integration check completed all four actual 50-step runs, covering three supplied prompts and one custom prompt. All four records passed the current completion and replay checks. Every proposal is generated from the actual local model with updated state and last-action feedback. Blocked actions restrict the next choice to a free neighboring direction or STOP. The model still chooses among those commands. A STOP action holds position for that step. Goal arrival does not end the run. No scripted route or authored response replaces model actions. Directional decoding permits ordinary casing variants such as Right.


Warm language and vision answers in this check took roughly 1 to 2 seconds, with additional time for model loading. These observations are not performance guarantees for student hardware.

## Manual QA

Use an isolated `LAB9_SUBMISSION_DIR` under `runtime/`. The ordinary instructor-test submission directory stays separate. Before the 50-step transition update, browser QA at 1280 by 720 completed actual preflight generation, all three original requests plus a custom request in each mission, all three Check and save actions, and navigation to synthesis. Those saved real-model records passed the then-current readiness checks for all three missions. New 50-step records use a new simulator contract. Progressive reveal and the maze input explanation were inspected on the pages. The automated full student workflow separately verifies finalization and restart recovery.

Student submissions contain exact inputs, outputs and states, not model weights. All instructor QA records are kept in ignored runtime folders. Restart the normal launcher with a fresh instructor submission directory after testing.
