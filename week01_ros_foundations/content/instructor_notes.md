# Instructor notes

## Intended duration

- Introduction and Part 1: 20–25 minutes
- Part 2 architecture activities: 25–30 minutes
- Part 3 ROS concepts and preflight: 20–25 minutes
- Mission 1: 35–45 minutes
- Mission 2: 35–45 minutes
- Mission 3: 50–65 minutes
- Final synthesis and reflection: 25–35 minutes

Students may complete Mission 3 outside the scheduled meeting.

## What is assessed

- Correct ROS graph interpretation
- Explanations of sensor, timing, distribution, and hardware challenges
- Architecture comparison, arbitration, and layered-safety reasoning
- Correct distinction among ROS middleware, nodes, topics, messages, and services
- Predictions recorded before experiments
- Evidence connecting commands to motion
- A safe subscriber-to-publisher behavior
- Tests that cover invalid and missing sensor data
- Individual explanations

Environment installation speed and screenshot aesthetics are not graded.

## Recommended rubric

| Category | Points |
|---|---:|
| Parts 1–3 conceptual foundations | 20 |
| Mission 1 graph and service investigation | 15 |
| Mission 1 architecture explanation | 10 |
| Mission 2 predictions, trials, and timing evidence | 15 |
| Mission 3 implementation | 15 |
| Mission 3 tests and layered-safety analysis | 15 |
| Final synthesis and reflection | 5 |
| Reproducibility and organization | 5 |

## Pilot checks

Before student use:

1. Start from the same clean image students receive.
2. Confirm the TurtleBot3 launch publishes `/scan` and `/odom`.
3. Confirm the graph snapshot contains at least one service and its type.
4. Confirm the guard is the only publisher on `/cmd_vel` during student behaviors.
5. Complete all four motion trials and inspect their timing fields.
6. Implement the starter functions locally and run the behavior evaluator.
7. Confirm an interrupted scan produces a zero command.
8. Complete and inspect `foundations.md`, the ROS system diagram, and the generated submission folder.
