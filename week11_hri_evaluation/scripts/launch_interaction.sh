#!/usr/bin/env bash
# Migration notice only. The previous text-command demo is no longer a lab.
set -e
cat >&2 <<'MESSAGE'
These are older Lab 10 instructions. The /hri/command text demo has been replaced.
Stop the old demo terminal with Ctrl+C. Preserve your student_submission folder.
From your computer's repository terminal, restart the current guide with:
  bash scripts/ros_course.sh lab week11_hri_evaluation
Then, in the virtual desktop, run:
  cd /workspace/week11_hri_evaluation
  bash scripts/launch_handover.sh
Use Refresh ROS checks and the microphone recording check in the guide.
Do not paste terminal output into a preflight field or publish /hri/command.
If the guide still shows those steps, your checkout needs the course update.
MESSAGE
exit 2
