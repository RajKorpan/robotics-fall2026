# Lab 10 · Voice, Shared Control, and Assistive Handover

Work individually with a TurtleBot3 in Gazebo. Build its interaction controller in the guide, give spoken requests through your microphone, and compare manual teleoperation, voice shared autonomy, and supplied autonomous execution.

## Start

From the course repository on Windows, run the usual launcher.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\ros_course.ps1 lab week11_hri_evaluation
```

On macOS or Linux, run the following command.

```bash
bash scripts/ros_course.sh lab week11_hri_evaluation
```

The launcher builds the Lab 10 ROS package and prepares the local speech recognizer. The first speech-package installation needs an internet connection. Open the guide at **http://localhost:8501** in your computer's browser and the virtual desktop at **http://localhost:6080/vnc.html?autoconnect=1&resize=remote**. Use the microphone recorder in your computer's browser and allow microphone access.

For initial Docker setup and rebuilding the image, see [the shared ROS setup](../ROS_DOCKER_SETUP.md).

On the preflight page, launch the world in Terminal 1 of the virtual desktop.

```bash
cd /workspace/week11_hri_evaluation
bash scripts/launch_handover.sh
```

Keep Terminal 1 running. Gazebo opens the cup delivery room with a green person station, red and blue cup stations, and a yellow correction checkpoint. Refresh the guide's ROS checks. It must receive fresh odometry from the world. Record the example phrase, play the clip, and check its transcript.

If the microphone recorder cannot start, allow access in the browser site settings and operating system privacy settings. Quiet or silent playback usually means the wrong microphone is selected. A clear clip with no recognized phrase means the decoder could not match its limited English vocabulary. Try the short example phrase. Recognition runs in the course container. The browser sends microphone recordings to that local guide.

### Troubleshooting an older guide or rebuild

The current preflight checks Gazebo, ROS, saving, and a microphone recording. It has no terminal-output field. If your instructions say `launch_interaction.sh`, publish `/hri/command`, or paste preflight output, you are viewing the previous version. Preserve `student_submission`, update your course checkout using the course's fork-update instructions, close the old demo terminal with Ctrl+C, and restart the guide with the course launcher above. Do not reset or delete your work.

`Waiting for at least 1 matching subscription` means a topic publisher has not found a compatible receiving node. Manual topic publication is not part of the current preflight. Launch `launch_handover.sh` and use the guide's ROS checks. The troubleshooting expander provides commands for checking the controller and selecting domain 31 consistently.

PocketSphinx 5.0.4 can fail when compiled inside the Linux ARM64 container used on Apple Silicon Macs. The updated dependencies use 5.1.0 and validate the actual course decoder. After updating, rebuild the image from your computer's repository terminal with `bash scripts/ros_course.sh setup`, then start the lab. Source compilation can take several minutes on the first build. Builds use two CMake jobs to limit memory pressure. Installing PocketSphinx on the host Mac does not update the container. A failed dependency build does not erase your submission folder.

## Four guided activities

1. Follow intended speech through transcription, parsing, clarification, and confirmation. Compare visible cup choices and the selected interaction phase.
2. Step through fetching, offering, and transferring in a teaching diagram. Compare early readiness, readiness during an offer, timeout, and cancellation. Read the event trace to see which rule permitted or prevented transfer.
3. Edit the starter Python directly in the guide. Save the corrected readiness guard, rerun the checks, and compare the expected and observed transitions.
4. Redirect the same task in each control mode. Inspect who changes the goal, who chooses the movement, and when a fresh confirmation is required.

## Missions

**Mission 1** completes the interaction controller in the guide. Check its rules in three groups, then run the full scripted suite. Test the saved source on the Gazebo robot and retain a ROS trial before saving the mission.

**Mission 2** runs four microphone trials with the actual robot. Try a clear request, an ambiguous request followed by a named cup, a correction, and a cancellation. The guide records intended words, recognized text, ROS events, odometry poses, and the observed result. Review spoken Confirm and Ready before applying them. Redesign feedback from one observed problem and repeat the matching trial.

**Mission 3** compares normal and changed-goal deliveries in manual, shared, and autonomous control. All six trials use the same room, initial position, checkpoint, readiness rule, and Stop control.

Before each fresh trial, finish or archive the old attempt and reset the world in Terminal 2.

```bash
cd /workspace/week11_hri_evaluation
bash scripts/reset_handover.sh
```

For manual control, open Terminal 3 and run the keyboard controller.

```bash
cd /workspace/week11_hri_evaluation
bash scripts/manual_control.sh
```

Focus Terminal 3 and use W/S/A/D to drive or turn. Hold the key for repeated short commands. Space stops and Q exits. Keep the guide visible and open. Dock at the colored pad, then use the guide to load the cup. Return to the green pad, offer the cup, and signal readiness. The guide and Gazebo controller stop motion when commands, the guide heartbeat, or odometry become stale.

The mobile robot uses a simulated tray state for cup loading and transfer. Navigation is executed by Gazebo physics and measured through ROS odometry. Students implement the interaction rules that authorize movement and transfer.

## Save and submit

Submitted commands and robot observations save automatically. Reopening the guide requires a fresh microphone and ROS check. If the ROS trial was lost because the world or controller restarted, archive the disconnected attempt and collect a new trial. Resetting Gazebo during a trial invalidates that attempt.

Use Download draft backup to retain unfinished work and archived runs. Review the final readiness table, complete the technical synthesis and separate course reflection, then save and download the complete submission. Inspect the saved source, scripted checks, ROS trial evidence, transcripts, feedback redesign, and mode comparisons. Commit and push the submission folder to your fork and submit the commit link.

[Detailed outline](OUTLINE.md)
