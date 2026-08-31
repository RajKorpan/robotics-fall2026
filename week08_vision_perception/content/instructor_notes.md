# Instructor notes — Week 8

## Design intent

This 3-hour individual lab compares inspectable rules with frozen learned perception. Students do not train a substantial model. The central learning target is the boundary between apparent competence and reliable perception, followed by the engineering responsibility to contain failures before they become unsafe motion.

## Suggested timing

| Activity | Time |
|---|---:|
| Concepts and preflight | 25 min |
| Mission 1: classical perception | 50 min |
| Mission 2: learned perception | 55 min |
| Mission 3: behavior integration | 40 min |
| Synthesis and artifact check | 20 min |

## Condition controls

The condition dimensions are lighting, glare, distance, occlusion, orientation, clutter, and a distractor. Mission 1 uses generated images so every student sees the same ground truth. Students tune on the normal condition, lock parameters, and then evaluate the complete bank. Do not permit condition-specific retuning because it destroys the comparison.

Mission 2 should use the same dimensions but a target class supported by the frozen model. Collect detections once at a permissive threshold and perform threshold selection offline. This prevents repeated camera/model variation from being mistaken for a threshold effect.

## Learned model release checklist

- Freeze one exact ONNX file and labels file.
- Verify that output layout matches the supplied Ultralytics-style parser.
- Record source, license, version, input size, checksum, and expected classes.
- Preload it in the course image.
- Provide a recorded evidence run for students whose live pipeline fails.
- Test CPU latency on the slowest supported machine.
- Do not grade raw accuracy if the environment differs; grade experimental completeness and correct interpretation.

## Safety architecture

Detector-only launch mode is the default. Motion behavior requires `enable_behavior:=true`. The behavior node stops on stale observations and never approaches at low confidence. The command guard independently enforces low linear/angular limits and a command timeout. All motion testing is simulation-only for this lab.

## Assessment suggestion (100 points)

- Classical pipeline, controlled evaluation, and failure analysis: 25
- Learned detector threshold evaluation and comparison: 25
- ROS integration, behavior states, and safety evidence: 30
- Final synthesis: 15
- Reproducible artifacts and organization: 5

Automated gates check evidence presence, condition coverage, minimum classical performance, learned threshold sweep, and behavior invariants. Manually assess whether students distinguish heuristic scores from learned confidence, avoid interpreting confidence as safety probability, and explain how environmental failures propagate or are contained.

## Privacy and accessibility

Use objects rather than people as targets. Students should use the supplied condition bank, simulator, or consenting images and must not submit identifiable bystander imagery. All image-based evidence must also be summarized numerically and textually; grading must not depend on color perception alone.

## Common problems

- **No images:** inspect topic name, encoding, QoS, and whether the publisher is running.
- **No mask detections:** inspect HSV values and value/saturation loss under dim light or glare.
- **Learned node exits:** verify model and labels paths and the ONNX output format.
- **Unexpected model classes:** confirm the frozen label ordering matches the exported model.
- **Robot does not move:** confirm behavior was explicitly enabled and observations are fresh/reliable.
- **Robot moves unexpectedly:** terminate the launch; verify target observations and keep behavior disabled during perception-only missions.

## Calibration before release

Run at least three classical parameter sets across the generated bank. The passing floor should be achievable without eliminating the distractor challenge. Run the frozen model across the full learned condition set and confirm that several threshold choices are defensible. Verify every default behavior scenario passes and create failing fixtures for stale, low-confidence, uncentered, and close-target logic.
