# Current live model missions

All three missions follow the same flow: generate three supplied examples, compare their outputs, write and run a fourth prompt, explain a specific result, then Check and save. Later parts remain hidden until the earlier experiments finish. Model correctness is not a completion requirement.

Mission 1 uses SmolLM2 with one capability card and three robot requests. Mission 2 uses SmolVLM with one workbench photograph and three questions. M1 retains its existing final question. M2 asks whether the student's improved question produced a better-supported or more useful answer.

Mission 3 uses SmolLM2 on a fixed maze with alternating wall openings. Each run starts at (1,7) and aims for (11,1). The model gets the full ASCII map, current coordinates, goal, labeled objects, free/blocked neighbors and recent actions. The student prompt remains fixed while state updates after each action. Generation permits only UP, DOWN, LEFT, RIGHT or STOP, including normal casing variants. The model chooses the direction. Python checks and executes a single-cell transition. No computed route or recommended action is passed to the model.

One run button replaces the separate ask/check sequence. Live progress shows position, path and current step. Every run lasts 50 steps. Wall collisions and STOP hold the position for one step. Feedback is supplied before the next decision. After a blocked move, the next command menu permits only free neighboring directions or STOP. This local constraint does not select a route. Goal visits are recorded without ending the run. All three supplied prompts must finish before the required own-prompt experiment appears. Completion requires that fourth run and an explanation, even if it fails.

## Local execution

Pinned model revisions and isolated CPU dependencies are configured in `lab/local_config.py` and `requirements-models.txt`. Prepare the models through Preflight. Initial setup downloads public weights and software. Later inference uses local files and offline flags. Workers retain loaded weights until idle shutdown. Every requested run generates again rather than substituting a prior answer.

## Evidence

Records preserve prompts, pinned model revisions, raw answers, generation settings and timing. Vision records include exact image bytes and hashes. Robot records include every exact state sent to the model and every automatically checked transition. Readiness replays the movement records and verifies saved receipts. New prompts, runs or analysis invalidate current completion while previous checked evidence remains available.

Use temporary `LAB9_SUBMISSION_DIR` folders for QA. Explicit fixtures support UI tests. The two inference-check scripts separately exercise actual downloaded weights. They are not student answers or required outcomes.
