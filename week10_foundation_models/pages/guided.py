"""Six connected activities with concrete examples and observable experiments."""
import copy
import json
import math

from lab.evidence import ROOT
from lab.guidance_config import GUIDED_COUNT, GUIDED_TITLES
from lab.navigation import jump
from pages.guided_visuals import cup_regions, robot_timeline, robot_pair, weights_diagram, execution_result_svg, svg
from pages.workflow import trajectory_svg
from simulation.guided_examples import region_matches, demonstration_records, decoded_movement, chunk_trial, decision_walkthrough, audio_envelope
from simulation.guided_validation import CASES, STATE, execute

TITLES = GUIDED_TITLES


def render(st):
    step = min(GUIDED_COUNT - 1, max(0, st.session_state.get("tutorial_step", 0)))
    st.title(f"Guided learning {step + 1}/{GUIDED_COUNT}: {TITLES[step]}")
    ACTIVITIES[step](st)
    seen = set(st.session_state.get("guided_seen", []))
    st.divider()
    left, right = st.columns(2)
    if left.button("Back to preflight" if step == 0 else "Back: " + TITLES[step - 1], width="stretch"):
        if step:
            st.session_state["tutorial_step"] = step - 1
            jump(st, "guided")
        else:
            jump(st, "preflight")
    if right.button("Next: " + (TITLES[step + 1] if step + 1 < GUIDED_COUNT else "Mission 1"), type="primary", width="stretch"):
        seen.add(step)
        st.session_state["guided_seen"] = sorted(seen)
        st.session_state["tutorial_reviewed"] = len(seen)
        if step + 1 < GUIDED_COUNT:
            st.session_state["tutorial_step"] = step + 1
            jump(st, "guided")
        else:
            jump(st, "mission_1")


def model_roles(st):
    st.write("**Purpose:** recognize the different information a model can provide to a robot. Read the concrete input and output examples together, then compare which outputs describe, predict or command something.")
    st.write("A modality is a kind of information, such as text, images or sound. A foundation model learns reusable patterns from a large training collection. Its inputs and outputs determine the role it can play in a robot system.")
    st.image(cup_regions(), width=600)
    st.caption("Shared scene for the examples: a blue cup on the left, a red cup on the right, and a shelf beneath them.")
    llm, vlm, vla = st.columns(3)
    llm.subheader("LLM: language")
    llm.caption("Large language model")
    llm.write("**Input:** text requesting a task.")
    llm.code('Inspect the shelf, then report what you found.', language="text")
    llm.write("**Example output:** a symbolic plan.")
    llm.code('inspect("shelf")\nreport("inspection result")', language="python")
    llm.write("The output names actions. A separate skill program must decide whether and how to execute them.")
    vlm.subheader("VLM: vision + language")
    vlm.caption("Vision-language model")
    vlm.write("**Input:** the scene above and a question.")
    vlm.code('Which cup is blue, and where is it?', language="text")
    vlm.write("**Example output:** a visual interpretation.")
    vlm.code('The blue cup is on the left.\nA red cup is on the right.', language="text")
    vlm.write("This links a description to visible evidence. It does not supply the cup's physical distance or a grasp command.")
    vla.subheader("VLA: vision + language + action")
    vla.caption("Vision-language-action policy")
    vla.write("**Input:** a camera view and a task, such as putting the blue cup on a plate.")
    vla.write("**Example output:** a sequence of robot movements. In the recording, the arm approaches the cup and tries again after the first contact.")
    vla.video(str(ROOT / "assets" / "policy_recordings" / "cup_reattempt.mp4"))
    vla.caption("Recorded OpenVLA policy demonstration. Kim, Pertsch, Karamcheti and collaborators, CC BY-SA 4.0. Numerical controls are not supplied with this clip.")
    st.subheader("Other model roles in the same robot system")
    audio, spatial, world = st.columns(3)
    audio.markdown("**Audio / speech model**")
    audio.write("**Input example:** a microphone records a person saying Stop the robot.")
    audio.audio(str(ROOT / "assets" / "guided" / "stop_robot.wav"), format="audio/wav")
    audio.caption("Play the supplied synthesized speech sample. Its expected transcript is shown below. Speech recognition is not run on this page.")
    duration, peaks = audio_envelope(ROOT / "assets" / "guided" / "stop_robot.wav")
    waveform = ' '.join(f'{15+i/max(1,len(peaks)-1)*240:.1f},{110-65*value:.1f}' for i, value in enumerate(peaks))
    audio.image(svg(f'<text x="15" y="30">Amplitude over {duration:.1f} s</text><polyline points="{waveform}" fill="none" stroke="#2563eb" stroke-width="2"/>', 270, 145), width="stretch")
    audio.write("**Output example:** transcript: 'Stop the robot.' The system must still establish who spoke and whether the instruction is authorized.")
    spatial.markdown("**Spatial / 3D model**")
    spatial.write("**Input example:** depth or 3D points from a camera.")
    dots = ''.join(f'<circle cx="{60+(i%5)*26}" cy="{55+(i//5)*17}" r="4" fill="#2563eb"/>' for i in range(20))
    spatial.image(svg('<text x="20" y="30">Depth points on a cup</text>' + dots, 270, 145), width="stretch")
    spatial.write("**Output example:** cup center at (0.12, 0.00, 1.20) m in the camera frame. A camera-to-robot transform is needed before movement.")
    world.markdown("**World model**")
    world.write("**Input example:** the current scene and a candidate action to move the cup toward a plate.")
    world.image(svg('<text x="12" y="30">Now</text><text x="160" y="30">Predicted next</text><rect x="25" y="65" width="40" height="50" fill="#2563eb"/><path d="M80 85 H145" stroke="#64748b" stroke-width="3"/><ellipse cx="208" cy="118" rx="43" ry="10" fill="#eabf54"/><rect x="190" y="65" width="40" height="50" fill="#2563eb"/>', 270, 145), width="stretch")
    world.write("**Output example:** a predicted image with the cup over the plate. It predicts a possible future, rather than proving that the cup moved.")
    st.caption("The text, depth and future-image examples are worked illustrations. The audio is synthesized speech, with an amplitude plot computed from that file. The VLA video is an actual author-published recording. Source: https://openvla.github.io/")
    st.info("Compare the output types: a plan, an image description, motor behavior, a transcript, spatial coordinates and a predicted future are useful in different ways. A robot may combine several of them.")


def grounding(st):
    st.write("**Purpose:** see how an instruction refers to objects in an image, and why adding an image does not resolve every ambiguous request. You will keep the scene fixed and change only the instruction.")
    st.write("A model receives context, meaning the information supplied for one prediction. Text is encoded as tokens, which are small pieces of text. Image patches are encoded into visual features. Attention is a learned mechanism for combining these representations in context.")
    instruction = st.radio("Choose the instruction supplied with this same image", ["Point to the blue cup", "Point to the red cup", "Point to the cup"], key="control_ground_instruction")
    selected = region_matches(instruction)
    a, b = st.columns([3, 2])
    a.image(cup_regions(selected), width="stretch")
    a.caption("Solid thick outlines mark candidate regions matching the instruction. Dashed outlines mark the other labeled regions.")
    b.markdown("**How to read the regions**")
    b.write("A contains the blue cup. B contains the red cup. C marks the shelf/background. These labels refer to the boxes drawn on the image.")
    b.table([{"Region": "A: blue cup", "Matches this instruction": "Yes" if "A" in selected else "No"}, {"Region": "B: red cup", "Matches this instruction": "Yes" if "B" in selected else "No"}, {"Region": "C: shelf/background", "Matches this instruction": "No cup here"}])
    if len(selected) == 2:
        st.warning("Both A and B match the word cup. Seeing both cups does not tell the robot which one the user intended. A useful next response is: Which cup do you mean?")
    else:
        st.success(f"Region {selected[0]} matches the specified color. This resolves the visible color reference, but does not establish ownership, reachability or grasp capability.")
    st.write("**Try this:** select the blue-cup instruction, then the red-cup instruction. Notice that the words change which region matches while the scene stays the same. Finally choose Point to the cup and inspect the two remaining candidates.")
    st.write("The highlighting uses an explicit teaching rule based on the named color. A neural model's attention is learned and need not follow that rule. There is no measured attention score or correctness probability in this illustration. The point is to connect words to visible evidence and to recognize what information is still missing.")


def demonstrations(st):
    st.write("**Purpose:** follow how observations and commands are paired in robot training data, then see why a demonstration from one robot cannot simply be copied to another.")
    st.write("A demonstration is a time-ordered record of observations and actions. In teleoperation, a person drives the robot while the system records those pairs. The instruction describes the intended task. A final photograph alone would not show the commands and feedback that led there.")
    rows = demonstration_records()
    index = min(3, st.session_state.get("control_demo_step", 0))
    row = rows[index]
    st.markdown("**Worked demonstration: approach a shelf, then stop**")
    st.write("The robot starts at x = 0 m. The shelf is at x = 0.6 m. Each forward command lasts one second. The record below is a small synthetic example with explicit units.")
    st.table(rows)
    previous, label, following = st.columns([1, 2, 1])
    if previous.button("Previous snapshot", disabled=index == 0):
        st.session_state["control_demo_step"] = index - 1
        st.rerun()
    label.markdown(f"**Snapshot {index + 1} of 4, time {row['Time (s)']} s**")
    if following.button("Next snapshot", disabled=index == 3):
        st.session_state["control_demo_step"] = index + 1
        st.rerun()
    a, b = st.columns([3, 2])
    a.image(robot_timeline(index), width="stretch")
    b.write(f"**Observe:** robot at x = {row['Observed x (m)']:.1f} m, {row['Observation']}.")
    b.write(f"**Command:** {row['Action']} at {row['Forward command (m/s)']:.1f} m/s for one second.")
    b.write(f"**Feedback:** robot is now at x = {row['Resulting x (m)']:.1f} m.")
    b.write(f"Calculation: {row['Observed x (m)']:.1f} + {row['Forward command (m/s)']:.1f} Ãƒâ€” 1 = {row['Resulting x (m)']:.1f} m.")
    st.write("**Try this:** go through the four snapshots. The resulting position in one row becomes the observed position in the next. At the shelf, the command changes to zero. The training record needs this alignment between observations, commands and time.")
    st.subheader("The same task on different robots")
    st.write("Embodiment means the robot's body, sensors and control interface. Consider the task Move the blue cup from the shelf to the desk. Both robots can receive the same instruction and camera image, but their capabilities and action values differ.")
    st.image(robot_pair(), width=600)
    base, arm = st.columns(2)
    base.markdown("**Mobile base**")
    base.code('[forward speed, turning speed]\n[0.2, 0.0]  # m/s, rad/s', language="python")
    base.write("This command approaches the shelf. A base with no gripper cannot complete the cup-transfer task by itself.")
    arm.markdown("**Robot arm**")
    arm.code('[dx, dy, dz, droll, dpitch, dyaw, gripper]\n[0.02, 0, 0, 0, 0, 0, 1]', language="python")
    arm.write("With the supplied teaching convention, this moves the tool 2 cm along x with the gripper open. Many further steps would be needed to grasp and place the cup.")
    st.table([{"Change": "Different wording", "Which part changes": "Language input", "What it may require": "Clarification or examples in context"}, {"Change": "Different gripper or action dimensions", "Which part changes": "Action interface", "What it may require": "Compatible controller/adapter and robot demonstrations"}, {"Change": "Different camera view", "Which part changes": "Observation and frame relationship", "What it may require": "Calibration and demonstrations covering that view"}])
    st.write("Internet-scale pretraining provides broad language and visual patterns. Robot-action training connects observations with commands. Open X-Embodiment aggregates demonstrations from several platforms, but their schemas, units and timing still have to be interpreted.")
    st.markdown("[Open X-Embodiment project](https://robotics-transformer-x.github.io/)")


ADAPTATIONS = {
    "Zero-shot prompting": ("Give an instruction without examples or weight updates.", "Replace Bring it with Bring the blue cup to the tray. This may resolve wording, but cannot add a missing gripper."),
    "Few-shot prompting": ("Put examples into the model's input context. Its parameters remain fixed.", "Supply two examples matching a named cup to its requested tray before asking about another cup. The interface must support these examples."),
    "Additional demonstrations": ("Collect more observation-action records. Collecting data alone does not change the model.", "Record grasps from a new camera angle, with different cup positions. These records can later support adaptation."),
    "LoRA": ("Train small added low-rank parameter updates while keeping the main pretrained weights fixed.", "Use new grasp demonstrations to train small adapter weights for a compatible robot setup, then evaluate held-out grasps."),
    "Full fine-tuning": ("Update the pretrained model's weights using task data.", "Train on representative demonstrations for a new manipulation setup. Check both the new task and whether earlier abilities degraded."),
    "Training from scratch": ("Start with new randomly initialized parameters and learn from training data.", "Train a small policy for one toy robot task from a large enough demonstration collection, without relying on pretrained weights."),
}


def adaptation(st):
    st.write("**Purpose:** distinguish changes to the input, changes to the data and changes to learned parameters. These choices solve different problems and require different evidence.")
    st.write("Parameters, also called weights, are the numbers learned during training. Frozen weights stay fixed when a model is used. Start with the definitions and concrete examples below, then manipulate the visual comparison.")
    columns = st.columns(2)
    for index, (name, (definition, example)) in enumerate(ADAPTATIONS.items()):
        column = columns[index % 2]
        column.markdown("**" + name + "**")
        column.write(definition)
        column.caption("Example: " + example)
    st.subheader("Compare what each adaptation choice changes")
    st.write("**Scenario:** a robot already has a pretrained model, but needs help moving cups to trays. You are choosing how to adapt that system. This comparison lets you inspect which information goes into the input, which records are collected for training, and which parameters change.")
    st.markdown("1. Leave the instruction as **Move the blue cup to the tray** and choose **Few-shot prompting**. Set the number of records to **2**. Read the two examples below the diagrams. They are supplied in the input context, while the model stays fixed.\n2. Choose **LoRA**, keeping the same instruction and two records. Now the records are training demonstrations, and the orange adapter blocks can be updated. The gray pretrained blocks stay fixed.\n3. Choose **Additional demonstrations**. The records are only stored. Collecting them has not trained the model. Then compare **Full fine-tuning** and **Training from scratch** to see which starting parameters change.\n4. Finally, select a concrete problem below the diagrams and read which kind of change could address it.")
    st.caption("Read each diagram from left to right: instruction and example records, followed by model parameters. Gray blocks are fixed pretrained weights, orange blocks are trainable weights or adapters, and purple blocks begin from a random initialization. Colored horizontal bars stand for the listed example records.")
    choice = st.selectbox("Show what this choice changes", list(ADAPTATIONS), key="control_adapt_choice")
    instruction = st.text_input("Task instruction supplied to the model", "Move the blue cup to the tray", max_chars=80, key="control_adapt_instruction")
    examples = st.slider("Number of example records supplied or collected", 1, 6, 2, key="control_adapt_records") if choice != "Zero-shot prompting" else 0
    left, right = st.columns(2)
    left.image(weights_diagram("Zero-shot prompting", 0), width="stretch")
    left.caption("Reference: instruction in, fixed pretrained model.")
    right.image(weights_diagram(choice, examples, instruction), width="stretch")
    right.caption("Selected choice. The diagram shows what changes, not a measured training run.")
    st.write("Reference instruction: Move it. Selected instruction: " + instruction)
    st.caption("Changing the instruction updates the input box. Changing the record count updates the bars and example table. Choosing an adaptation changes the parameter blocks. These controls explain the mechanism. They do not run training or predict a success rate.")
    if examples:
        context_examples = [("red cup", "red tray"), ("blue cup", "blue tray"), ("green cup", "green tray")]
        role = "Input-context example" if choice == "Few-shot prompting" else "Collected record, not yet trained" if choice == "Additional demonstrations" else "Training demonstration"
        with st.expander("Inspect the example records represented by the colored bars", expanded=True):
            st.table([{"Record": i + 1, "Example": f"Move {context_examples[i%3][0]} to {context_examples[i%3][1]}", "Use here": role} for i in range(examples)])
    explanations = {
        "Zero-shot prompting": "The instruction changes, but there are no example records and no parameter updates.",
        "Few-shot prompting": "The colored records are examples in the input context. The gray model blocks remain fixed. More examples consume more context.",
        "Additional demonstrations": "The colored records are collected data. Gray blocks remain unchanged because no training has taken place yet.",
        "LoRA": "Gray blocks represent frozen pretrained parameters. Orange blocks are the small adapter updates trained from demonstrations. The block counts are schematic, not parameter ratios.",
        "Full fine-tuning": "Orange model blocks represent updating the pretrained weights from the demonstration collection. The task examples are training data, rather than prompt examples.",
        "Training from scratch": "Purple blocks represent new parameters learned from a random starting point. There is no pretrained starting model to preserve.",
    }
    st.info(explanations[choice])
    scenario = st.selectbox("Apply the comparison to a concrete problem", ["The request does not identify the intended cup", "Grasps fail from a new camera angle", "The new robot has a different gripper interface"], key="control_adapt_scenario")
    st.write({"The request does not identify the intended cup": "First obtain a clearer instruction or relevant examples. Updating weights is not a substitute for learning which cup this user intends.", "Grasps fail from a new camera angle": "Collect demonstrations covering that angle, then consider LoRA or full fine-tuning. Evaluate separate episodes from that view. More examples help only if they address the missing conditions.", "The new robot has a different gripper interface": "Check action dimensions, units, signs and controller support before adapting the model. Additional demonstrations may then be needed to learn the new behavior."}[scenario])
    st.write("**Try this:** compare Few-shot prompting with LoRA using the same number of example records. In the first, examples change the context. In the second, demonstrations train adapters. Then choose Additional demonstrations and notice that gathering records alone leaves the model fixed.")
    st.write("Keep evaluation episodes separate from adaptation data. Nearly identical frames from one trajectory should not be split across training and test sets. This exercise illustrates the interfaces and choices, rather than claiming that a particular amount of data guarantees better performance.")


def movement(st):
    st.write("**Starting question:** once a model has identified the right cup, how does its output become the right robot movement?")
    st.write("In Activity 2, you connected words to the intended object. In Activity 3, you saw that a mobile base and an arm need different commands. Activity 4 explained how a model can be adapted to a task. Even a well-adapted model still needs an agreed action interface: what its output means, which direction it refers to, and when the robot should look again.")
    st.info("You will investigate three separate interface choices: naming a skill, decoding a movement in a coordinate frame, and deciding how long to act before observing again. Each section starts a fresh worked example. Its output is not carried into the next section.")
    st.write("**Scenario:** a robot must approach a shelf or move its tool toward a cup. A correct object description alone cannot tell a controller which program to run, how far to move, or whether the cup has moved since the last camera image. You will see how each missing detail can change behavior.")
    st.subheader("1. A named skill and a direct action use different interfaces")
    symbolic, direct = st.columns(2)
    symbolic.code('{"tool": "navigate_to",\n "args": {"location": "shelf"}}', language="json")
    symbolic.write("This dictionary is a work order. tool names a skill and args holds its arguments. A schema defines which fields and types are required. A conventional navigation program must turn the named destination into movement.")
    direct.code('[dx, dy, dz, droll, dpitch, dyaw, gripper]', language="python")
    direct.write("This action vector describes tool movement. Translation uses metres, rotation uses radians, and the gripper convention must be supplied. A model can predict tokens that a decoder converts into such values.")
    st.write("**What to compare:** the left output asks a navigation skill to handle the route to a named place. The right output specifies small changes for an arm controller. Both can be useful, but they require different software interfaces. Mission 1 asks about a robot's capabilities. Mission 3 uses one-cell directional actions instead of a named navigation skill. Arm action vectors would require a different controller.")
    st.subheader("2. Decode and transform one movement")
    st.write("In this worked decoder, the token sets a signed movement along the camera's x-axis. A reference frame defines the physical directions of those axes. The same camera-axis movement points in a different world direction if that camera is rotated.")
    st.write("Imagine a camera watching the robot's tool next to a cup. The model outputs an integer token from 0 to 255. The supplied decoder maps that number to a camera-axis displacement between -0.10 m and +0.10 m. Values below the midpoint move in the negative direction. Values above it move in the positive direction. This translation is necessary because an integer by itself has no physical meaning.")
    token = st.slider("Predicted token controlling camera-x movement", 0, 255, 191, key="control_movement_token")
    angle = st.select_slider("Camera x-axis direction relative to world x", [0, 90], value=0, format_func=lambda v: "Aligned (0 degrees)" if v == 0 else "Rotated 90 degrees", key="control_movement_angle")
    move = decoded_movement(token, angle)
    left, right = st.columns(2)
    left.code(f"camera_dx = (token / 255 * 2 - 1) * 0.10\n# camera_dx = {move['camera_dx_m']:.3f} m\n# world movement = ({move['world_dx_m']:.3f}, {move['world_dy_m']:.3f}) m", language="python")
    right.image(trajectory_svg([{"x_m": 0., "y_m": 0.}, {"x_m": move["world_dx_m"], "y_m": move["world_dy_m"]}], scale=.1), width="stretch")
    right.caption("The blue segment starts at the tool's initial position (0, 0) and ends at its commanded position in world coordinates. Read its direction and length alongside the numeric world movement on the left.")
    st.write("**Try this:** keep the token fixed and rotate the camera axes. The length stays the same while the world direction changes. Next move the token below the midpoint to reverse direction. Joint-space commands would instead name changes to individual robot joints, which also depend on the robot.")
    st.caption("This is a supplied teaching decoder and frame transform, not OpenVLA's tokenizer. A real policy also requires its own normalization and controller conventions.")
    st.subheader("3. Compare action chunks and fresh feedback")
    st.write("An action chunk contains several predicted steps executed before a new observation. In this experiment, a tool starts moving right. At 0.5 seconds the target moves upward. Compare a controller that observes every step with one that holds the earlier commands for a chunk.")
    st.markdown("1. Keep **Commands per second** at **10** and set **Commands executed before observing again** to **1**. Both controllers now receive equally frequent observations, so their error curves overlap.\n2. Change only the chunk size to **4**. Four commands take 0.4 seconds. The robot can continue toward the earlier target until the next observation arrives. Compare its path, error curve and reported response delay.\n3. Keep the chunk at **4** and increase the rate to **20**. Four commands now take 0.2 seconds. Check whether the response delay changes in this particular trial.")
    hz = st.select_slider("Commands per second", [5, 10, 20], value=10, key="control_chunk_hz")
    chunk = st.slider("Commands executed before observing again", 1, 8, 4, key="control_chunk_size")
    baseline, base_delay = chunk_trial(1, hz)
    trial, delay = chunk_trial(chunk, hz)
    left, right = st.columns(2)
    path_picture = trajectory_svg(trial)
    path_picture = path_picture.replace('</svg>', '<circle cx="267" cy="79" r="8" fill="none" stroke="#16a34a" stroke-width="3"/><text x="279" y="73" font-family="sans-serif" font-size="13">target after 0.5 s</text></svg>')
    left.image(path_picture, width="stretch")
    left.caption("Selected chunk: blue path, red circle at the initial target, green circle at the target after it moves at 0.5 s.")
    import pandas as pd
    right.line_chart(pd.DataFrame({"Time (s)": [r["time_s"] for r in trial], "Observe every command": [r["error_m"] for r in baseline], "Selected chunk": [r["error_m"] for r in trial]}).set_index("Time (s)"), x_label="Time (s)", y_label="Error to current target (m)")
    right.write(f"The selected controller updates its commands {delay:.2f} s after the target changes. With one command per observation, the delay is {base_delay:.2f} s at this sampling rate.")
    st.write("**Read the graph:** the horizontal axis is elapsed time. The vertical axis is the tool's distance from the target's current location, so lower is closer. Both curves can jump when the target moves at 0.5 seconds, even though the tool does not jump. After that change, compare how soon each controller starts reducing the error. The path plot shows only the selected chunk controller, while the graph compares it with the fresh-observation baseline.")
    st.write("**Try this:** compare chunks of 1 and 4 at 10 commands per second. The longer chunk keeps using the old direction for longer. Changing the command rate also changes the time represented by a chunk. A predicted future image could suggest what might happen, but new feedback is what reveals where the robot and target actually are.")
    st.success("**Takeaway:** recognizing the intended object is only the beginning. Useful action also depends on a compatible command format, the correct coordinate frame, and timely feedback. In the next activity you will check whether a proposed skill should be allowed to run at all.")


def validation(st):
    st.write("**Starting question:** if a model proposes an action in the correct format, should the robot immediately carry it out?")
    st.write("Activity 5 explained how commands become movement. This activity adds the decision before execution. A proposal can name a valid skill yet rely on an old observation, refer to the wrong cup, request an unavailable destination, or come from text the robot happened to see. A validator is ordinary code that checks these conditions before allowing a skill to run.")
    st.write("**Scenario:** a simulated mobile robot starts at base. It can navigate to the shelf or desk, inspect a known object, report information, or stop. The closed room is unavailable and prohibited. Inspection records an observation without moving the robot. These are bounded teaching skills, rather than a physical camera or navigation system.")
    st.markdown("1. Select **Navigate to the shelf**, leaving the observation age at **0.10 s** and evidence score at **0.90**. Read the proposal and checks, then click **Validate and attempt this action**. Both systems should reach the shelf.\n2. Increase the age above **2 seconds** and click the button again. Compare the unchecked attempt with the validated system, which should withhold the action.\n3. Select **Inspect the known cup** and run it. The robot stays in place, but the inspection marker and recorded observation change. Then compare **Use an old cup observation** and **Inspect an ambiguous cup**.\n4. Try the unreachable room and poster instruction. Read the failed rule, then inspect whether a skill was attempted and whether it actually completed.")
    names = {"Navigate to the shelf": "navigate", "Inspect the known cup": "inspect", "Navigate to an unreachable room": "unreachable", "Use an old cup observation": "stale", "Inspect an ambiguous cup": "ambiguous", "Follow an instruction from a poster": "poster"}
    chosen = st.selectbox("Start with this proposal", list(names), key="control_validate_case")
    proposal = copy.deepcopy(next(p for key, p, _ in CASES if key == names[chosen]))
    a, b = st.columns(2)
    proposal["observation_age_s"] = a.slider("Age of supporting observation (seconds)", 0., 30., float(proposal["observation_age_s"]), .1, key="control_validate_age_" + names[chosen])
    proposal["confidence"] = b.slider("Evidence score", .1, 1., float(proposal["confidence"]), .1, key="control_validate_conf_" + names[chosen])
    st.write("The course policy rejects unavailable or unauthorized actions, abstains if age exceeds 2 s or score falls below 0.6, and asks for confirmation if ambiguity remains. A score is an interface value, not a certified probability of correctness.")
    st.caption("The proposal is a dictionary describing the requested skill and its evidence. Source identifies who supplied the instruction. Observation age says how old its supporting evidence is. Ambiguous means the target still needs clarification. Each dropdown choice loads a different proposal. The sliders let you vary only freshness or score within that case.")
    a, b = st.columns([2, 3])
    a.json(proposal)
    verdict, trace = decision_walkthrough(proposal)
    b.table(trace)
    st.info("Decision: " + verdict + ". " + {"EXECUTE": "The checks passed, so the bounded skill may attempt the action.", "REJECT": "The proposal failed a capability, format, grounding or authority check. It must not execute.", "ABSTAIN": "The evidence is not usable. Obtain fresh or more reliable evidence before proceeding.", "CONFIRM": "Wait for a person to resolve or authorize the proposal. The robot does not act yet."}[verdict])
    st.write("The table is evaluated from top to bottom. It stops at the first failed check. Not reached means the program did not need to evaluate a later rule. This order prevents a high score or a confirmation request from overriding an unsupported action.")
    signature = json.dumps(proposal, sort_keys=True)
    if st.button("Validate and attempt this action", type="primary"):
        trials = []
        for mode, decision in (("Unchecked skill attempt", "EXECUTE"), ("Validated system", verdict)):
            state = copy.deepcopy(STATE)
            before = copy.deepcopy(state)
            success, feedback = execute(proposal, state) if decision == "EXECUTE" else (False, "No execution. " + decision)
            trials.append({"mode": mode, "decision": decision, "before": before, "after": state, "completed": success, "feedback": feedback})
        st.session_state["guided_execution"] = {"signature": signature, "trials": trials}
    experiment = st.session_state.get("guided_execution")
    if experiment and experiment["signature"] == signature:
        for column, result in zip(st.columns(2), experiment["trials"]):
            column.markdown("**" + result["mode"] + "**")
            column.image(execution_result_svg(proposal, result), width="stretch")
            column.write("Decision: " + result["decision"])
            column.write("Feedback: " + result["feedback"])
            column.write("Robot position: " + result["before"]["position"] + " Ã¢â€ â€™ " + result["after"]["position"])
            column.write("Last inspected object: " + str(result["before"].get("last_observation", "none")) + " Ã¢â€ â€™ " + str(result["after"].get("last_observation", "none")))
        st.caption("Both panels use the same starting world so the comparison stays fair. A green arrow shows completed navigation, a cup highlight shows a completed inspection, and a dashed request shows an action that did not complete. A blocked action leaves the robot and observations unchanged. The source and evidence labels identify the selected proposal even when its destination matches another case.")
    elif experiment:
        st.caption("The proposal changed. Run the action again to compare these current inputs.")
    st.write("**Try this:** first run Navigate to the shelf with fresh evidence. The accepted skill moves the simulated robot from base to shelf. Increase the age above 2 s and run again. The validated system now abstains and stays at base. Finally choose the unreachable room. The unchecked skill attempts the request but reports failure, while the validator rejects it before execution.")
    st.write("**Use this in the missions:** a model's answer is different from an observed outcome. In Mission 1, compare generated plans with the capability card. In Mission 2, compare generated image claims with what is actually visible. In Mission 3, run a prompt with the live model and inspect how its automatically checked directional actions change the maze position.")


ACTIVITIES = (model_roles, grounding, demonstrations, adaptation, movement, validation)
