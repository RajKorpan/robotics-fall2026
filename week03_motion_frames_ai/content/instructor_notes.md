# Instructor notes

## Intended duration

- Motion-model introduction: 15 minutes
- Mission 1: 35–45 minutes
- Mission 2: 35–45 minutes
- Mission 3: 60–90 minutes, with outside-class completion expected
- Final synthesis: 10 minutes

## Assessment priorities

- Numerical predictions are made before execution.
- Students distinguish model error from pose-estimation or measurement error.
- Frame answers include both coordinates and frame IDs.
- The original AI output remains intact.
- Tests expose at least one weakness or unsupported assumption.
- The final node stops after normal completion and interruption.
- Students explain what their tests do and do not establish.

## Suggested rubric

| Category | Points |
|---|---:|
| Mission 1 predictions and calculations | 15 |
| Mission 1 execution and discrepancy analysis | 15 |
| Mission 2 TF and transformation reasoning | 20 |
| Original AI interaction and review | 10 |
| Tests and expected/actual evidence | 15 |
| Final ROS pattern and safety | 15 |
| Correctness argument and limitations | 5 |
| Reproducibility and submission quality | 5 |

## Pilot checks

1. Verify `base_scan` is the TurtleBot3 LiDAR frame.
2. Run all three motion sequences from a reset pose.
3. Confirm `frame_probe` works before and after moving the robot.
4. Complete one reference implementation for every assigned pattern.
5. Interrupt a pattern node and confirm a zero command is published.
6. Confirm the AI lock cannot be overwritten through ordinary app use.
7. Inspect a final submission from a clean clone.

