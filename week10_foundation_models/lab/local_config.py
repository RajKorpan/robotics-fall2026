"""Pinned local models and short, controlled mission inputs."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_CONFIG = {
    "language": {"id": "HuggingFaceTB/SmolLM2-360M-Instruct", "revision": "a10cc1512eabd3dde888204e902eca88bddb4951"},
    "vision": {"id": "HuggingFaceTB/SmolVLM-500M-Instruct", "revision": "a7da5b986cb59b408707209984f360a5f4ad7e47"},
}
LANGUAGE_TASKS = {
    "clear": {"label": "Clear request", "prompt": "Go to the shelf, inspect the cup, and report what you observe."},
    "ambiguous": {"label": "Ambiguous request", "prompt": "Go over there and inspect it."},
    "capability": {"label": "Beyond the robot's capabilities", "prompt": "Pick up the cup and carry it to the desk."},
}
CAPABILITIES = "You are helping a mobile robot. It starts at base. It can navigate to base, shelf or desk, inspect a known object, report observations, or stop. There is a cup on the shelf and a book on the desk. The robot has a camera and wheels but no arm or gripper. It cannot pick up or carry objects."
LANGUAGE_SYSTEM = CAPABILITIES + " Suggest a short plan using only these capabilities. If information is missing, ask a specific clarification question. If the task is impossible for this robot, explain why. Use at most four short sentences."
VISION_PREPROCESSING = {"longest_edge": 512, "image_splitting": False}
VISION_TASKS = {
    "identify": {"label": "Identify", "prompt": "What tool is lying in the foreground of this workbench?"},
    "spatial": {"label": "Locate", "prompt": "Where is the black vertical metal post relative to the tool in the foreground?"},
    "purpose": {"label": "Decide", "prompt": "A robot needs the correct tool for its task. Which object in this image should it pick up?"},
}
VISION_REFERENCE = "A metal drawing compass lies in the foreground. A dark vertical post and its circular base are to its right. A brown leather notebook lies behind them. The photograph does not specify the robot's task, establish graspability, or show what else is around."


def runtime_dir():
    # Native storage avoids thousands of tiny package writes over Docker's Windows bind mount.
    return Path(os.environ.get("LAB9_MODEL_RUNTIME", Path.home() / ".cache" / "course-lab9" / ("venv-" + sys.platform)))


def model_python():
    return runtime_dir() / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def model_dir(kind):
    return ROOT / "runtime" / "models" / (kind + "-" + MODEL_CONFIG[kind]["revision"][:12])


def scene_path(scene=None):
    return ROOT / "assets" / "live_vision" / "workbench.jpg"


def contract_signature(kind):
    import hashlib
    import json
    inputs = {"model": MODEL_CONFIG[kind], "flow": "compare-three-custom-v2"}
    if kind == "language":
        inputs.update({"system": LANGUAGE_SYSTEM, "tasks": LANGUAGE_TASKS})
    else:
        inputs.update({"tasks": VISION_TASKS, "preprocessing": VISION_PREPROCESSING,
                       "image": hashlib.sha256(scene_path().read_bytes()).hexdigest()})
    return hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
