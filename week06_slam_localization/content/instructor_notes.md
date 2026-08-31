# Instructor notes — Week 6

## Intent and scope

This 3–3.5 hour individual lab teaches students to operate, inspect, and evaluate SLAM/localization systems. It deliberately avoids implementing scan matching, graph optimization, or particle filtering. The intellectual work is experimental design and interpretation: students must distinguish map appearance from map quality and a displayed pose from warranted confidence.

## Suggested timing

| Activity | Time |
|---|---:|
| Concepts and preflight | 25–30 min |
| Mission 1 mapping | 45–55 min |
| Mission 2 controlled strategy comparison | 45–55 min |
| Mission 3 localization trials | 60–75 min |
| Synthesis and artifact review | 20 min |

## Experimental controls

Mapping comparisons are only meaningful when the world, robot, approximate duration, map resolution, and software configuration remain fixed. Require a simulator/SLAM restart between runs. The route strategy should be the main changed variable. The analyzer reports known fraction, occupied/free fractions, small occupied speckles, border contact, component count, and a transparent composite quality score. The score is a discussion scaffold—not ground truth and not a replacement for visual inspection.

Students should not claim loop closure merely because the map grew. Stronger evidence includes revisiting a known area followed by a visible correction to earlier walls or trajectory, reduced duplicate structures, or a pose-graph response observed through appropriate diagnostics. Accept a well-supported conclusion that evidence was insufficient.

For localization, AMCL covariance represents the algorithm’s modeled uncertainty, not guaranteed physical error. Reward students who explicitly separate covariance, consistency, recovery, and ground truth. An apparently confident but incorrect estimate is the key failure mode.

## Degraded-scan condition

The supplied `scan_degrader` retains approximately 50% of scans and adds Gaussian range noise before publishing `/scan_degraded`. The localization wrapper remaps AMCL’s `/scan` input inside the Navigation2 launch group while leaving the original scan visible to the recorder. This is a pedagogical perturbation, not a calibrated physical sensor model.

## Assessment suggestion (100 points)

- Mission 1 map construction, system observation, and map interpretation: 25
- Mission 2 controlled comparison and loop-closure reasoning: 25
- Mission 3 four trials, quantitative interpretation, and safe fallback: 35
- Final synthesis: 10
- Complete, reproducible artifacts: 5

Automated gates check minimum evidence. Manually assess whether metrics are interpreted correctly, whether the strategy comparison controls confounds, whether screenshots support claims, and whether limitations identify affected stakeholders.

## Common problems

- **No map appears:** verify `/scan`, `/odom`, TF, simulated time, and the SLAM lifecycle state.
- **Map saver times out:** confirm `/map` is publishing and wait for lifecycle activation.
- **AMCL never converges:** check that the saved map matches the world, set an initial pose, drive through distinctive geometry, and verify scan/map frame alignment.
- **Degraded scan is not counted:** confirm both `/scan` and `/scan_degraded` publish and that degraded mode was selected.
- **Cross-talk between students:** assign unique `ROS_DOMAIN_ID` values.

## Accessibility and recovery

Plots and screenshots are supported by numeric JSON evidence and written prompts; grading must not depend on color alone. If a run crashes, preserve the existing `student_submission/` directory and rerun only the missing condition. Evidence is deterministic in format but necessarily differs across student driving behavior.
