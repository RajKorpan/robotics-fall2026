# Instructor notes

## Intended duration

- Introduction and preflight: 15 minutes
- Mission 1: 30–35 minutes
- Mission 2: 30–35 minutes
- Mission 3: 45–60 minutes
- Final synthesis: 10 minutes

Students may complete Mission 3 outside the scheduled meeting.

## What is assessed

- Correct ROS graph interpretation
- Predictions recorded before experiments
- Evidence connecting commands to motion
- A safe subscriber-to-publisher behavior
- Tests that cover invalid and missing sensor data
- Individual explanations

Environment installation speed and screenshot aesthetics are not graded.

## Recommended rubric

| Category | Points |
|---|---:|
| Mission 1 graph investigation | 20 |
| Mission 1 system explanation | 10 |
| Mission 2 predictions and trials | 15 |
| Mission 2 evidence and comparison | 10 |
| Mission 3 implementation | 20 |
| Mission 3 tests and safety | 15 |
| Final synthesis and reflection | 5 |
| Reproducibility and organization | 5 |

## Pilot checks

Before student use:

1. Start from the same clean image students receive.
2. Confirm the TurtleBot3 launch publishes `/scan` and `/odom`.
3. Confirm the guard is the only publisher on `/cmd_vel` during student behaviors.
4. Complete all four motion trials.
5. Implement the starter functions locally and run the behavior evaluator.
6. Confirm an interrupted scan produces a zero command.
7. Complete and inspect the generated submission folder.

