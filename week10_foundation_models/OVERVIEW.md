# Lab 9 overview

Six connected guided activities introduce model roles, scene grounding, demonstrations, embodiment, adaptation, action interfaces and validation.

Mission 1 runs three supplied robot requests through a real local language model. All three answers remain visible for comparison. Only then do students write their own improved request, generate its answer and explain one difference using the robot capability card.

Mission 2 repeats that structure on one multi-object workbench photograph. Three questions ask the vision-language model to identify a tool, describe a spatial relationship and choose a tool for an underspecified task. Students then choose one of those tasks, state its goal in a new request and compare the new answer with the original answer for that same task. The decision task supplies a concrete job, marking a circle on a wooden workpiece, so the revised request can address the original missing information.

Mission 3 gives the local language model a 13 by 9 maze, current coordinates, a goal, object locations, neighboring-cell status and recent actions. Three supplied prompts attempt the same route using only UP, DOWN, LEFT, RIGHT and STOP. Every model action is automatically checked and simulated. Runs last 50 steps. A blocked move or STOP holds the robot in place for one step, then the model chooses again. Goal visits are recorded without ending the run. Students compare paths and endings, write a required fourth prompt and test it from the same starting position. No planner chooses or repairs the model's moves.

Each mission ends with one short analysis question. Incorrect answers and unsuccessful robot runs count as experiments. The final technical synthesis connects all three missions. The separate individual reflection uses the shared course prompts. Exact inputs, model outputs and simulator states are saved with restart recovery, a complete ZIP and a hash manifest.
