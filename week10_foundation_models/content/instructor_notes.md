# Instructor notes

Each mission requires three original prompt runs followed by one student-written prompt run and one short analysis. In Missions 1 and 2, original answers remain visible together. Mission 3 compares complete directional robot runs from the same initial maze. Prompt changes are explicit and required. No accuracy threshold gates completion.

M1 uses a fixed robot capability card. M2 uses one multi-object workbench image with identification, spatial and underspecified task-choice questions. M3 gives the language model the full text map and state but no planned route. Only UP, DOWN, LEFT, RIGHT and STOP are allowed. Checks execute one cell at a time and block walls. Each run continues for 50 steps. STOP is a one-step pause. Blocked moves receive feedback and a free-direction-or-STOP menu for the next step. Reaching the goal is recorded but does not end the experiment. The robot is a simple local grid simulation, not a physical safety or learned-policy benchmark.

Six guided activities remain connected to these experiments and require no written answers. References and recorded demonstrations are labeled separately from live model output. The final synthesis integrates the missions. The reflection uses the exact shared course prompts.

Keep model revisions fixed for the class. Download once and generate offline with the isolated CPU environment. Incorrect answers are often useful evidence. Students should distinguish observed improvements from general reliability claims.

The guide saves exact prompts, outputs, images and simulator transitions. Use `LAB9_SUBMISSION_DIR` for isolated tests. Preserve instructor testing data before resetting the normal test directory. Never clear actual student submissions. Use the unit/UI suite for workflow and evidence checks and the inference scripts for real model behavior.
