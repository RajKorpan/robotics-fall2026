"""Live reinforcement-learning activity for the CartPole inverted pendulum.

Run the interactive app with:

    streamlit run pendulum_rl_live.py

Run a tiny non-interactive check with:

    python pendulum_rl_live.py --smoke-test
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import html
import io
import importlib
import importlib.util
import json
import math
import os
import pickle
import random
import sys
import uuid
import zipfile
from datetime import datetime
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


os.environ.setdefault("MPLCONFIGDIR", "/tmp/pendulum_rl_matplotlib")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


CART_HALF_WIDTH = 0.20
CART_HALF_HEIGHT = 0.12
CART_AXLE_Y = 0.06
POLE_LENGTH = 1.0
POLE_HALF_WIDTH = 0.04
ANIMAL_Y = 0.0


def clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def wrap_angle(theta: float) -> float:
    return ((float(theta) + math.pi) % (2.0 * math.pi)) - math.pi


def normalized_observation_values(
    raw_state: Any,
    animal_position: float = 0.0,
) -> dict[str, float]:
    """Map observations into stable ranges before the agent sees them."""
    x, x_dot, theta, theta_dot = [float(value) for value in raw_state]
    wrapped_theta = wrap_angle(theta)
    animal_distance = x - float(animal_position)

    return {
        "cart_position": clamp(x / 2.4),
        "cart_velocity": clamp(x_dot / 3.0),
        "pole_angle": clamp(wrapped_theta / math.pi),
        "sin_theta": math.sin(theta),
        "cos_theta": math.cos(theta),
        "pole_angular_velocity": clamp(theta_dot / 3.5),
        "animal_distance": clamp(animal_distance / 2.4),
        "abs_animal_distance": clamp(abs(animal_distance) / 2.4, 0.0, 1.0),
    }


# ---------------------------------------------------------------------------
# LIVE CODING SPOTS: change these functions during the activity.
# ---------------------------------------------------------------------------
def observation_function(
    raw_state: Any,
    features: tuple[str, ...],
    animal_position: float = 0.0,
) -> Any:
    """Choose what the agent sees from the CartPole state.

    Values returned here are normalized so Q-learning and DQN both train on
    compact inputs instead of raw environment magnitudes.
    """
    np = require_dependencies("numpy")["numpy"]
    feature_values = normalized_observation_values(raw_state, animal_position)
    return np.array([feature_values[name] for name in features], dtype=np.float32)


def action_function(action_index: int, action_forces: tuple[float, ...]) -> float:
    """Map the action chosen by the agent into a cart force."""
    return float(action_forces[action_index])


def reward_signal_observations(
    raw_state: Any,
    env_reward: float,
    terminated: bool,
    action_force: float,
    animal_position: float = 0.0,
    animal_radius: float = 0.0,
) -> dict[str, float]:
    """Base normalized signals used by reward blocks."""
    x, x_dot, theta, theta_dot = [float(value) for value in raw_state]
    wrapped_theta = wrap_angle(theta)
    animal_distance = x - animal_position
    contact = animal_contact(raw_state, animal_position, animal_radius)
    track_limit = 2.4

    state_signals = {
        "cart_position": clamp(x / 2.4),
        "abs_cart_position": clamp(abs(x) / 2.4, 0.0, 1.0),
        "cart_velocity": clamp(x_dot / 3.0),
        "abs_cart_velocity": clamp(abs(x_dot) / 3.0, 0.0, 1.0),
        "pole_angle": clamp(wrapped_theta / math.pi),
        "abs_pole_angle": clamp(abs(wrapped_theta) / math.pi, 0.0, 1.0),
        "sin_theta": math.sin(theta),
        "cos_theta": math.cos(theta),
        "pole_angular_velocity": clamp(theta_dot / 3.5),
        "abs_pole_angular_velocity": clamp(abs(theta_dot) / 3.5, 0.0, 1.0),
        "action_force": clamp(action_force / 10.0),
        "abs_action_force": clamp(abs(action_force) / 10.0, 0.0, 1.0),
        "animal_distance": clamp(animal_distance / 2.4),
        "abs_animal_distance": clamp(abs(animal_distance) / 2.4, 0.0, 1.0),
        "pole_distance_to_animal": clamp(float(contact["pole_distance"]) / 2.4, 0.0, 1.0),
    }

    return {
        "env_reward": float(env_reward),
        "alive": 1.0,
        "cart_off_screen": 1.0 if abs(x) >= track_limit else 0.0,
        "fell": 1.0 if terminated else 0.0,
        "cart_hit_animal": 1.0 if contact["cart_hit"] else 0.0,
        "pole_hit_animal": 1.0 if contact["pole_hit"] else 0.0,
        "hit_animal": 1.0 if contact["hit"] else 0.0,
        **state_signals,
    }


def animal_contact(
    raw_state: Any,
    animal_position: float,
    animal_radius: float,
) -> dict[str, float | bool]:
    """Detect full cart rectangle and pole capsule contact with the animal circle."""
    x, _, theta, _ = [float(value) for value in raw_state]
    animal_radius = max(0.0, float(animal_radius))
    animal_x = float(animal_position)
    animal_y = ANIMAL_Y

    cart_left = x - CART_HALF_WIDTH
    cart_right = x + CART_HALF_WIDTH
    cart_bottom = -CART_HALF_HEIGHT
    cart_top = CART_HALF_HEIGHT
    closest_cart_x = min(max(animal_x, cart_left), cart_right)
    closest_cart_y = min(max(animal_y, cart_bottom), cart_top)
    cart_surface_distance = math.hypot(animal_x - closest_cart_x, animal_y - closest_cart_y)
    cart_clearance = max(0.0, cart_surface_distance - animal_radius)
    cart_hit = animal_radius > 0.0 and cart_surface_distance <= animal_radius

    pole_base_x = x
    pole_base_y = CART_AXLE_Y
    pole_tip_x = pole_base_x + POLE_LENGTH * math.sin(theta)
    pole_tip_y = pole_base_y + POLE_LENGTH * math.cos(theta)
    segment_dx = pole_tip_x - pole_base_x
    segment_dy = pole_tip_y - pole_base_y
    segment_length_squared = max(1e-9, segment_dx * segment_dx + segment_dy * segment_dy)
    projection = ((animal_x - pole_base_x) * segment_dx + (animal_y - pole_base_y) * segment_dy) / segment_length_squared
    projection = max(0.0, min(1.0, projection))
    closest_pole_x = pole_base_x + projection * segment_dx
    closest_pole_y = pole_base_y + projection * segment_dy
    pole_centerline_distance = math.hypot(animal_x - closest_pole_x, animal_y - closest_pole_y)
    pole_clearance = max(0.0, pole_centerline_distance - POLE_HALF_WIDTH - animal_radius)
    pole_hit = animal_radius > 0.0 and pole_centerline_distance <= animal_radius + POLE_HALF_WIDTH

    return {
        "cart_hit": cart_hit,
        "pole_hit": pole_hit,
        "hit": cart_hit or pole_hit,
        "cart_distance": cart_clearance,
        "pole_distance": pole_clearance,
        "pole_centerline_distance": pole_centerline_distance,
    }


def reward_function(
    obs: Any,
    action: int,
    action_force: float,
    next_obs: Any,
    env_reward: float,
    terminated: bool,
    truncated: bool,
    weights: dict[str, Any],
) -> float:
    """Turn the environment reward into the reward the agent actually learns."""
    del obs, truncated, action

    signals = reward_signal_observations(
        next_obs,
        env_reward,
        terminated,
        action_force,
        float(weights.get("animal_position", 0.0)),
        float(weights.get("animal_radius", 0.0)),
    )
    x, _, theta, _ = [float(value) for value in next_obs]
    if "target_cart_position" in weights:
        target_x = float(weights.get("target_cart_position", 0.0))
        signals["target_cart_position_error"] = clamp(abs(x - target_x) / 2.4, 0.0, 1.0)
    if "target_pole_angle" in weights:
        target_theta = float(weights.get("target_pole_angle", 0.0))
        signals["target_pole_angle_error"] = clamp(abs(wrap_angle(theta - target_theta)) / math.pi, 0.0, 1.0)

    reward_tokens = weights.get("reward_tokens")
    if isinstance(reward_tokens, list) and reward_tokens:
        return evaluate_reward_tokens(reward_tokens, signals)

    total = 0.0
    product_group = 1.0
    group_started = False
    for term in weights["reward_terms"]:
        term_value = reward_term_value(term, signals)
        connector = str(term.get("connector", "add"))
        if connector == "multiply" and group_started:
            product_group *= term_value
        else:
            if group_started:
                total += product_group
            product_group = term_value
            group_started = True

    if group_started:
        total += product_group
    return float(total)


def default_reward_scale(signal: str) -> str:
    return "pi" if signal in {"pole_angle", "abs_pole_angle"} else "unit"


def clean_reward_scale(signal: str, scale: str) -> str:
    if signal not in REWARD_SCALE_SIGNALS:
        return "unit"
    if scale not in REWARD_SCALE_LABELS:
        return default_reward_scale(signal)
    return scale


def reward_signal_scale(value: float, scale: str) -> float:
    if scale == "pi":
        return float(value) * math.pi
    return float(value)


def reward_term_value(term: dict[str, Any], signals: dict[str, float]) -> float:
    signal = str(term["signal"])
    value = signals[signal]
    scale = clean_reward_scale(signal, str(term.get("scale", default_reward_scale(signal))))
    value = reward_signal_scale(value, scale)
    transform = str(term.get("transform", "abs" if term.get("absolute", False) else "raw"))
    if transform == "abs":
        value = abs(value)
    elif transform == "sin":
        value = math.sin(value)
    elif transform == "cos":
        value = math.cos(value)
    return float(term["factor"]) * value


def evaluate_reward_tokens(tokens: list[Any], signals: dict[str, float]) -> float:
    precedence = {"add": 1, "multiply": 2}
    output: list[float | str] = []
    operators: list[str] = []
    expecting_value = True

    def apply_operator_stack(new_operator: str) -> None:
        while (
            operators
            and operators[-1] != "("
            and not operators[-1].startswith("func:")
            and precedence[operators[-1]] >= precedence[new_operator]
        ):
            output.append(operators.pop())
        operators.append(new_operator)

    for token in tokens:
        if not isinstance(token, dict):
            continue

        token_type = str(token.get("type", "term" if "signal" in token else ""))
        if token_type == "term":
            try:
                output.append(reward_term_value(token, signals))
                expecting_value = False
            except (KeyError, TypeError, ValueError):
                continue
        elif token_type == "func" and isinstance(token.get("children"), list):
            child_value = evaluate_reward_tokens(token["children"], signals)
            function_name = str(token.get("func", "abs"))
            threshold = float(token.get("threshold", 0.0))
            if function_name == "abs":
                child_value = abs(child_value)
            elif function_name == "sin":
                child_value = math.sin(child_value)
            elif function_name == "cos":
                child_value = math.cos(child_value)
            elif function_name == "min":
                child_value = min(child_value, threshold)
            elif function_name == "max":
                child_value = max(child_value, threshold)
            else:
                continue
            output.append(float(token.get("factor", 1.0)) * child_value)
            expecting_value = False
        elif token_type == "func":
            function_name = str(token.get("func", "abs"))
            if function_name in ("abs", "sin", "cos"):
                operators.append(f"func:{function_name}")
                expecting_value = True
        elif token_type == "op" and not expecting_value:
            operator = "multiply" if token.get("op") in ("multiply", "*", "x") else "add"
            apply_operator_stack(operator)
            expecting_value = True
        elif token_type == "paren" and token.get("value") == "(":
            operators.append("(")
            expecting_value = True
        elif token_type == "paren" and token.get("value") == ")" and not expecting_value:
            while operators and operators[-1] != "(":
                output.append(operators.pop())
            if operators and operators[-1] == "(":
                operators.pop()
            if operators and operators[-1].startswith("func:"):
                output.append(operators.pop())
            expecting_value = False

    while operators:
        operator = operators.pop()
        if operator != "(":
            output.append(operator)

    stack: list[float] = []
    for item in output:
        if isinstance(item, float):
            stack.append(item)
        elif item in precedence and len(stack) >= 2:
            right = stack.pop()
            left = stack.pop()
            stack.append(left + right if item == "add" else left * right)
        elif isinstance(item, str) and item.startswith("func:") and stack:
            value = stack.pop()
            function_name = item.removeprefix("func:")
            if function_name == "abs":
                stack.append(abs(value))
            elif function_name == "sin":
                stack.append(math.sin(value))
            elif function_name == "cos":
                stack.append(math.cos(value))

    return float(stack[-1]) if stack else 0.0


REWARD_SIGNAL_LABELS: dict[str, str] = {
    "alive": "alive each step",
    "cart_position": "cart position",
    "abs_cart_position": "|cart position|",
    "cart_off_screen": "cart off screen",
    "cart_velocity": "cart velocity",
    "abs_cart_velocity": "|cart velocity|",
    "pole_angle": "pole angle",
    "abs_pole_angle": "|pole angle|",
    "sin_theta": "sin(theta)",
    "cos_theta": "cos(theta)",
    "pole_angular_velocity": "pole angular velocity",
    "abs_pole_angular_velocity": "|pole angular velocity|",
    "action_force": "cart force",
    "abs_action_force": "|cart force|",
    "fell": "fell",
    "animal_distance": "distance to animal",
    "abs_animal_distance": "|distance to animal|",
    "pole_distance_to_animal": "pole distance to animal",
    "cart_hit_animal": "cart hit animal",
    "pole_hit_animal": "pole hit animal",
    "hit_animal": "cart or pole hit animal",
    "target_cart_position_error": "distance from target position",
    "target_pole_angle_error": "distance from target angle",
}


DEFAULT_REWARD_TERMS: tuple[dict[str, Any], ...] = ()


DEFAULT_REWARD_WEIGHTS: dict[str, Any] = {
    "reward_terms": [dict(term) for term in DEFAULT_REWARD_TERMS],
}


BASELINE_REWARD_WEIGHTS: dict[str, Any] = {
    "reward_terms": [{"signal": "alive", "factor": 1.0, "scale": "unit"}],
}


OBSERVATION_DEMO_REWARD_WEIGHTS: dict[str, Any] = {
    "reward_terms": [
        {"signal": "alive", "factor": 1.0, "scale": "unit"},
        {"signal": "pole_angle", "factor": 1.0, "transform": "cos", "scale": "pi"},
        {"signal": "pole_angle", "factor": -2.0, "transform": "abs", "scale": "pi"},
        {"signal": "pole_angular_velocity", "factor": -0.2, "transform": "abs", "scale": "unit"},
        {"signal": "cart_position", "factor": -0.1, "transform": "abs", "scale": "unit"},
        {"signal": "fell", "factor": -8.0, "scale": "unit"},
    ],
}


# Reward used by the interactive observation/action playground demos. A more
# robust signal than -1 * fell: reward an upright pole (cos of pole angle) and a
# centered cart (cos of cart position), so the agent is rewarded for the whole
# ideal pose rather than just for not having fallen yet.
CONTROLLED_DEMO_REWARD_WEIGHTS: dict[str, Any] = {
    "reward_terms": [
        {"signal": "pole_angle", "factor": 1.0, "transform": "cos", "scale": "pi"},
        {"signal": "cart_position", "factor": 1.0, "transform": "cos", "scale": "unit"},
    ],
}


REWARD_DEMO_WEIGHTS: dict[str, dict[str, Any]] = {
    # Reliable upright balance: reward standing straight, punish falling.
    "balance": {
        "reward_terms": [
            {"signal": "alive", "factor": 1.0, "scale": "unit"},
            {"signal": "pole_angle", "factor": 1.0, "transform": "cos", "scale": "pi"},
            {"signal": "pole_angle", "factor": -2.0, "transform": "abs", "scale": "pi"},
            {"signal": "fell", "factor": -8.0, "scale": "unit"},
        ],
    },
    # Go as fast as possible without driving off the screen.
    "max_cart_velocity": {
        "reward_terms": [
            {"signal": "cart_velocity", "factor": 1.0, "transform": "abs", "scale": "unit"},
            {"signal": "cart_off_screen", "factor": -10.0, "scale": "unit"},
        ],
    },
    # Spin the pole as fast as possible; falling is allowed (no fell penalty,
    # and the episode does not stop when the pole tips over).
    "max_pole_velocity": {
        "reward_terms": [
            {"signal": "pole_angular_velocity", "factor": 1.0, "transform": "abs", "scale": "unit"},
            {"signal": "cart_off_screen", "factor": -10.0, "scale": "unit"},
        ],
    },
}


CONTROLLED_DEMO_VERSION = "controlled-demo-v8-1k"
DEMO_EPISODES = 500
# The reward demos need to converge enough to show the cos-vs-sin difference, so
# they train longer than the snappy observation/action demos.
REWARD_DEMO_EPISODES = 800
DEMO_MAX_STEPS = 300
DEMO_LEARNING_RATE = 0.25
DEMO_GAMMA = 0.99
DEMO_EPSILON = 0.9
DEMO_EPSILON_MIN = 0.05
DEMO_Q_BINS = 6

# The reward-design exercise needs training strong enough that a genuinely good
# reward reliably balances (so students can trust what they see). Tabular
# Q-learning on the 4D state needs more bins and more episodes than the snappy
# observation/action demos use.
REWARD_LESSON_EPISODES = 1000
REWARD_LESSON_Q_BINS = 10
REWARD_LESSON_LEARNING_RATE = 0.1
REWARD_LESSON_EPSILON_MIN = 0.01


REWARD_SCALE_LABELS: dict[str, str] = {
    "unit": "[-1,1]",
    "pi": "[-pi,pi]",
}


# Continuous observation signals that can be read either on their normalized
# [-1,1] scale or stretched onto [-pi,pi] (so cos/sin treat the value as an angle).
REWARD_SCALE_SIGNALS: set[str] = {
    "cart_position",
    "abs_cart_position",
    "cart_velocity",
    "abs_cart_velocity",
    "pole_angle",
    "abs_pole_angle",
    "pole_angular_velocity",
    "abs_pole_angular_velocity",
    "sin_theta",
    "cos_theta",
    "action_force",
    "abs_action_force",
    "animal_distance",
    "abs_animal_distance",
    "pole_distance_to_animal",
}


def reward_signal_display(signal: str, transform: str = "raw") -> str:
    if signal.startswith("abs_"):
        signal = signal.removeprefix("abs_")
        transform = "abs"

    label = REWARD_SIGNAL_LABELS.get(signal, signal)
    if transform == "abs":
        return f"|{label}|"
    if transform == "sin":
        return f"sin({label})"
    if transform == "cos":
        return f"cos({label})"
    return label


OBSERVATION_LABELS: dict[str, str] = {
    "cart_position": "Cart position",
    "cart_velocity": "Cart velocity",
    "pole_angle": "Pole angle",
    "sin_theta": "sin(theta)",
    "cos_theta": "cos(theta)",
    "pole_angular_velocity": "Pole angular velocity",
    "animal_distance": "Distance to animal",
    "abs_animal_distance": "|Distance to animal|",
}


OBSERVATION_DESCRIPTIONS: dict[str, str] = {
    "cart_position": "Where the cart is on the track.",
    "cart_velocity": "How fast the cart is moving left or right.",
    "pole_angle": "Which way the pole is leaning.",
    "pole_angular_velocity": "How fast the pole is rotating.",
    "sin_theta": "A smooth angle helper based on pole angle.",
    "cos_theta": "A smooth uprightness helper based on pole angle.",
    "animal_distance": "Signed distance from the cart to the animal.",
}


FEATURE_RANGES: dict[str, tuple[float, float]] = {
    "cart_position": (-1.0, 1.0),
    "cart_velocity": (-1.0, 1.0),
    "pole_angle": (-1.0, 1.0),
    "sin_theta": (-1.0, 1.0),
    "cos_theta": (-1.0, 1.0),
    "pole_angular_velocity": (-1.0, 1.0),
    "animal_distance": (-1.0, 1.0),
    "abs_animal_distance": (0.0, 1.0),
}


DEFAULT_OBSERVATION_FEATURES: tuple[str, ...] = (
    "cart_position",
    "cart_velocity",
    "pole_angle",
    "pole_angular_velocity",
)


_DRAG_CANVAS_COMPONENT: Any | None = None


def drag_builder_session_token(st: Any) -> str:
    """Stable per-session token for drag-canvas reset ids.

    The drag component persists its live value in the browser's sessionStorage
    keyed by reset_id so that a mid-interaction iframe remount does not flash the
    box back to empty. Tying the reset_id to a per-session token keeps that key
    stable within a session while ensuring a genuinely new session starts fresh
    instead of restoring another session's stale value.
    """
    token = st.session_state.get("drag_builder_session_token")
    if not token:
        token = uuid.uuid4().hex
        st.session_state["drag_builder_session_token"] = token
    return str(token)


def drag_canvas_component(
    *,
    mode: str,
    title: str,
    pool: list[dict[str, Any]],
    value: list[Any],
    key: str,
    height: int,
    reset_id: str = "",
) -> Any:
    """Render the local drag/drop builder and return its JSON value."""
    global _DRAG_CANVAS_COMPONENT
    components = require_dependencies("streamlit.components.v1")["streamlit.components.v1"]
    if _DRAG_CANVAS_COMPONENT is None:
        component_dir = Path(__file__).parent / "drag_canvas"
        _DRAG_CANVAS_COMPONENT = components.declare_component(
            "drag_canvas",
            path=str(component_dir),
        )

    return _DRAG_CANVAS_COMPONENT(
        mode=mode,
        title=title,
        pool=pool,
        value=value,
        height=height,
        reset_id=reset_id,
        default=value,
        key=key,
    )


_PENDULUM_PLAYGROUND_COMPONENT: Any | None = None


def pendulum_playground_component(*, height: int = 470, key: str = "pendulum_playground") -> Any:
    """Render the interactive drag-the-pendulum explainer component."""
    global _PENDULUM_PLAYGROUND_COMPONENT
    components = require_dependencies("streamlit.components.v1")["streamlit.components.v1"]
    if _PENDULUM_PLAYGROUND_COMPONENT is None:
        component_dir = Path(__file__).parent / "pendulum_playground"
        _PENDULUM_PLAYGROUND_COMPONENT = components.declare_component(
            "pendulum_playground",
            path=str(component_dir),
        )
    return _PENDULUM_PLAYGROUND_COMPONENT(height=height, key=key)


_RL_CONCEPTS_COMPONENT: Any | None = None


def rl_concepts_component(*, key: str = "rl_concepts") -> Any:
    """Render the interactive RL-concepts slide deck and return its value
    (a dict with {"done": True} once the student finishes the last slide)."""
    global _RL_CONCEPTS_COMPONENT
    components = require_dependencies("streamlit.components.v1")["streamlit.components.v1"]
    if _RL_CONCEPTS_COMPONENT is None:
        component_dir = Path(__file__).parent / "rl_concepts"
        _RL_CONCEPTS_COMPONENT = components.declare_component(
            "rl_concepts",
            path=str(component_dir),
        )
    return _RL_CONCEPTS_COMPONENT(key=key)


ACTION_PRESETS: dict[str, tuple[float, ...]] = {
    "Standard left/right": (-10.0, 10.0),
    "Gentle left/none/right": (-5.0, 0.0, 5.0),
    "Strong left/none/right": (-15.0, 0.0, 15.0),
    "Five force levels": (-15.0, -7.5, 0.0, 7.5, 15.0),
    "Custom": (-10.0, 10.0),
}


TUTORIAL_STEPS: tuple[dict[str, str], ...] = (
    {
        "target": "training",
        "title": "Training controls",
        "body": "Pick the learning method, practice budget, learning speed, and exploration. As in the grid game, exploration means trying moves before the notebook is trustworthy; later the agent gets greedy and follows its best Q-values.",
    },
    {
        "target": "ethical",
        "title": "Ethical exploration",
        "body": "This changes the environment. The animal creates a safety constraint, and optional distance/contact signals let students ask what the agent can know and what it should value.",
    },
    {
        "target": "observation_action",
        "title": "Observations and actions",
        "body": "This is the grid-game notebook again: observations choose the row, actions are the choices in that row, and the policy picks the highest-scoring action.",
    },
    {
        "target": "reward",
        "title": "Reward function",
        "body": "Reward is the teacher. Just like spikes and gems nudged the grid-game Q-values, these blocks nudge force choices up or down in each pendulum situation.",
    },
    {
        "target": "train",
        "title": "Train agent",
        "body": "Training repeats the same loop from the grid game: observe, try an action, get reward, update the notebook, then slowly trust it more.",
    },
    {
        "target": "replay",
        "title": "Replay",
        "body": "Replay runs the learned policy without random exploration: the agent just reads its notebook and takes the force with the best Q-value.",
    },
    {
        "target": "curve",
        "title": "Learning curve",
        "body": "The curve is the grid-game score graph again. If the notebook is improving, total reward and CartPole score should rise over episodes.",
    },
    {
        "target": "policy",
        "title": "Policy map",
        "body": "This opens the learned notebook: which force has the highest Q-value in each pendulum situation, and how valuable that situation looks.",
    },
)


def require_dependencies(*module_names: str) -> dict[str, Any]:
    """Import external modules with a clear install message when missing."""
    modules: dict[str, Any] = {}
    missing: list[str] = []

    for module_name in module_names:
        try:
            modules[module_name] = importlib.import_module(module_name)
        except ModuleNotFoundError:
            missing.append(module_name)

    if missing:
        package_hint = ", ".join(sorted(missing))
        raise SystemExit(
            "Missing dependencies: "
            f"{package_hint}\n\n"
            "Create a virtual environment, activate it, then run:\n"
            "  python -m pip install -r requirements.txt"
        )

    return modules


@dataclass
class TrainSettings:
    algorithm: str
    episodes: int
    max_steps: int
    learning_rate: float
    gamma: float
    epsilon: float
    epsilon_min: float
    seed: int
    batch_size: int = 64
    hidden_size: int = 64
    target_update: int = 10
    update_every: int = 1
    parallel_envs: int = 1
    show_training_preview: bool = False
    training_preview_interval: int = 25
    q_bins_per_feature: int = 8
    observation_features: tuple[str, ...] = DEFAULT_OBSERVATION_FEATURES
    action_forces: tuple[float, ...] = ACTION_PRESETS["Standard left/right"]
    initial_state: tuple[float, float, float, float] | None = None
    terminate_on_angle: bool = True
    ethical_exploration: bool = False
    animal_position: float = 0.0
    animal_radius: float = 0.18
    animal_contact_ends_episode: bool = True
    # Half-pole length used by the CartPole physics (Gymnasium default is 0.5).
    pole_length: float = 0.5
    random_start_around_animal: bool = False


@dataclass
class TrainingResult:
    algorithm: str
    returns: list[float]
    env_returns: list[float]
    episode_lengths: list[int]
    policy: Any
    settings: TrainSettings
    reward_weights: dict[str, Any]
    label: str = "Current reward"


def make_env(render: bool = False) -> Any:
    gymnasium = require_dependencies("gymnasium")["gymnasium"]
    render_mode = "rgb_array" if render else None
    return gymnasium.make("CartPole-v1", render_mode=render_mode)


def reset_env(env: Any, settings: TrainSettings, seed: int) -> Any:
    np = require_dependencies("numpy")["numpy"]
    obs, _ = env.reset(seed=seed)

    # Apply a custom pole length: a longer pole has more rotational inertia, so it
    # tips more slowly and is actually easier to balance.
    base_env = env.unwrapped
    base_env.length = float(settings.pole_length)
    base_env.polemass_length = base_env.masspole * base_env.length

    if settings.random_start_around_animal:
        rng = np.random.default_rng(seed)
        side = -1.0 if rng.random() < 0.5 else 1.0
        start_x = clamp(settings.animal_position + side * 0.85, -1.6, 1.6)
        start_theta = float(rng.uniform(-0.04, 0.04))
        custom_state = (start_x, 0.0, start_theta, 0.0)
        base_env.state = np.array(custom_state, dtype=np.float64)
        return np.array(custom_state, dtype=np.float32)

    if settings.initial_state is None:
        return obs

    base_env.state = np.array(settings.initial_state, dtype=np.float64)
    return np.array(settings.initial_state, dtype=np.float32)


def step_cartpole_with_force(
    env: Any,
    force: float,
    terminate_on_angle: bool = True,
) -> tuple[Any, float, bool, bool, dict[str, Any]]:
    """Step CartPole with an arbitrary horizontal force."""
    np = require_dependencies("numpy")["numpy"]
    base_env = env.unwrapped
    x, x_dot, theta, theta_dot = base_env.state

    costheta = np.cos(theta)
    sintheta = np.sin(theta)
    temp = (force + base_env.polemass_length * np.square(theta_dot) * sintheta) / base_env.total_mass
    thetaacc = (base_env.gravity * sintheta - costheta * temp) / (
        base_env.length
        * (4.0 / 3.0 - base_env.masspole * np.square(costheta) / base_env.total_mass)
    )
    xacc = temp - base_env.polemass_length * thetaacc * costheta / base_env.total_mass

    if base_env.kinematics_integrator == "euler":
        x = x + base_env.tau * x_dot
        x_dot = x_dot + base_env.tau * xacc
        theta = theta + base_env.tau * theta_dot
        theta_dot = theta_dot + base_env.tau * thetaacc
    else:
        x_dot = x_dot + base_env.tau * xacc
        x = x + base_env.tau * x_dot
        theta_dot = theta_dot + base_env.tau * thetaacc
        theta = theta + base_env.tau * theta_dot

    base_env.state = np.array((x, x_dot, theta, theta_dot), dtype=np.float64)
    cart_out = x < -base_env.x_threshold or x > base_env.x_threshold
    angle_out = theta < -base_env.theta_threshold_radians or theta > base_env.theta_threshold_radians
    terminated = bool(cart_out or (terminate_on_angle and angle_out))
    return np.array(base_env.state, dtype=np.float32), 1.0, terminated, False, {}


def apply_animal_contact_termination(
    obs: Any,
    terminated: bool,
    settings: TrainSettings,
) -> bool:
    if not settings.ethical_exploration or not settings.animal_contact_ends_episode:
        return bool(terminated)

    contact = animal_contact(obs, settings.animal_position, settings.animal_radius)
    return bool(terminated or contact["hit"])


def seed_everything(seed: int) -> None:
    random.seed(seed)
    modules = require_dependencies("numpy")
    modules["numpy"].random.seed(seed)

    if importlib.util.find_spec("torch") is not None:
        torch = importlib.import_module("torch")
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)


def epsilon_for_episode(settings: TrainSettings, episode: int) -> float:
    start = max(0.0, float(settings.epsilon))
    end = max(0.0, min(float(settings.epsilon_min), start))

    if start == 0.0:
        return 0.0

    if settings.episodes <= 1:
        return end

    fraction = episode / float(settings.episodes - 1)
    if end == 0.0:
        return max(0.0, start * (1.0 - fraction))

    return max(end, start * ((end / start) ** fraction))


def make_bins(features: tuple[str, ...], bins_per_feature: int) -> list[Any]:
    np = require_dependencies("numpy")["numpy"]
    return [
        np.linspace(FEATURE_RANGES[feature][0], FEATURE_RANGES[feature][1], bins_per_feature - 1)
        for feature in features
    ]


def discretize_state(obs: Any, bins: list[Any]) -> tuple[int, ...]:
    np = require_dependencies("numpy")["numpy"]
    state: list[int] = []

    for value, edges in zip(obs, bins):
        bucket = int(np.digitize(float(value), edges))
        state.append(int(np.clip(bucket, 0, len(edges))))

    return tuple(state)


def rolling_mean(values: list[float], window: int = 10) -> list[float]:
    if not values:
        return []

    smoothed: list[float] = []
    for index in range(len(values)):
        start = max(0, index + 1 - window)
        smoothed.append(sum(values[start : index + 1]) / (index + 1 - start))
    return smoothed


def checkpoint_episodes(total_episodes: int, count: int = 5) -> set[int]:
    """Episode numbers (1-indexed) at which to snapshot the policy: every 1/count."""
    total = max(1, int(total_episodes))
    count = max(1, min(count, total))
    return {max(1, round(total * (i + 1) / count)) for i in range(count)}


def train_q_learning(
    settings: TrainSettings,
    reward_weights: dict[str, Any],
    progress_callback: Callable[[int, int, list[float]], None] | None = None,
    label: str = "Current reward",
    checkpoint_callback: Callable[[int, int, TrainingResult], None] | None = None,
) -> TrainingResult:
    np = require_dependencies("numpy")["numpy"]
    seed_everything(settings.seed)

    env = make_env()
    env.action_space.seed(settings.seed)
    bins = make_bins(settings.observation_features, settings.q_bins_per_feature)
    q_shape = (
        tuple(settings.q_bins_per_feature for _ in settings.observation_features)
        + (len(settings.action_forces),)
    )
    q_table = np.zeros(q_shape, dtype=np.float32)
    checkpoints = checkpoint_episodes(settings.episodes) if checkpoint_callback else set()

    returns: list[float] = []
    env_returns: list[float] = []
    episode_lengths: list[int] = []

    for episode in range(settings.episodes):
        obs = reset_env(env, settings, settings.seed + episode)
        agent_obs = observation_function(
            obs,
            settings.observation_features,
            settings.animal_position,
        )
        state = discretize_state(agent_obs, bins)
        epsilon = epsilon_for_episode(settings, episode)
        total_reward = 0.0
        total_env_reward = 0.0

        for step in range(settings.max_steps):
            if random.random() < epsilon:
                action = random.randrange(len(settings.action_forces))
            else:
                action = int(np.argmax(q_table[state]))

            action_force = action_function(action, settings.action_forces)
            next_obs, env_reward, terminated, truncated, _ = step_cartpole_with_force(
                env,
                action_force,
                settings.terminate_on_angle,
            )
            terminated = apply_animal_contact_termination(next_obs, terminated, settings)
            done = bool(terminated or truncated)
            shaped_reward = reward_function(
                obs,
                action,
                action_force,
                next_obs,
                float(env_reward),
                bool(terminated),
                bool(truncated),
                reward_weights,
            )

            next_agent_obs = observation_function(
                next_obs,
                settings.observation_features,
                settings.animal_position,
            )
            next_state = discretize_state(next_agent_obs, bins)
            best_next_q = 0.0 if done else float(np.max(q_table[next_state]))
            target = shaped_reward + settings.gamma * best_next_q
            q_table[state + (action,)] += settings.learning_rate * (
                target - float(q_table[state + (action,)])
            )

            obs = next_obs
            state = next_state
            total_reward += shaped_reward
            total_env_reward += float(env_reward)

            if done:
                episode_lengths.append(step + 1)
                break
        else:
            episode_lengths.append(settings.max_steps)

        returns.append(total_reward)
        env_returns.append(total_env_reward)

        if progress_callback is not None:
            progress_callback(episode + 1, settings.episodes, list(returns))

        if checkpoint_callback is not None and (episode + 1) in checkpoints:
            snapshot = TrainingResult(
                algorithm="Q-learning",
                returns=list(returns),
                env_returns=list(env_returns),
                episode_lengths=list(episode_lengths),
                policy={"q_table": q_table.copy(), "bins": bins},
                settings=settings,
                reward_weights=dict(reward_weights),
                label=label,
            )
            checkpoint_callback(episode + 1, settings.episodes, snapshot)

    env.close()

    return TrainingResult(
        algorithm="Q-learning",
        returns=returns,
        env_returns=env_returns,
        episode_lengths=episode_lengths,
        policy={"q_table": q_table, "bins": bins},
        settings=settings,
        reward_weights=dict(reward_weights),
        label=label,
    )


class ReplayBuffer:
    def __init__(self, capacity: int = 2_000) -> None:
        self.items: deque[tuple[Any, int, float, Any, bool]] = deque(maxlen=capacity)

    def add(self, obs: Any, action: int, reward: float, next_obs: Any, done: bool) -> None:
        self.items.append((obs, action, reward, next_obs, done))

    def sample(self, batch_size: int) -> list[tuple[Any, int, float, Any, bool]]:
        return random.sample(self.items, batch_size)

    def __len__(self) -> int:
        return len(self.items)


def make_q_network(input_size: int, hidden_size: int, output_size: int) -> Any:
    torch_modules = require_dependencies("torch")
    torch = torch_modules["torch"]
    nn = torch.nn

    return nn.Sequential(
        nn.Linear(input_size, hidden_size),
        nn.ReLU(),
        nn.Linear(hidden_size, hidden_size),
        nn.ReLU(),
        nn.Linear(hidden_size, output_size),
    )


def train_dqn(
    settings: TrainSettings,
    reward_weights: dict[str, Any],
    progress_callback: Callable[[int, int, list[float]], None] | None = None,
    label: str = "Current reward",
    checkpoint_callback: Callable[[int, int, TrainingResult], None] | None = None,
) -> TrainingResult:
    modules = require_dependencies("numpy", "torch")
    np = modules["numpy"]
    torch = modules["torch"]
    nn = torch.nn
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.set_num_threads(max(1, min(2, torch.get_num_threads())))

    seed_everything(settings.seed)
    env_count = max(1, int(settings.parallel_envs))
    envs = [make_env() for _ in range(env_count)]
    for index, env in enumerate(envs):
        env.action_space.seed(settings.seed + index)
    checkpoints = checkpoint_episodes(settings.episodes) if checkpoint_callback else set()

    obs_size = len(settings.observation_features)
    action_size = len(settings.action_forces)

    model = make_q_network(obs_size, settings.hidden_size, action_size).to(device)
    target_model = make_q_network(obs_size, settings.hidden_size, action_size).to(device)
    target_model.load_state_dict(model.state_dict())
    optimizer = torch.optim.Adam(model.parameters(), lr=settings.learning_rate)
    loss_fn = nn.SmoothL1Loss()
    replay = ReplayBuffer()

    returns: list[float] = []
    env_returns: list[float] = []
    episode_lengths: list[int] = []
    update_count = 0
    global_step = 0

    observations = [
        reset_env(env, settings, settings.seed + env_index)
        for env_index, env in enumerate(envs)
    ]
    agent_observations = [
        observation_function(obs, settings.observation_features, settings.animal_position)
        for obs in observations
    ]
    running_returns = [0.0 for _ in envs]
    running_env_returns = [0.0 for _ in envs]
    running_lengths = [0 for _ in envs]

    def optimize_once() -> None:
        nonlocal update_count

        if len(replay) < settings.batch_size:
            return

        batch = replay.sample(settings.batch_size)
        obs_batch = torch.tensor(
            np.array([item[0] for item in batch]),
            dtype=torch.float32,
            device=device,
        )
        action_batch = torch.tensor(
            [item[1] for item in batch],
            dtype=torch.int64,
            device=device,
        ).unsqueeze(1)
        reward_batch = torch.tensor(
            [item[2] for item in batch],
            dtype=torch.float32,
            device=device,
        )
        next_obs_batch = torch.tensor(
            np.array([item[3] for item in batch]),
            dtype=torch.float32,
            device=device,
        )
        done_batch = torch.tensor(
            [item[4] for item in batch],
            dtype=torch.float32,
            device=device,
        )

        q_values = model(obs_batch).gather(1, action_batch).squeeze(1)
        with torch.no_grad():
            next_q_values = target_model(next_obs_batch).max(dim=1).values
            targets = reward_batch + settings.gamma * (1.0 - done_batch) * next_q_values

        loss = loss_fn(q_values, targets)
        optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=10.0)
        optimizer.step()
        update_count += 1

    while len(returns) < settings.episodes:
        epsilon = epsilon_for_episode(settings, len(returns))
        with torch.no_grad():
            obs_tensor = torch.tensor(
                np.array(agent_observations),
                dtype=torch.float32,
                device=device,
            )
            greedy_actions = (
                torch.argmax(model(obs_tensor), dim=1)
                .cpu()
                .numpy()
                .astype(int)
                .tolist()
            )

        for env_index, env in enumerate(envs):
            if len(returns) >= settings.episodes:
                break

            if random.random() < epsilon:
                action = random.randrange(action_size)
            else:
                action = greedy_actions[env_index]

            obs = observations[env_index]
            agent_obs = agent_observations[env_index]
            action_force = action_function(action, settings.action_forces)
            next_obs, env_reward, terminated, _, _ = step_cartpole_with_force(
                env,
                action_force,
                settings.terminate_on_angle,
            )
            terminated = apply_animal_contact_termination(next_obs, terminated, settings)
            running_lengths[env_index] += 1
            truncated = running_lengths[env_index] >= settings.max_steps
            done = bool(terminated or truncated)
            next_agent_obs = observation_function(
                next_obs,
                settings.observation_features,
                settings.animal_position,
            )
            shaped_reward = reward_function(
                obs,
                action,
                action_force,
                next_obs,
                float(env_reward),
                bool(terminated),
                bool(truncated),
                reward_weights,
            )
            replay.add(agent_obs, action, shaped_reward, next_agent_obs, done)

            running_returns[env_index] += shaped_reward
            running_env_returns[env_index] += float(env_reward)
            global_step += 1

            if global_step % settings.update_every == 0:
                optimize_once()

            if done:
                returns.append(running_returns[env_index])
                env_returns.append(running_env_returns[env_index])
                episode_lengths.append(running_lengths[env_index])

                if len(returns) % settings.target_update == 0:
                    target_model.load_state_dict(model.state_dict())

                if progress_callback is not None:
                    progress_callback(len(returns), settings.episodes, list(returns))

                if checkpoint_callback is not None and len(returns) in checkpoints:
                    snapshot = TrainingResult(
                        algorithm="DQN",
                        returns=list(returns),
                        env_returns=list(env_returns),
                        episode_lengths=list(episode_lengths),
                        policy={
                            "model": model,
                            "updates": update_count,
                            "parallel_envs": env_count,
                            "device": str(device),
                        },
                        settings=settings,
                        reward_weights=dict(reward_weights),
                        label=label,
                    )
                    checkpoint_callback(len(returns), settings.episodes, snapshot)

                reset_seed = settings.seed + env_count + len(returns) + env_index
                observations[env_index] = reset_env(env, settings, reset_seed)
                agent_observations[env_index] = observation_function(
                    observations[env_index],
                    settings.observation_features,
                    settings.animal_position,
                )
                running_returns[env_index] = 0.0
                running_env_returns[env_index] = 0.0
                running_lengths[env_index] = 0
            else:
                observations[env_index] = next_obs
                agent_observations[env_index] = next_agent_obs

        optimize_once()

    target_model.load_state_dict(model.state_dict())
    for env in envs:
        env.close()

    return TrainingResult(
        algorithm="DQN",
        returns=returns,
        env_returns=env_returns,
        episode_lengths=episode_lengths,
        policy={
            "model": model,
            "updates": update_count,
            "parallel_envs": env_count,
            "device": str(device),
        },
        settings=settings,
        reward_weights=dict(reward_weights),
        label=label,
    )


def train_agent(
    settings: TrainSettings,
    reward_weights: dict[str, Any],
    progress_callback: Callable[[int, int, list[float]], None] | None = None,
    label: str = "Current reward",
    checkpoint_callback: Callable[[int, int, TrainingResult], None] | None = None,
) -> TrainingResult:
    if settings.algorithm == "Q-learning":
        return train_q_learning(settings, reward_weights, progress_callback, label, checkpoint_callback)
    return train_dqn(settings, reward_weights, progress_callback, label, checkpoint_callback)


def choose_action_for_result(result: TrainingResult, obs: Any) -> int:
    np = require_dependencies("numpy")["numpy"]
    agent_obs = observation_function(
        obs,
        result.settings.observation_features,
        result.settings.animal_position,
    )

    if result.algorithm == "Q-learning":
        q_table = result.policy["q_table"]
        bins = result.policy["bins"]
        state = discretize_state(agent_obs, bins)
        return int(np.argmax(q_table[state]))

    torch = require_dependencies("torch")["torch"]
    model = result.policy["model"]
    model.eval()
    model_device = next(model.parameters()).device
    with torch.no_grad():
        obs_tensor = torch.tensor(agent_obs, dtype=torch.float32, device=model_device).unsqueeze(0)
        return int(torch.argmax(model(obs_tensor), dim=1).item())


def append_fall_animation(
    env: Any,
    frames: list[Any],
    frame_limit: int | None,
    max_fall_frames: int = 120,
) -> None:
    """Continue the visualization after failure without changing the episode score."""
    base_env = env.unwrapped
    x, _, theta, theta_dot = [float(value) for value in base_env.state]

    if abs(theta) < 0.02:
        direction = theta_dot if abs(theta_dot) > 0.001 else 1.0
        theta = math.copysign(0.02, direction)

    for _ in range(max_fall_frames):
        if frame_limit is not None and len(frames) >= frame_limit:
            break

        angular_acceleration = (base_env.gravity / base_env.length) * math.sin(theta)
        theta_dot = (theta_dot + base_env.tau * angular_acceleration) * 0.995
        theta += base_env.tau * theta_dot

        fall_state = base_env.state.copy()
        fall_state[:] = (x, 0.0, theta, theta_dot)
        base_env.state = fall_state
        frames.append(env.render())

        if abs(theta) >= math.pi * 0.95:
            break


def evaluate_policy(
    result: TrainingResult,
    seed: int,
    render: bool = False,
    sleep_limit: int | None = None,
) -> tuple[float, float, int, list[Any]]:
    env = make_env(render=render)
    obs = reset_env(env, result.settings, seed)
    total_reward = 0.0
    total_env_reward = 0.0
    frames: list[Any] = []

    for step in range(result.settings.max_steps):
        if render:
            frame = env.render()
            frames.append(frame)

        action = choose_action_for_result(result, obs)
        action_force = action_function(action, result.settings.action_forces)
        next_obs, env_reward, terminated, truncated, _ = step_cartpole_with_force(
            env,
            action_force,
            result.settings.terminate_on_angle,
        )
        terminated = apply_animal_contact_termination(next_obs, terminated, result.settings)
        shaped_reward = reward_function(
            obs,
            action,
            action_force,
            next_obs,
            float(env_reward),
            bool(terminated),
            bool(truncated),
            result.reward_weights,
        )
        total_reward += shaped_reward
        total_env_reward += float(env_reward)
        obs = next_obs

        if terminated:
            if render:
                append_fall_animation(env, frames, sleep_limit)
            env.close()
            return total_reward, total_env_reward, step + 1, frames

        if truncated:
            env.close()
            return total_reward, total_env_reward, step + 1, frames

        if sleep_limit is not None and len(frames) >= sleep_limit:
            break

    env.close()
    return total_reward, total_env_reward, result.settings.max_steps, frames


def make_learning_curve(results: list[TrainingResult]) -> Any:
    modules = require_dependencies("matplotlib.pyplot")
    plt = modules["matplotlib.pyplot"]

    figure, axes = plt.subplots(1, 2, figsize=(10, 3.5))

    for result in results:
        episodes = list(range(1, len(result.returns) + 1))
        axes[0].plot(
            episodes,
            rolling_mean(result.returns),
            label=f"{result.label}: shaped",
            linewidth=2,
        )
        axes[1].plot(
            episodes,
            rolling_mean(result.env_returns),
            label=f"{result.label}: env",
            linewidth=2,
        )

    axes[0].set_title("Reward the agent learned from")
    axes[0].set_xlabel("Episode")
    axes[0].set_ylabel("Rolling return")
    axes[1].set_title("CartPole score")
    axes[1].set_xlabel("Episode")
    axes[1].set_ylabel("Rolling score")

    for axis in axes:
        axis.grid(True, alpha=0.25)
        axis.legend()

    figure.tight_layout()
    return figure


def policy_value_grid(
    result: TrainingResult,
    cart_position: float,
    cart_velocity: float,
    resolution: int = 81,
) -> tuple[Any, Any, Any, Any]:
    """Evaluate both actions across an angle/angular-velocity state slice."""
    np = require_dependencies("numpy")["numpy"]
    angles = np.linspace(-0.2095, 0.2095, resolution)
    angular_velocities = np.linspace(-3.5, 3.5, resolution)
    action_count = len(result.settings.action_forces)
    q_values = np.zeros((resolution, resolution, action_count), dtype=np.float32)

    if result.algorithm == "Q-learning":
        q_table = result.policy["q_table"]
        bins = result.policy["bins"]
        for row, angular_velocity in enumerate(angular_velocities):
            for column, angle in enumerate(angles):
                agent_obs = observation_function(
                    (cart_position, cart_velocity, angle, angular_velocity),
                    result.settings.observation_features,
                    result.settings.animal_position,
                )
                state = discretize_state(agent_obs, bins)
                q_values[row, column] = q_table[state]
    else:
        torch = require_dependencies("torch")["torch"]
        angle_grid, angular_velocity_grid = np.meshgrid(
            angles,
            angular_velocities,
        )
        states = np.column_stack(
            (
                np.full(angle_grid.size, cart_position),
                np.full(angle_grid.size, cart_velocity),
                angle_grid.ravel(),
                angular_velocity_grid.ravel(),
            )
        )
        agent_states = np.array(
            [
                observation_function(
                    state,
                    result.settings.observation_features,
                    result.settings.animal_position,
                )
                for state in states
            ],
            dtype=np.float32,
        )
        model = result.policy["model"]
        model.eval()
        with torch.no_grad():
            q_values = (
                model(torch.tensor(agent_states, dtype=torch.float32))
                .cpu()
                .numpy()
                .reshape(resolution, resolution, action_count)
            )

    best_action_indices = np.argmax(q_values, axis=2)
    action_forces = np.array(result.settings.action_forces, dtype=np.float32)
    preferred_forces = action_forces[best_action_indices]
    best_value = np.max(q_values, axis=2)
    return angles, angular_velocities, preferred_forces, best_value


def make_policy_value_figure(
    result: TrainingResult,
    cart_position: float,
    cart_velocity: float,
) -> Any:
    modules = require_dependencies("matplotlib.pyplot")
    np = require_dependencies("numpy")["numpy"]
    plt = modules["matplotlib.pyplot"]
    angles, angular_velocities, preferred_forces, best_value = policy_value_grid(
        result,
        cart_position,
        cart_velocity,
    )

    figure, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    extent = [
        math.degrees(float(angles[0])),
        math.degrees(float(angles[-1])),
        float(angular_velocities[0]),
        float(angular_velocities[-1]),
    ]
    force_limit = max(float(np.max(np.abs(result.settings.action_forces))), 0.001)

    action_image = axes[0].imshow(
        preferred_forces,
        origin="lower",
        aspect="auto",
        extent=extent,
        cmap="coolwarm",
        vmin=-force_limit,
        vmax=force_limit,
        interpolation="nearest" if result.algorithm == "Q-learning" else "bilinear",
    )
    if float(np.min(preferred_forces)) < 0.0 < float(np.max(preferred_forces)):
        axes[0].contour(
            np.degrees(angles),
            angular_velocities,
            preferred_forces,
            levels=[0.0],
            colors="black",
            linewidths=1.0,
        )
    axes[0].set_title("Preferred force")
    axes[0].set_xlabel("Pole angle (degrees)")
    axes[0].set_ylabel("Pole angular velocity")
    action_colorbar = figure.colorbar(action_image, ax=axes[0])
    action_colorbar.set_label("Cart force")

    value_image = axes[1].imshow(
        best_value,
        origin="lower",
        aspect="auto",
        extent=extent,
        cmap="viridis",
        interpolation="nearest" if result.algorithm == "Q-learning" else "bilinear",
    )
    axes[1].set_title("Best predicted value")
    axes[1].set_xlabel("Pole angle (degrees)")
    axes[1].set_ylabel("Pole angular velocity")
    value_colorbar = figure.colorbar(value_image, ax=axes[1])
    value_colorbar.set_label("max Q(state, action)")

    figure.suptitle(
        f"{result.algorithm} at cart x={cart_position:.2f}, velocity={cart_velocity:.2f}"
    )
    figure.tight_layout()
    return figure


def summarize_result(result: TrainingResult) -> dict[str, float | int | str]:
    tail = max(1, min(20, len(result.returns)))
    return {
        "Run": result.label,
        "Algorithm": result.algorithm,
        "Episodes": len(result.returns),
        "Mean shaped reward": round(sum(result.returns[-tail:]) / tail, 2),
        "Mean CartPole score": round(sum(result.env_returns[-tail:]) / tail, 2),
        "Best CartPole score": round(max(result.env_returns), 2),
        "Mean episode length": round(sum(result.episode_lengths[-tail:]) / tail, 2),
    }


def run_smoke_test() -> None:
    print("Running Q-learning smoke test...")
    q_settings = TrainSettings(
        algorithm="Q-learning",
        episodes=4,
        max_steps=60,
        learning_rate=0.2,
        gamma=0.95,
        epsilon=0.7,
        epsilon_min=0.05,
        seed=4,
        q_bins_per_feature=5,
    )
    q_result = train_q_learning(q_settings, DEFAULT_REWARD_WEIGHTS)
    q_eval = evaluate_policy(q_result, seed=104, render=False)

    print("Running DQN smoke test...")
    dqn_settings = TrainSettings(
        algorithm="DQN",
        episodes=4,
        max_steps=60,
        learning_rate=0.001,
        gamma=0.95,
        epsilon=0.8,
        epsilon_min=0.1,
        seed=8,
        batch_size=16,
        hidden_size=32,
        target_update=2,
        update_every=2,
        parallel_envs=2,
    )
    dqn_result = train_dqn(dqn_settings, DEFAULT_REWARD_WEIGHTS)
    dqn_eval = evaluate_policy(dqn_result, seed=108, render=False)

    print(
        "Smoke test passed.\n"
        f"  Q-learning episodes: {len(q_result.returns)}, eval score: {q_eval[1]:.0f}\n"
        f"  DQN episodes: {len(dqn_result.returns)}, eval score: {dqn_eval[1]:.0f}"
    )


def tutorial_enabled(st: Any) -> bool:
    return bool(st.session_state.get("tutorial_enabled", False))


def tutorial_step_index(st: Any) -> int:
    step = int(st.session_state.get("tutorial_step", 0))
    step = max(0, min(step, len(TUTORIAL_STEPS) - 1))
    st.session_state["tutorial_step"] = step
    return step


def active_tutorial_step(st: Any) -> dict[str, str] | None:
    if not tutorial_enabled(st):
        return None
    return TUTORIAL_STEPS[tutorial_step_index(st)]


def tutorial_target_for_step(index: int) -> str:
    index = max(0, min(index, len(TUTORIAL_STEPS) - 1))
    return TUTORIAL_STEPS[index]["target"]


def request_streamlit_rerun(st: Any) -> None:
    rerun = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if rerun is not None:
        rerun()


def set_app_stage(st: Any, stage: str) -> None:
    st.session_state["app_stage"] = stage
    st.session_state["scroll_to_top_pending"] = True
    request_streamlit_rerun(st)


def scroll_to_top_if_requested(st: Any) -> None:
    if not st.session_state.pop("scroll_to_top_pending", False):
        return
    st.html(
        """
        <script>
        function scrollToTop() {
          window.scrollTo({ top: 0, left: 0, behavior: "instant" });
          document.documentElement.scrollTop = 0;
          document.body.scrollTop = 0;
        }
        setTimeout(scrollToTop, 30);
        setTimeout(scrollToTop, 180);
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def render_rl_concepts_page(st: Any) -> None:
    """Interactive intro to RL fundamentals before the pendulum-specific work.

    A scrollable playground: the student plays a Wumpus-style grid game seeing
    only local observations, then trains an imitation agent and a reward-driven
    Q-learning agent from their own play and watches both replay.
    """
    st.title("Reinforcement learning, by playing")
    st.markdown(
        "Before the pendulum, get a feel for RL by *being* the agent. Play the game,"
        " then scroll down to train agents from how you played."
    )
    rl_concepts_component()

    back_column, next_column = st.columns(2)
    if back_column.button("Back", use_container_width=True):
        set_app_stage(st, "intro")
    if next_column.button(
        "Continue to the pendulum",
        type="primary",
        use_container_width=True,
        key="rl_concepts_continue",
    ):
        set_app_stage(st, "background")


def render_intro_page(st: Any) -> None:
    gif_bytes = intro_demo_gif(st)
    if gif_bytes:
        encoded = base64.b64encode(gif_bytes).decode("ascii")
        background = (
            "background-image: linear-gradient(90deg, rgba(15, 23, 42, 0.86), "
            "rgba(15, 23, 42, 0.32)), "
            f"url(data:image/gif;base64,{encoded});"
        )
    else:
        background = "background: linear-gradient(120deg, #172033, #285d62);"

    st.markdown(
        f"""
        <style>
        .intro-hero {{
            {background}
            background-size: cover;
            background-position: center;
            min-height: 68vh;
            border-radius: 8px;
            display: flex;
            align-items: flex-end;
            padding: clamp(1.4rem, 4vw, 3.5rem);
            color: white;
        }}
        .intro-copy {{
            max-width: 720px;
        }}
        .intro-copy h1 {{
            font-size: clamp(2.2rem, 6vw, 5rem);
            line-height: 0.96;
            margin: 0 0 0.8rem 0;
            letter-spacing: 0;
        }}
        .intro-copy p {{
            font-size: clamp(1rem, 1.6vw, 1.25rem);
            line-height: 1.45;
            margin: 0;
            max-width: 620px;
        }}
        .intro-start-button + div[data-testid="stButton"] > button {{
            min-height: 4.25rem;
            font-size: 1.15rem;
            font-weight: 800;
            border-radius: 8px;
        }}
        </style>
        <div class="intro-hero">
            <div class="intro-copy">
                <h1>Live RL Pendulum Lab</h1>
                <p>Use reinforcement learning to balance an inverted pendulum, then change the learning problem yourself.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, tutorial_column, skip_column, right = st.columns([0.7, 1.2, 1.2, 0.7])
    with tutorial_column:
        st.markdown('<span class="intro-start-button"></span>', unsafe_allow_html=True)
        if st.button("Start tutorial", type="primary", use_container_width=True):
            st.session_state["tutorial_enabled"] = True
            st.session_state["tutorial_step"] = 0
            set_app_stage(st, "rl_concepts")
    with skip_column:
        st.markdown('<span class="intro-start-button"></span>', unsafe_allow_html=True)
        if st.button("Skip to activity", use_container_width=True):
            st.session_state["tutorial_enabled"] = False
            set_app_stage(st, "lab")


def render_background_page(st: Any) -> None:
    st.title("Background")
    st.markdown(
        """
        The inverted pendulum is a common platform used for research in controls and machine learning.
        The problem consists of figuring out how to make the pendulum balance itself for as long as possible.

        We are going to learn how to use reinforcement learning to balance the pendulum as our introduction to RL.

        Reinforcement learning is used to solve elaborate problems with edge cases by allowing algorithms to learn how to solve them on their own.
        For instance, walking is very difficult to describe fully in code, so we let algorithms learn how to figure it out on their own in simulation.
        """
    )
    st.subheader("Three Things To Design")
    columns = st.columns(3)
    with columns[0]:
        st.markdown("**Observations**")
        st.write("What your agent can see when interacting with the environment.")
    with columns[1]:
        st.markdown("**Actions**")
        st.write("What your agent can do based on what it sees.")
    with columns[2]:
        st.markdown("**Reward Function**")
        st.write("How you teach your agent what to do based on what it sees.")

    st.caption("We will go over each one in depth.")
    render_grid_game_bridge(
        st,
        title="Same notebook, different world",
        body=(
            "In the grid game, a situation was the tiny view around you, the actions were "
            "up/down/left/right, and reward nudged the notebook entry for that move. "
            "For the pendulum, the notebook idea is the same: observation numbers replace "
            "the tiny grid view, force choices replace arrows, and reward still does the teaching."
        ),
    )
    background_checkin = render_reflective_checkin(
        st,
        key="background_design_parts",
        title="Map the loop to this lab",
        prompt="For this pendulum, name one observation, one action, and one reward signal.",
        placeholder="Example: observation = pole angle; action = push right; reward = +1 for staying balanced.",
        required=True,
    )
    left, center, right = st.columns([1, 1.2, 1])
    with center:
        if st.button(
            "Continue",
            type="primary",
            use_container_width=True,
            disabled=not background_checkin["complete"],
        ):
            set_app_stage(st, "pendulum_intro")


# ---------------------------------------------------------------------------
# Precomputed demo assets: the fixed (non-interactive) slide demos are trained
# once via `--precompute` and saved to disk so the slide pages load instantly.
# ---------------------------------------------------------------------------
DEMO_ASSETS_PATH = Path(__file__).resolve().parent / "assets" / "demo_assets.pkl"


def figure_to_png_bytes(figure: Any) -> bytes:
    """Render a matplotlib figure to PNG bytes so it can be cached on disk."""
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", dpi=110, bbox_inches="tight")
    return buffer.getvalue()


def load_demo_assets(st: Any) -> dict[str, Any]:
    """Load the precomputed demo asset bundle from disk once per session."""
    if "demo_assets" in st.session_state:
        return st.session_state["demo_assets"]
    assets: dict[str, Any] = {}
    if DEMO_ASSETS_PATH.exists():
        try:
            with open(DEMO_ASSETS_PATH, "rb") as handle:
                assets = pickle.load(handle)
        except Exception:
            assets = {}
    st.session_state["demo_assets"] = assets
    return assets


def build_observation_demo_run(
    *,
    label: str,
    features: tuple[str, ...],
    seed: int,
    initial_state: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
) -> dict[str, Any]:
    settings = TrainSettings(
        algorithm="Q-learning",
        episodes=DEMO_EPISODES,
        max_steps=DEMO_MAX_STEPS,
        learning_rate=DEMO_LEARNING_RATE,
        gamma=DEMO_GAMMA,
        epsilon=DEMO_EPSILON,
        epsilon_min=DEMO_EPSILON_MIN,
        seed=seed,
        q_bins_per_feature=DEMO_Q_BINS,
        observation_features=features,
        initial_state=initial_state,
    )
    result = train_q_learning(settings, OBSERVATION_DEMO_REWARD_WEIGHTS, label=label)
    shaped, env_score, length, frames = evaluate_policy(
        result,
        seed=seed + 200,
        render=True,
        sleep_limit=180,
    )
    return {
        "label": label,
        "features": features,
        "score": env_score,
        "length": length,
        "shaped": shaped,
        "gif_bytes": frames_to_gif(frames, fps=30),
    }


def _build_observation_demo() -> dict[str, Any]:
    return {
        "full": build_observation_demo_run(
            label="Full observations",
            features=DEFAULT_OBSERVATION_FEATURES,
            seed=31,
        ),
        "limited": build_observation_demo_run(
            label="No pole angle or pole spin",
            features=("cart_position", "cart_velocity"),
            seed=31,
            # Start slightly tilted. Without pole angle/spin observations the
            # agent cannot tell which way to correct, so it fails more visibly.
            initial_state=(0.0, 0.0, 0.06, 0.0),
        ),
    }


def observation_demo_cache(st: Any) -> dict[str, Any]:
    assets = load_demo_assets(st)
    if "observation_demo" in assets:
        return dict(assets["observation_demo"])
    if "observation_demo_cache" not in st.session_state:
        st.session_state["observation_demo_cache"] = _build_observation_demo()
    return dict(st.session_state["observation_demo_cache"])


def build_controlled_demo_run(
    *,
    features: tuple[str, ...],
    action_forces: tuple[float, ...],
    seed: int,
    reward_weights: dict[str, Any] | None = None,
    episodes: int | None = None,
    q_bins: int | None = None,
    learning_rate: float | None = None,
    epsilon_min: float | None = None,
    terminate_on_angle: bool = True,
) -> dict[str, Any]:
    settings = TrainSettings(
        algorithm="Q-learning",
        episodes=episodes if episodes is not None else DEMO_EPISODES,
        max_steps=DEMO_MAX_STEPS,
        learning_rate=learning_rate if learning_rate is not None else DEMO_LEARNING_RATE,
        gamma=DEMO_GAMMA,
        epsilon=DEMO_EPSILON,
        epsilon_min=epsilon_min if epsilon_min is not None else DEMO_EPSILON_MIN,
        seed=seed,
        q_bins_per_feature=q_bins if q_bins is not None else DEMO_Q_BINS,
        observation_features=features,
        action_forces=action_forces,
        # Always start the pole perfectly upright and centered for the interactive
        # demos so students see a consistent starting state, not a random tilt.
        initial_state=(0.0, 0.0, 0.0, 0.0),
        # The lazy-agent demo turns this off so the episode runs full length even
        # if the pole falls, removing the agent's incentive to keep balancing.
        terminate_on_angle=terminate_on_angle,
    )
    result = train_q_learning(
        settings, reward_weights or CONTROLLED_DEMO_REWARD_WEIGHTS, label="Demo"
    )
    _, env_score, _, frames = evaluate_policy(
        result,
        seed=seed + 200,
        render=True,
        sleep_limit=180,
    )
    # When the episode never ends early (lazy-agent demo), step count no longer
    # tells us whether the pole is up. Measure how much of an evaluation episode
    # the pole actually stays near upright.
    upright_fraction = _measure_upright_fraction(result, seed=seed + 311)
    return {
        "version": CONTROLLED_DEMO_VERSION,
        "features": features,
        "action_forces": action_forces,
        "score": env_score,
        "upright_fraction": upright_fraction,
        "gif_bytes": frames_to_gif(frames, fps=30),
        # Per-episode total shaped reward (what the agent is optimizing), for the
        # reward-over-training curve.
        "reward_curve": list(result.returns),
        # Per-episode survival length, kept for reference.
        "episode_lengths": list(result.episode_lengths),
    }


def _render_policy_no_terminate(result: TrainingResult, seed: int) -> tuple[bytes, float]:
    """Render a trained policy in an environment where the pole is allowed to
    fall without ending the episode, and report its upright fraction. Lets us
    show a good agent and a lazy agent side by side in the same world.

    Both start from the same small tilt so the difference is obvious right away:
    the good agent corrects it and holds; the lazy agent lets it topple."""
    import copy

    eval_result = copy.copy(result)
    eval_settings = copy.copy(result.settings)
    eval_settings.terminate_on_angle = False
    # A visible starting lean (~9 degrees) so the contrast shows from frame one.
    eval_settings.initial_state = (0.0, 0.0, 0.16, 0.0)
    eval_result.settings = eval_settings
    _, _, _, frames = evaluate_policy(eval_result, seed=seed, render=True, sleep_limit=200)
    upright = _measure_upright_fraction(eval_result, seed=seed)
    return (frames_to_gif(frames, fps=30) if frames else b""), upright


def build_lazy_comparison(*, seed: int = 21) -> dict[str, Any]:
    """For the lazy-agent step: train a good (+1 alive) policy and a lazy
    (+10 alive) policy, then render BOTH in the same fall-allowed environment so
    students can directly compare a balancing agent with one that gives up."""
    base_penalties = [
        {"signal": "cart_position", "factor": -1.0, "transform": "abs", "scale": "unit"},
        {"signal": "pole_angular_velocity", "factor": -1.0, "transform": "abs", "scale": "unit"},
    ]
    good_reward = {"reward_terms": [{"signal": "alive", "factor": 1.0, "scale": "unit"}] + base_penalties}
    lazy_reward = {"reward_terms": [{"signal": "alive", "factor": 10.0, "scale": "unit"}] + base_penalties}

    def train(reward: dict[str, Any], terminate: bool) -> TrainingResult:
        settings = TrainSettings(
            algorithm="Q-learning",
            episodes=REWARD_LESSON_EPISODES,
            max_steps=DEMO_MAX_STEPS,
            learning_rate=REWARD_LESSON_LEARNING_RATE,
            gamma=DEMO_GAMMA,
            epsilon=DEMO_EPSILON,
            epsilon_min=REWARD_LESSON_EPSILON_MIN,
            seed=seed,
            q_bins_per_feature=REWARD_LESSON_Q_BINS,
            observation_features=DEFAULT_OBSERVATION_FEATURES,
            action_forces=ACTION_PRESETS["Standard left/right"],
            initial_state=(0.0, 0.0, 0.0, 0.0),
            terminate_on_angle=terminate,
        )
        return train_q_learning(settings, reward, label="Demo")

    # Good agent learned WITH the fall cutoff (step 2); lazy agent learned with
    # the cutoff removed and a huge alive bonus (step 3).
    good_result = train(good_reward, True)
    lazy_result = train(lazy_reward, False)
    good_gif, good_up = _render_policy_no_terminate(good_result, seed + 200)
    lazy_gif, lazy_up = _render_policy_no_terminate(lazy_result, seed + 200)
    return {
        "version": CONTROLLED_DEMO_VERSION,
        "good_gif": good_gif,
        "good_upright": good_up,
        "good_curve": list(good_result.returns),
        "lazy_gif": lazy_gif,
        "lazy_upright": lazy_up,
        "lazy_curve": list(lazy_result.returns),
    }


# Bump when the lazy-comparison rendering/measurement logic changes, so stale
# cached results (e.g. a lazy clip mislabeled as 100% upright) are rebuilt.
LAZY_COMPARISON_VERSION = "lazy-cmp-v3-curves"


def cached_lazy_comparison(st: Any, *, seed: int = 21) -> dict[str, Any]:
    cache = st.session_state.setdefault("controlled_lazy_comparison_cache", {})
    key = (CONTROLLED_DEMO_VERSION, LAZY_COMPARISON_VERSION, seed)
    if key not in cache:
        cache[key] = build_lazy_comparison(seed=seed)
    return dict(cache[key])


def _measure_upright_fraction(result: TrainingResult, seed: int) -> float:
    """Fraction of a (non-rendered) evaluation episode the pole stays near
    upright (|angle| < ~12 degrees). Useful when the episode does not end on a
    fall, so step count alone cannot tell balancing from doing nothing."""
    env = make_env(render=False)
    obs = reset_env(env, result.settings, seed)
    upright = 0
    steps = 0
    try:
        for _ in range(result.settings.max_steps):
            action = choose_action_for_result(result, obs)
            action_force = action_function(action, result.settings.action_forces)
            next_obs, _, terminated, truncated, _ = step_cartpole_with_force(
                env, action_force, result.settings.terminate_on_angle
            )
            theta = float(next_obs[2])
            if abs(theta) < 0.2095:  # ~12 degrees, the usual upright threshold
                upright += 1
            steps += 1
            obs = next_obs
            if terminated or truncated:
                break
    finally:
        env.close()
    return upright / steps if steps else 0.0


def cached_controlled_demo_run(
    st: Any,
    *,
    cache_name: str,
    features: tuple[str, ...],
    action_forces: tuple[float, ...],
    seed: int,
    reward_weights: dict[str, Any] | None = None,
    episodes: int | None = None,
    q_bins: int | None = None,
    learning_rate: float | None = None,
    epsilon_min: float | None = None,
    terminate_on_angle: bool = True,
) -> dict[str, Any]:
    cache = st.session_state.setdefault(cache_name, {})
    reward_key = json.dumps(reward_weights, sort_keys=True) if reward_weights else ""
    key = (
        CONTROLLED_DEMO_VERSION, features, action_forces, seed, reward_key,
        episodes, q_bins, learning_rate, epsilon_min, terminate_on_angle,
    )
    if key not in cache:
        cache[key] = build_controlled_demo_run(
            features=features,
            action_forces=action_forces,
            seed=seed,
            reward_weights=reward_weights,
            episodes=episodes,
            q_bins=q_bins,
            learning_rate=learning_rate,
            epsilon_min=epsilon_min,
            terminate_on_angle=terminate_on_angle,
        )
    return dict(cache[key])


ALL_OBSERVATION_FEATURES: tuple[str, ...] = (
    "cart_position",
    "cart_velocity",
    "pole_angle",
    "pole_angular_velocity",
)


def render_guided_prompt(
    st: Any,
    *,
    step_label: str,
    title: str,
    body: str,
    tone: str = "info",
) -> None:
    """Mission-style coaching card used on the observation/action demo pages."""
    st.markdown(
        f"""
        <div class="guided-prompt guided-prompt-{tone}">
            <div class="guided-step">{step_label}</div>
            <div class="guided-title">{title}</div>
            <div class="guided-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


GUIDED_PROMPT_STYLE = """
<style>
.guided-prompt {
    border: 1px solid #d0d5dd;
    border-left: 6px solid #2e90fa;
    border-radius: 10px;
    padding: 0.9rem 1.2rem;
    margin: 0.4rem 0 1rem;
    background: #f5faff;
}
.guided-prompt-success { border-left-color: #12b76a; background: #f0fdf4; }
.guided-prompt-warn { border-left-color: #f79009; background: #fffaf0; }
.guided-step {
    font-size: 0.8rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #1570cd;
}
.guided-title { font-size: 1.25rem; font-weight: 800; color: #101828; margin: 0.15rem 0 0.35rem; }
.guided-body { font-size: 1.05rem; line-height: 1.5; color: #344054; }
</style>
"""


GRID_GAME_BRIDGE_STYLE = """
<style>
.grid-bridge {
    border: 1px solid #bfdbfe;
    border-left: 6px solid #2563eb;
    border-radius: 10px;
    padding: 0.9rem 1.15rem;
    margin: 0.9rem 0 1.1rem;
    background: #eff6ff;
}
.grid-bridge-label {
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #1d4ed8;
}
.grid-bridge-title {
    font-size: 1.12rem;
    font-weight: 800;
    margin: 0.12rem 0 0.35rem;
    color: #0b1220;
}
.grid-bridge-body {
    font-size: 1.02rem;
    line-height: 1.5;
    color: #344054;
}
</style>
"""


def render_grid_game_bridge(st: Any, *, title: str, body: str) -> None:
    """Connect a pendulum concept back to the grid-game Q-learning notebook."""
    st.markdown(GRID_GAME_BRIDGE_STYLE, unsafe_allow_html=True)
    st.markdown(
        '<div class="grid-bridge">'
        '<div class="grid-bridge-label">Back to the grid game</div>'
        f'<div class="grid-bridge-title">{html.escape(title)}</div>'
        f'<div class="grid-bridge-body">{body}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


REFLECTIVE_CHECKIN_STYLE = """
<style>
.reflective-checkin {
    border: 1px solid #d0d5dd;
    border-left: 6px solid #12b76a;
    border-radius: 10px;
    padding: 0.9rem 1.2rem;
    margin: 0.8rem 0 1rem;
    background: #f7fdf9;
}
.reflective-checkin-label {
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #027a48;
}
.reflective-checkin-title {
    font-size: 1.18rem;
    font-weight: 800;
    color: #101828;
    margin: 0.15rem 0 0.35rem;
}
.reflective-checkin-prompt {
    font-size: 1.02rem;
    line-height: 1.5;
    color: #344054;
}
</style>
"""


def reflective_checkin_state_key(key: str, suffix: str) -> str:
    """Session-state key for check-ins that stays scoped to the caller."""
    safe_key = "".join(character if character.isalnum() or character in "_-" else "_" for character in str(key))
    safe_suffix = "".join(character if character.isalnum() or character in "_-" else "_" for character in str(suffix))
    return f"reflective_checkin_{safe_key}_{safe_suffix}"


def reflective_checkin_response(st: Any, key: str) -> dict[str, Any]:
    """Return the current session-only response for a reflective check-in."""
    choice = str(st.session_state.get(reflective_checkin_state_key(key, "choice"), ""))
    note = str(st.session_state.get(reflective_checkin_state_key(key, "note"), ""))
    return {
        "choice": choice,
        "note": note,
        "complete": bool(choice.strip() or note.strip()),
    }


def render_reflective_checkin(
    st: Any,
    *,
    key: str,
    title: str,
    prompt: str,
    label: str = "Reflect",
    choices: tuple[str, ...] = (),
    note_label: str = "What did you notice?",
    placeholder: str = "",
    help_text: str = "",
    required: bool = False,
) -> dict[str, Any]:
    """Render a reusable reflection card for lessons or lab sections.

    Responses are kept in Streamlit session state only. Mission submissions stay
    owned by `render_mission_explanations`.
    """
    st.markdown(REFLECTIVE_CHECKIN_STYLE, unsafe_allow_html=True)
    help_html = (
        f'<div class="reflective-checkin-prompt">{html.escape(str(help_text))}</div>'
        if help_text
        else ""
    )
    st.markdown(
        '<div class="reflective-checkin">'
        f'<div class="reflective-checkin-label">{html.escape(str(label))}</div>'
        f'<div class="reflective-checkin-title">{html.escape(str(title))}</div>'
        f'<div class="reflective-checkin-prompt">{html.escape(str(prompt))}</div>'
        f"{help_html}"
        "</div>",
        unsafe_allow_html=True,
    )

    if choices:
        choice_key = reflective_checkin_state_key(key, "choice")
        current_choice = st.session_state.get(choice_key)
        radio_index = list(choices).index(current_choice) if current_choice in choices else None
        st.radio(
            "Choose one",
            list(choices),
            index=radio_index,
            key=choice_key,
            horizontal=True,
            label_visibility="collapsed",
        )
    st.text_area(
        note_label,
        key=reflective_checkin_state_key(key, "note"),
        height=90,
        placeholder=placeholder,
    )
    response = reflective_checkin_response(st, key)
    if required and not response["complete"]:
        st.caption("Answer this check-in to continue.")
    return response


def render_pendulum_intro_page(st: Any) -> None:
    """Interactive 'meet the inverted pendulum' explainer before observations."""
    st.markdown(
        """
        <style>
        .pendulum-intro-lead {
            font-size: 1.22rem;
            line-height: 1.55;
            margin: 0.35rem 0 0.6rem;
            color: #243447;
        }
        .pendulum-intro-note {
            font-size: 1.05rem;
            line-height: 1.5;
            color: #475467;
            margin: 0.2rem 0 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("Meet the inverted pendulum")
    st.markdown(
        """
        <div class="pendulum-intro-lead">
            This is the world the agent lives in: a cart on a track with a pole
            balanced on top.
        </div>
        <div class="pendulum-intro-note">
            <strong>Use the ← and → arrow keys to push the cart. Drag the pole with
            your mouse to swing it.</strong> The agent never sees the picture &mdash;
            it only sees the four numbers on the right: position in meters,
            velocity in meters per second, pole angle in radians, and pole angular
            velocity in radians per second. Notice how pushing the cart also tips the pole.
            Play until the numbers make sense, then continue.
        </div>
        """,
        unsafe_allow_html=True,
    )

    pendulum_playground_component()
    render_grid_game_bridge(
        st,
        title="The tiny grid view becomes four physics numbers",
        body=(
            "The grid agent only saw nearby squares. The pendulum agent only sees the numbers "
            "we give it: cart position, cart velocity, pole angle, and pole angular velocity. "
            "Those numbers are the situation key for the Q-table notebook."
        ),
    )

    pendulum_checkin = render_reflective_checkin(
        st,
        key="pendulum_state_variables",
        title="Connect the picture to the numbers",
        prompt=(
            "When the pole starts leaning right, which number tells you the lean, "
            "and which number tells you whether it is still rotating?"
        ),
        placeholder="Angle tells me... angular velocity tells me...",
        required=True,
    )

    back_column, next_column = st.columns(2)
    if back_column.button("Back", use_container_width=True):
        set_app_stage(st, "background")
    if next_column.button(
        "Continue",
        type="primary",
        use_container_width=True,
        disabled=not pendulum_checkin["complete"],
    ):
        set_app_stage(st, "observation_demo")


def render_observation_slideshow_page(st: Any) -> None:
    st.markdown(
        """
        <style>
        .observation-slide-lead {
            font-size: 1.28rem;
            line-height: 1.55;
            margin: 0.35rem 0 1rem;
            color: #243447;
        }
        .observation-slide-note {
            font-size: 1.18rem;
            line-height: 1.55;
            margin: 1rem 0 1.25rem;
            color: #344054;
        }
        .observation-slide-features {
            font-size: 1.05rem;
            line-height: 1.45;
            margin: 0 0 0.8rem;
            color: #475467;
        }
        .observation-slide-features.demo-caption {
            min-height: 4.2rem;
        }
        .lab-snippet {
            border: 1px solid #d0d5dd;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0 1.25rem;
            background: #f9fafb;
        }
        .lab-snippet-title {
            font-size: 1.15rem;
            font-weight: 800;
            color: #182230;
            margin-bottom: 0.75rem;
        }
        .lab-snippet-row {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 0.8rem;
            align-items: center;
        }
        .lab-snippet-panel {
            min-height: 6rem;
            border: 1px dashed #98a2b3;
            border-radius: 8px;
            padding: 0.85rem;
            background: white;
        }
        .lab-snippet-label {
            font-size: 0.95rem;
            font-weight: 800;
            color: #475467;
            margin-bottom: 0.55rem;
        }
        .lab-chip {
            display: inline-block;
            border: 1px solid #98a2b3;
            border-radius: 999px;
            padding: 0.42rem 0.7rem;
            margin: 0.18rem;
            background: #ffffff;
            color: #182230;
            font-weight: 700;
            font-size: 0.95rem;
        }
        .lab-chip.selected {
            border-color: #2563eb;
            background: #eff6ff;
            color: #1d4ed8;
        }
        .snippet-arrow {
            color: #667085;
            font-size: 1.8rem;
            font-weight: 800;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("Observation Demo")
    st.markdown(
        """
        <div class="observation-slide-note">
            Observations are what the agent can see. If the agent cannot observe
            the pole angle or how fast the pole is rotating, it has to act from
            incomplete information.
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_grid_game_bridge(
        st,
        title="Observation means 'what row of the notebook am I in?'",
        body=(
            "In the grid game, the notebook row was something like 'spike on my right, "
            "gem above.' Here it is a bucketed version of the pendulum numbers. If the "
            "agent cannot see pole angle or pole spin, it is choosing from a notebook row "
            "that is missing the clues it needs."
        ),
    )

    with st.spinner("Training two small Q-learning agents for the observation demo..."):
        demo = observation_demo_cache(st)

    full_column, limited_column = st.columns(2)
    for column, key in ((full_column, "full"), (limited_column, "limited")):
        run = demo[key]
        with column:
            st.subheader(run["label"])
            features = ", ".join(OBSERVATION_LABELS[feature] for feature in run["features"])
            st.markdown(
                f'<div class="observation-slide-features demo-caption"><strong>Observations:</strong> {features}</div>',
                unsafe_allow_html=True,
            )
            if run["gif_bytes"]:
                st.image(run["gif_bytes"], width="stretch")

    st.markdown(
        """
        <div class="lab-snippet">
            <div class="lab-snippet-title">In the lab, students change observations by dragging them into the agent's observation box.</div>
            <div class="lab-snippet-row">
                <div class="lab-snippet-panel">
                    <div class="lab-snippet-label">Observation pool</div>
                    <span class="lab-chip">Cart position</span>
                    <span class="lab-chip">Cart velocity</span>
                    <span class="lab-chip">Pole angle</span>
                    <span class="lab-chip">Pole angular velocity</span>
                </div>
                <div class="snippet-arrow">→</div>
                <div class="lab-snippet-panel">
                    <div class="lab-snippet-label">Agent sees</div>
                    <span class="lab-chip selected">Cart position</span>
                    <span class="lab-chip selected">Pole angle</span>
                </div>
            </div>
        </div>
        <div class="observation-slide-lead">
            <strong>Both agents are trained the same way:</strong> same reward,
            same Q-learning notebook update, same episode budget. Only the observations
            &mdash; the notebook row keys &mdash; change.
        </div>
        <div class="observation-slide-note">
            Removing pole angle and pole spin usually changes the behavior
            dramatically because those observations tell the agent which way the
            pendulum is falling.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(GUIDED_PROMPT_STYLE, unsafe_allow_html=True)
    st.subheader("Experiment: what does the agent need to see?")
    st.markdown(
        '<div class="observation-slide-note">Same fixed Q-learning notebook update and the same reward'
        ' (<strong>cos(pole angle) + cos(cart position)</strong> &mdash; reward an upright pole'
        ' and a centered cart). The only thing you change is what the agent can observe.</div>',
        unsafe_allow_html=True,
    )

    observation_pool = [
        {"id": "cart_position", "label": OBSERVATION_LABELS["cart_position"], "group": "Cart"},
        {"id": "cart_velocity", "label": OBSERVATION_LABELS["cart_velocity"], "group": "Cart"},
        {"id": "pole_angle", "label": OBSERVATION_LABELS["pole_angle"], "group": "Pole"},
        {
            "id": "pole_angular_velocity",
            "label": OBSERVATION_LABELS["pole_angular_velocity"],
            "group": "Pole",
        },
    ]
    if st.session_state.get("observation_demo_builder_version") != "empty-v3":
        st.session_state["observation_demo_builder_features"] = []
        st.session_state["observation_demo_builder_touched"] = False
        st.session_state["observation_demo_builder_version"] = "empty-v3"

    # Track every observation combination the student has actually trained.
    runs_done: dict[frozenset[str], float] = st.session_state.setdefault(
        "observation_demo_runs_done", {}
    )
    trained_full = frozenset(ALL_OBSERVATION_FEATURES) in runs_done
    trained_without_angle = any(
        "pole_angle" not in combo and combo for combo in runs_done
    )
    trained_free = trained_full and trained_without_angle and len(runs_done) >= 3

    # Which step is the student currently on (drives the prompt and the check).
    if not trained_full:
        current_step = "full"
    elif not trained_without_angle:
        current_step = "without_angle"
    elif not trained_free:
        current_step = "free"
    else:
        current_step = "done"

    # Show the result of the last Train click and keep it on screen until the
    # next Train click overwrites it, so a "not yet" message stays put while the
    # student fixes their selection instead of flickering away.
    feedback = st.session_state.get("observation_demo_feedback")
    if feedback:
        tone = feedback.get("tone", "info")
        if tone == "success":
            st.success(feedback["text"])
        else:
            st.warning(feedback["text"])

    # Decide which guided step the student is on.
    observation_reflection_complete = False
    if not trained_full:
        render_guided_prompt(
            st,
            step_label="Step 1 of 3 · Give it everything",
            title="Drag in all four observations, then train.",
            body="Let the agent see cart position, cart velocity, pole angle, and pole spin."
            " <strong>Predict first:</strong> with full information, can it keep the pole up?"
            " Then press Train and watch.",
        )
    elif not trained_without_angle:
        render_guided_prompt(
            st,
            step_label="Step 2 of 3 · Take away an eye",
            title="Now remove pole angle and train again.",
            body="Drag <strong>pole angle</strong> back out so the agent can no longer see which"
            " way the pole is leaning. <strong>Predict first:</strong> will it still balance, or"
            " fall? Then train and compare.",
            tone="warn",
        )
    elif not trained_free:
        render_guided_prompt(
            st,
            step_label="Step 3 of 3 · Your own experiment",
            title="Try a different combination of your choosing.",
            body="Pick any mix you are curious about &mdash; maybe pole angle but no spin, or just"
            " the cart. <strong>Say out loud how you think it will behave</strong>, then train and"
            " see if your prediction was right.",
        )
    else:
        render_guided_prompt(
            st,
            step_label="Nice work",
            title="More observations is not always better.",
            body="You may have noticed something surprising: removing an observation sometimes"
            " makes the agent do <strong>better</strong>, not worse. Two reasons:<br><br>"
            "<strong>1. Size.</strong> Each observation you add multiplies the size of the"
            " Q-table notebook the agent has to fill in (with a 6-bin grid, 2 observations = 36 cells,"
            " but 4 observations = 1296). With the same training budget, more observations can"
            " mean each situation is visited less and learned worse &mdash; an extra signal can"
            " act like <strong>noise</strong>.<br><br>"
            "<strong>2. Some signals are harder to read patterns from.</strong> Pole angle and"
            " cart position both swing from positive to negative as they cross the center"
            " (upright pole, centered cart). The agent has to learn that a value and its"
            " mirror-image opposite call for <em>opposite</em> actions &mdash; lean right, push"
            " right; lean left, push left &mdash; and the bin grid splits those two sides right"
            " at the boundary. That sign-flipping pattern is trickier to pin down than a"
            " smoother, less symmetric signal.<br><br>"
            "<strong>3. One signal can stand in for another.</strong> For the simple goal of"
            " &lsquo;balance as long as possible,&rsquo; pole <em>velocity</em> is almost as"
            " useful as pole <em>angle</em>. The pole is falling in whatever direction it is"
            " rotating, so the agent can just learn to push the cart toward the pole&rsquo;s spin"
            " to catch it &mdash; without ever being told the exact angle. Look back at step 2:"
            " you took pole angle <em>out</em>, and the agent struggled. But if you had left"
            " <strong>pole velocity</strong> in, it might have balanced anyway, because velocity"
            " carries much of the same &lsquo;which way is it tipping?&rsquo; information. (Try"
            " it: remove pole angle but keep pole velocity.) The best observation"
            " set depends on the task, not just on how much information you can pile on.<br><br>"
            "The <strong>right</strong> observations matter more than the <strong>most</strong>"
            " observations. Continue to learn about <strong>actions</strong>.",
            tone="success",
        )
        observation_reflection = render_reflective_checkin(
            st,
            key="observation_demo_takeaway",
            title="Observation tradeoff",
            prompt=(
                "Did your best run use all four observations? Give one reason extra "
                "observations can help or hurt Q-learning."
            ),
            placeholder="Extra observations helped because... / hurt because...",
            required=True,
        )
        observation_reflection_complete = bool(observation_reflection["complete"])

    selected_features = list(st.session_state["observation_demo_builder_features"])
    playground_columns = st.columns([1, 1])
    with playground_columns[0]:
        component_value = drag_canvas_component(
            mode="observation",
            title="Agent observations",
            pool=observation_pool,
            value=selected_features,
            key="observation_demo_drag_canvas",
            height=330,
            reset_id=f"observation-demo-empty-v3:{drag_builder_session_token(st)}",
        )
        if isinstance(component_value, list):
            incoming_features = [
                str(feature)
                for feature in component_value
                if str(feature) in OBSERVATION_LABELS
            ]
            if incoming_features or st.session_state.get("observation_demo_builder_touched", False):
                selected_features = incoming_features
                st.session_state["observation_demo_builder_features"] = selected_features
                st.session_state["observation_demo_builder_touched"] = True
        if st.button(
            "Train with these observations",
            type="primary",
            use_container_width=True,
            disabled=not selected_features,
        ):
            st.session_state["observation_demo_train_requested"] = True
        if not selected_features:
            st.caption("Drag at least one observation into the box before training.")

    with playground_columns[1]:
        # Train on the features currently in the box. The latch lets the click
        # survive the extra rerun the drag component triggers, so we always
        # train on the up-to-date selection instead of a stale one. Only consume
        # the latch once the box has features, so a momentarily empty settle
        # frame does not swallow the request.
        train_observation_demo = (
            bool(st.session_state.get("observation_demo_train_requested", False))
            and bool(selected_features)
        )
        if train_observation_demo:
            st.session_state.pop("observation_demo_train_requested", None)
            features_for_run = tuple(selected_features)
            with st.spinner("Training controlled observation demo..."):
                run_result = cached_controlled_demo_run(
                    st,
                    cache_name="controlled_observation_demo_cache",
                    features=features_for_run,
                    action_forces=ACTION_PRESETS["Standard left/right"],
                    seed=21,
                )
            st.session_state["observation_demo_playground_run"] = run_result
            feature_set = frozenset(features_for_run)
            already_seen = feature_set in runs_done
            runs_done[feature_set] = float(run_result.get("score", 0.0))

            # Check this specific run against the step the student was on and
            # report back exactly what happened.
            count = len(features_for_run)
            names = ", ".join(OBSERVATION_LABELS[f] for f in features_for_run)
            has_angle = "pole_angle" in feature_set
            if current_step == "full":
                if feature_set == frozenset(ALL_OBSERVATION_FEATURES):
                    msg = (f"✓ Step 1 complete — you trained with all 4 observations "
                           f"({names}). Now remove pole angle for step 2.")
                    tone = "success"
                else:
                    msg = (f"Not step 1 yet: you trained with {count} observation(s) "
                           f"({names}). Step 1 needs all 4 — drag in every observation, then train.")
                    tone = "warn"
            elif current_step == "without_angle":
                if not has_angle:
                    msg = (f"✓ Step 2 complete — you trained without pole angle "
                           f"({names}). Now try any different combination for step 3.")
                    tone = "success"
                else:
                    msg = ("Not step 2 yet: pole angle is still in the box. Drag pole "
                           "angle OUT so the agent cannot see it, then train.")
                    tone = "warn"
            elif current_step == "free":
                if not already_seen:
                    msg = (f"✓ Step 3 complete — you tried a new combination "
                           f"({names}). All experiments done; continue to actions.")
                    tone = "success"
                else:
                    msg = (f"That combination ({names}) was already trained. Step 3 "
                           "needs a NEW, different combination — change the box, then train.")
                    tone = "warn"
            else:
                msg = (f"Trained with {count} observation(s): {names}. "
                       "You've finished all three experiments — explore freely.")
                tone = "success"
            st.session_state["observation_demo_feedback"] = {"text": msg, "tone": tone}
            # Rerun so the prompt and feedback update on this single click.
            request_streamlit_rerun(st)
        run = st.session_state.get("observation_demo_playground_run")
        selected_feature_tuple = tuple(selected_features)
        if (
            isinstance(run, dict)
            and run.get("gif_bytes")
            and run.get("version") == CONTROLLED_DEMO_VERSION
            and tuple(run.get("features", ())) == selected_feature_tuple
        ):
            shown_features = ", ".join(OBSERVATION_LABELS[feature] for feature in run["features"])
            st.markdown(
                f'<div class="observation-slide-features"><strong>Agent sees:</strong> {shown_features}'
                f'<br><strong>Balanced for:</strong> {int(round(float(run.get("score", 0.0))))} steps'
                f' (out of {DEMO_MAX_STEPS})</div>',
                unsafe_allow_html=True,
            )
            st.image(run["gif_bytes"], width="stretch")
        else:
            st.info("Train once to see this observation choice in action.")

    can_continue = trained_full and trained_without_angle and trained_free and observation_reflection_complete
    back_column, next_column = st.columns(2)
    if back_column.button("Back", use_container_width=True):
        set_app_stage(st, "pendulum_intro")
    if next_column.button(
        "Continue to actions",
        type="primary",
        use_container_width=True,
        key="observation_demo_continue",
        disabled=not can_continue,
    ):
        set_app_stage(st, "action_demo")
    if not can_continue:
        st.caption("Run all three experiments and answer the observation check-in to continue.")


def build_action_demo_run(
    *,
    label: str,
    action_forces: tuple[float, ...],
    description: str,
    seed: int,
    terminate_on_angle: bool = True,
) -> dict[str, Any]:
    settings = TrainSettings(
        algorithm="Q-learning",
        episodes=DEMO_EPISODES,
        max_steps=DEMO_MAX_STEPS,
        learning_rate=DEMO_LEARNING_RATE,
        gamma=DEMO_GAMMA,
        epsilon=DEMO_EPSILON,
        epsilon_min=DEMO_EPSILON_MIN,
        seed=seed,
        q_bins_per_feature=DEMO_Q_BINS,
        observation_features=DEFAULT_OBSERVATION_FEATURES,
        action_forces=action_forces,
        terminate_on_angle=terminate_on_angle,
        initial_state=(0.0, 0.0, 0.0, 0.0),
    )
    result = train_q_learning(settings, OBSERVATION_DEMO_REWARD_WEIGHTS, label=label)
    _, _, _, frames = evaluate_policy(
        result,
        seed=seed + 300,
        render=True,
        sleep_limit=300,
    )
    return {
        "label": label,
        "description": description,
        "action_forces": action_forces,
        "gif_bytes": frames_to_gif(frames, fps=30),
    }


def _build_action_demo() -> dict[str, Any]:
    return {
        "strong": build_action_demo_run(
            label="Strong left or strong right",
            action_forces=(-15.0, 15.0),
            description="Only two big pushes, no gentle option. Every correction is a hard shove, so the cart jerks back and forth and overshoots instead of settling — it cannot hold the pole steady.",
            seed=31,
            terminate_on_angle=False,
        ),
        "gentle": build_action_demo_run(
            label="Gentle left, coast, gentle right",
            action_forces=(-5.0, 0.0, 5.0),
            description="Smaller pushes plus a no-force coast action. With fine control the agent balances the pole and keeps it upright.",
            seed=31,
        ),
        "right_biased": build_action_demo_run(
            label="One left, several right",
            action_forces=(-10.0, 0.0, 5.0, 10.0, 15.0),
            description="Most of the force options push right, so the agent is biased that way and drifts the cart rightward across the track instead of balancing.",
            seed=11,
            terminate_on_angle=False,
        ),
    }


def action_demo_cache(st: Any) -> dict[str, Any]:
    assets = load_demo_assets(st)
    if "action_demo" in assets:
        return dict(assets["action_demo"])
    if "action_demo_cache" not in st.session_state:
        st.session_state["action_demo_cache"] = _build_action_demo()
    return dict(st.session_state["action_demo_cache"])


ACTION_DEMO_CHOICES: dict[str, tuple[float, ...]] = {
    "Strong left/right": (-15.0, 15.0),
    "Gentle left/none/right": (-5.0, 0.0, 5.0),
    "One left, several right": (-10.0, 0.0, 5.0, 10.0, 15.0),
    "Five force levels": (-15.0, -7.5, 0.0, 7.5, 15.0),
}


def seed_for_action_demo(action_forces: tuple[float, ...]) -> int:
    rounded_forces = tuple(round(float(force), 3) for force in action_forces)
    stable_seeds = {
        (-10.0, 10.0): 21,
        (-15.0, 15.0): 31,
        (-5.0, 0.0, 5.0): 31,
        (-10.0, 0.0, 5.0, 10.0, 15.0): 31,
        (-15.0, -7.5, 0.0, 7.5, 15.0): 42,
    }
    return stable_seeds.get(rounded_forces, 7)


def build_reward_demo_run(
    *,
    label: str,
    reward_weights: dict[str, Any],
    formula: str,
    description: str,
    seed: int,
    terminate_on_angle: bool = True,
) -> dict[str, Any]:
    settings = TrainSettings(
        algorithm="Q-learning",
        episodes=REWARD_DEMO_EPISODES,
        max_steps=DEMO_MAX_STEPS,
        learning_rate=DEMO_LEARNING_RATE,
        gamma=DEMO_GAMMA,
        epsilon=DEMO_EPSILON,
        epsilon_min=DEMO_EPSILON_MIN,
        seed=seed,
        q_bins_per_feature=DEMO_Q_BINS,
        observation_features=DEFAULT_OBSERVATION_FEATURES,
        action_forces=ACTION_PRESETS["Standard left/right"],
        terminate_on_angle=terminate_on_angle,
        initial_state=(0.0, 0.0, 0.0, 0.0),
    )
    result = train_q_learning(settings, reward_weights, label=label)
    _, env_score, _, frames = evaluate_policy(
        result,
        seed=seed + 200,
        render=True,
        sleep_limit=180,
    )
    return {
        "label": label,
        "formula": formula,
        "description": description,
        "score": env_score,
        "gif_bytes": frames_to_gif(frames, fps=30),
    }


def _build_reward_demo() -> dict[str, Any]:
    return {
        "balance": build_reward_demo_run(
            label="Balance the pole",
            reward_weights=REWARD_DEMO_WEIGHTS["balance"],
            formula="reward = alive + cos(pole angle) - 2 x |pole angle| - 8 x fell",
            description="The classic goal. Rewarding staying alive and an upright pole, and punishing falling, gives a policy that reliably balances.",
            seed=41,
        ),
        "max_pole_velocity": build_reward_demo_run(
            label="Spin the pole",
            reward_weights=REWARD_DEMO_WEIGHTS["max_pole_velocity"],
            formula="reward = |pole angular velocity| - 10 x cart off screen",
            description="Reward only how fast the pole spins, with no penalty for falling and no stoppage when it tips. The agent spins the pole around instead of balancing it.",
            seed=33,
            terminate_on_angle=False,
        ),
    }


def reward_demo_cache(st: Any) -> dict[str, Any]:
    assets = load_demo_assets(st)
    if "reward_demo" in assets:
        return dict(assets["reward_demo"])
    # Tie the cache to the episode budget so retraining at a new length rebuilds.
    cache_key = f"reward_demo_cache_e{REWARD_DEMO_EPISODES}_v3"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = _build_reward_demo()
    return dict(st.session_state[cache_key])


def _alive_factor(terms: list[dict[str, Any]]) -> float:
    """Total positive 'alive' weight in a built reward (0 if none)."""
    return sum(
        float(t.get("factor", 0.0))
        for t in terms
        if str(t.get("signal")) == "alive"
    )


def _penalizes_signal(weights: dict[str, Any], signal: str) -> bool:
    """True if moving `signal` away from 0 LOWERS the reward — checked by
    evaluating the built reward, so it works whether the negative sign sits on
    the term or on an absolute-value block wrapping it."""
    idx = {"cart_position": 0, "cart_velocity": 1, "pole_angle": 2,
           "pole_angular_velocity": 3}.get(signal)
    if idx is None:
        return False
    base = [0.0, 0.0, 0.0, 0.0]
    bumped = list(base)
    # Bump within the normalized range so it registers on the reward's scale.
    bumped[idx] = 1.2 if signal in ("cart_position", "cart_velocity") else 0.6
    r0 = reward_function((0, 0, 0, 0), 0, 0.0, tuple(base), 1.0, False, False, weights)
    r1 = reward_function((0, 0, 0, 0), 0, 0.0, tuple(bumped), 1.0, False, False, weights)
    return r1 < r0 - 1e-9


def check_reward_for_stage(
    stage: str, terms: list[dict[str, Any]], tokens: list[Any] | None = None
) -> tuple[bool, str]:
    """Validate the built reward against what the current step asks for.

    Returns (is_correct, message). The message is a hint shown when the reward
    is wrong, so the student gets specific feedback before training. Penalty
    checks are behavioral (does the reward drop when the value moves away from
    0?) so they work no matter how absolute value / signs are assembled.
    """
    alive = _alive_factor(terms)
    weights = {"reward_terms": terms, "reward_tokens": tokens or []}
    has_cart_pen = _penalizes_signal(weights, "cart_position")
    has_polevel_pen = _penalizes_signal(weights, "pole_angular_velocity")

    if stage == "penalty":
        if alive > 0:
            return False, (
                "Not yet — this step is **penalties only**, but you have a positive **alive**"
                " term in there. Remove it for now. Penalize the cart's distance from center and"
                " the pole's rotation, each with a **negative** sign."
            )
        if not has_cart_pen or not has_polevel_pen:
            missing = []
            if not has_cart_pen:
                missing.append("the **cart's distance from center**")
            if not has_polevel_pen:
                missing.append("the **pole's rotation** (pole angular velocity)")
            return False, (
                "Not yet — your reward needs to get *worse* when " + " and ".join(missing)
                + " grows. Reward should drop the farther the cart drifts and the faster the pole"
                " spins."
                "\n\n**Hint:** distance is never negative, so wrap each in **absolute value**"
                " ( the `| |` blocks ) and give it a **negative** factor."
            )
        return True, ""

    if stage == "alive":
        if not (0 < alive <= 2):
            return False, (
                "Keep your two penalties, and add a **+1 alive** term (a positive alive bonus,"
                " factor about 1). That gives the agent a reason to stay in the game."
            )
        if not has_cart_pen or not has_polevel_pen:
            return False, (
                "Don't drop your penalties — keep penalizing the cart's distance from center and"
                " the pole's rotation, and add the **+1 alive** on top."
            )
        return True, ""

    if stage == "lazy":
        if alive < 10:
            return False, (
                "For this step, turn the **alive** bonus way up — set its factor to **10 or"
                " more** — and keep your penalties. Then train and watch what the agent does."
            )
        return True, ""

    return True, ""


def render_reward_howto(st: Any) -> None:
    """Quick illustrated guide: how to make a term negative and how to wrap it
    in absolute value, shown right before the design activity."""
    st.markdown(
        """
        <style>
        .howto-card {
            border: 1px solid #d0d5dd;
            border-radius: 12px;
            background: #f9fafb;
            padding: 1rem 1.2rem;
            margin: 0.6rem 0 1rem;
        }
        .howto-card h4 { margin: 0 0 0.6rem; font-size: 1.15rem; color: #101828; }
        .howto-step {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            flex-wrap: wrap;
            padding: 0.55rem 0;
            border-top: 1px dashed #e4e7ec;
        }
        .howto-step:first-of-type { border-top: none; }
        .howto-num {
            flex: 0 0 auto;
            width: 1.6rem; height: 1.6rem;
            border-radius: 999px;
            background: #2563eb; color: #fff;
            font-weight: 800; font-size: 0.9rem;
            display: inline-flex; align-items: center; justify-content: center;
        }
        .howto-text { font-size: 1rem; color: #344054; }
        .howto-pill {
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            background: #ffffff; border: 1px solid #98a2b3; border-radius: 8px;
            padding: 0.2rem 0.5rem; font-weight: 700; color: #182230; font-size: 0.92rem;
            white-space: nowrap;
        }
        .howto-pill.neg { border-color: #f04438; color: #b42318; background: #fef3f2; }
        .howto-pill.abs { border-color: #2563eb; color: #1d4ed8; background: #eff6ff; }
        .howto-arrow { color: #667085; font-weight: 800; font-size: 1.2rem; }
        </style>
        <div class="howto-card">
            <h4>Quick guide: shaping a reward term</h4>
            <div class="howto-step">
                <span class="howto-num">1</span>
                <span class="howto-text">Drag a signal into the equation. It starts with a
                factor of <span class="howto-pill">+1</span>.</span>
            </div>
            <div class="howto-step">
                <span class="howto-num">2</span>
                <span class="howto-text"><strong>Make it a penalty</strong> by typing a negative
                number in its factor box:</span>
                <span class="howto-pill">1 &times; pole angle</span>
                <span class="howto-arrow">&rarr;</span>
                <span class="howto-pill neg">&minus;1 &times; pole angle</span>
            </div>
            <div class="howto-step">
                <span class="howto-num">3</span>
                <span class="howto-text"><strong>Count both directions the same</strong> by
                dragging the <span class="howto-pill abs">abs( )</span> block <em>on top of</em>
                an existing term:</span>
                <span class="howto-pill neg">&minus;1 &times; pole angle</span>
                <span class="howto-arrow">&rarr;</span>
                <span class="howto-pill neg">&minus;1 &times; | pole angle |</span>
            </div>
            <div class="howto-step">
                <span class="howto-num">4</span>
                <span class="howto-text">Now the term is most when the value is 0 and drops as it
                moves either way &mdash; left or right, leaning or spinning, costs the same.</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_reward_design_exercise(st: Any) -> None:
    """Staged reward-design lesson: penalties-only fails, +alive fixes it, too
    much alive makes the agent lazy."""
    st.markdown(GUIDED_PROMPT_STYLE, unsafe_allow_html=True)
    st.subheader("Your turn: design a reward function")

    reward_pool = [
        {
            "id": signal,
            "label": REWARD_SIGNAL_LABELS[signal],
            "group": group,
            "scales": REWARD_SCALE_LABELS if signal in REWARD_SCALE_SIGNALS else {},
            "default_scale": default_reward_scale(signal),
        }
        for group, signals in {
            "Episode": ["alive", "fell"],
            "Cart state": ["cart_position", "cart_velocity"],
            "Pole state": ["pole_angle", "pole_angular_velocity"],
        }.items()
        for signal in signals
    ]

    # What the student has discovered so far (persists as they progress).
    saw_penalty_fail = bool(st.session_state.get("reward_lesson_saw_penalty_fail"))
    saw_alive_balance = bool(st.session_state.get("reward_lesson_saw_alive_balance"))
    saw_lazy = bool(st.session_state.get("reward_lesson_saw_lazy"))

    # Decide the current stage and show the matching prompt.
    if not saw_penalty_fail:
        stage = "penalty"
        render_guided_prompt(
            st,
            step_label="Step 1 of 3 · Say what you want",
            title="Reward the agent for staying centered and not rotating.",
            body="Build a reward that gets <em>worse</em> the further the cart is from the center"
            " and the faster the pole is rotating &mdash; in other words, penalize the cart&rsquo;s"
            " <strong>distance from center</strong> and the pole&rsquo;s <strong>distance from"
            " zero rotation</strong>. You have <strong>cart position</strong> and"
            " <strong>pole angular velocity</strong> to work with. <strong>Predict</strong> how it"
            " will do, then train and watch.",
        )
    elif not saw_alive_balance:
        stage = "alive"
        render_guided_prompt(
            st,
            step_label="Step 2 of 3 · Give it a reason to live",
            title="Now add a  + 1 · alive  term and train again.",
            body="Your last reward was all penalties, so every extra step only made the total"
            " <em>worse</em> &mdash; the agent&rsquo;s best move was to end the episode fast. Add a"
            " <strong>+1 alive</strong> term so staying in the game finally pays. Now keeping the"
            " pole up earns +1 each step, while drifting and rotating cost a little. Train and"
            " compare.",
            tone="warn",
        )
    elif not saw_lazy:
        stage = "lazy"
        render_guided_prompt(
            st,
            step_label="Step 3 of 3 · Push it further",
            title="Now turn the alive bonus way up — try + 10 or more — and train.",
            body="A +1 alive bonus worked nicely. What happens if you make surviving worth a lot"
            " more than the penalties &mdash; set the <strong>alive</strong> bonus to"
            " <strong>+10 or more</strong>? <strong>Predict what the agent will do</strong>, then"
            " train and watch closely.",
        )
    else:
        stage = "done"
        render_guided_prompt(
            st,
            step_label="Nice work",
            title="Reward design is a balancing act.",
            body="Too few positives and the agent gives up to stop the penalties; too large a"
            " survival bonus and it stops caring about doing the task well. A good reward keeps"
            " those forces in tension. Continue when you are ready.",
            tone="success",
        )

    st.session_state.setdefault("reward_demo_builder_terms", [])
    component_value = drag_canvas_component(
        mode="reward",
        title="Reward function",
        pool=reward_pool,
        value=list(st.session_state["reward_demo_builder_terms"]),
        key="reward_demo_drag_canvas",
        height=520,
        reset_id="reward-demo-builder",
    )
    if isinstance(component_value, list):
        st.session_state["reward_demo_builder_terms"] = component_value

    reward_tokens, demo_reward_terms = normalize_reward_builder_items(
        list(st.session_state["reward_demo_builder_terms"])
    )
    alive_weight = _alive_factor(demo_reward_terms)

    # Validate the built reward against the current step BEFORE allowing a train,
    # so a wrong reward gets an immediate hint instead of a wasted run.
    has_terms = bool(demo_reward_terms)
    reward_ok, reward_hint = check_reward_for_stage(stage, demo_reward_terms, reward_tokens)

    if st.button(
        "Train with your reward",
        type="primary",
        use_container_width=True,
        disabled=not has_terms,
        key="reward_demo_train_button",
    ):
        st.session_state["reward_demo_train_requested"] = True
    if not has_terms:
        st.caption("Build a reward function above before training.")

    train_clicked = bool(st.session_state.pop("reward_demo_train_requested", False))

    # If they tried to train a reward that does not match this step, stop and
    # coach them right away.
    if train_clicked and has_terms and not reward_ok and stage != "done":
        st.warning(reward_hint)
        train_clicked = False

    if train_clicked and has_terms:
        reward_for_run = {"reward_terms": demo_reward_terms, "reward_tokens": reward_tokens}
        # On the lazy-agent step, remove the early end-on-fall so the episode
        # always runs to full length. Now the alive bonus pays out every step
        # whether or not the pole is up, so the agent has no reason to balance.
        no_early_end = stage == "lazy"
        with st.spinner("Training a Q-learning agent with your reward..."):
            run_result = cached_controlled_demo_run(
                st,
                cache_name="controlled_reward_demo_cache",
                features=DEFAULT_OBSERVATION_FEATURES,
                action_forces=ACTION_PRESETS["Standard left/right"],
                seed=21,
                reward_weights=reward_for_run,
                episodes=REWARD_LESSON_EPISODES,
                q_bins=REWARD_LESSON_Q_BINS,
                learning_rate=REWARD_LESSON_LEARNING_RATE,
                epsilon_min=REWARD_LESSON_EPSILON_MIN,
                terminate_on_angle=not no_early_end,
            )
        run_result["alive_weight"] = alive_weight
        run_result["no_early_end"] = no_early_end
        st.session_state["reward_demo_playground_run"] = run_result
        # The reward matched the step (validated above), so advance the lesson.
        if stage == "penalty":
            st.session_state["reward_lesson_saw_penalty_fail"] = True
        elif stage == "alive":
            st.session_state["reward_lesson_saw_alive_balance"] = True
        elif stage == "lazy":
            st.session_state["reward_lesson_saw_lazy"] = True
        request_streamlit_rerun(st)

    reward_run = st.session_state.get("reward_demo_playground_run")
    if isinstance(reward_run, dict) and reward_run.get("gif_bytes"):
        score = int(round(float(reward_run.get("score", 0.0))))
        run_alive = float(reward_run.get("alive_weight", 0.0))
        no_early_end = bool(reward_run.get("no_early_end"))
        upright_frac = float(reward_run.get("upright_fraction", 0.0))
        upright_pct = int(round(upright_frac * 100))

        if no_early_end:
            # Step count is meaningless here (the episode always runs full length),
            # so report how much of the time the pole was actually upright.
            st.markdown(
                f'<div class="reward-slide-note"><strong>Your reward, trained:</strong> for this'
                f' run the episode never ends early, even if the pole falls. The pole was actually'
                f' upright only <strong>{upright_pct}%</strong> of the time.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="reward-slide-note"><strong>Your reward, trained:</strong> the agent'
                f' balanced for <strong>{score}</strong> steps (out of {DEMO_MAX_STEPS}).</div>',
                unsafe_allow_html=True,
            )
        # For the lazy run we show the good-vs-lazy comparison below instead of a
        # single clip, so skip the standalone gif here.
        if not no_early_end:
            st.image(reward_run["gif_bytes"], width="stretch")

        # Training curve: the total reward the agent collected each episode — the
        # quantity it is actually trying to maximize. This is what reveals the
        # consequences of the reward function you wrote.
        curve = reward_run.get("reward_curve")
        if isinstance(curve, list) and curve and not no_early_end:
            st.caption(
                "Total reward per episode over training (this is what the agent is"
                " maximizing — watch whether your reward pushes it toward balancing):"
            )
            st.line_chart({"reward per episode": [float(v) for v in curve]}, height=200)

        # Explain what just happened, matched to the run.
        if no_early_end and run_alive >= 10:
            st.warning(
                "There it is. For this run we turned off the rule that ends the episode when the"
                " pole falls — so the episode always runs the full length no matter what. Now the"
                f" big alive bonus pays out every single step whether the pole is up or down, and"
                f" the agent figured that out: it stopped balancing and just lets the pole swing"
                f" around (upright only {upright_pct}% of the time), still raking in almost the"
                f" same reward.\n\n"
                "**This is the lazy-agent problem.** Normally the episode *cutting short* when the"
                " pole falls is what made the alive bonus work — to keep earning +alive, the agent"
                " *had* to keep the pole up, so the bonus quietly reinforced balancing. Remove that"
                " cutoff, or make the bonus so large the penalties stop mattering, and the agent"
                " gets paid for doing nothing — so the notebook raises the value of doing nothing."
            )
            # Side-by-side: the good +1-alive agent vs the lazy +10 agent, both
            # rolled out in the SAME fall-allowed world.
            with st.spinner("Training..."):
                comparison = cached_lazy_comparison(st, seed=21)
            st.markdown(
                "**Same environment, both allowed to fall — compare them:**"
            )
            good_col, lazy_col = st.columns(2)
            with good_col:
                st.markdown(
                    f'<div class="reward-slide-note"><strong>+1 alive</strong> (step 2):'
                    f' upright <strong>{int(round(comparison["good_upright"] * 100))}%</strong>'
                    f' of the time — it keeps balancing.</div>',
                    unsafe_allow_html=True,
                )
                if comparison.get("good_gif"):
                    st.image(comparison["good_gif"], width="stretch")
                good_curve = comparison.get("good_curve")
                if isinstance(good_curve, list) and good_curve:
                    st.caption("Reward per episode while training:")
                    st.line_chart({"+1 alive": [float(v) for v in good_curve]}, height=180)
            with lazy_col:
                st.markdown(
                    f'<div class="reward-slide-note"><strong>+10 alive</strong> (lazy):'
                    f' upright <strong>{int(round(comparison["lazy_upright"] * 100))}%</strong>'
                    f' of the time — it lets the pole swing freely.</div>',
                    unsafe_allow_html=True,
                )
                if comparison.get("lazy_gif"):
                    st.image(comparison["lazy_gif"], width="stretch")
                lazy_curve = comparison.get("lazy_curve")
                if isinstance(lazy_curve, list) and lazy_curve:
                    st.caption("Reward per episode while training:")
                    st.line_chart({"+10 alive": [float(v) for v in lazy_curve]}, height=180)
        elif run_alive <= 0 and score < 80:
            st.warning(
                "Look at the reward curve: it stays **negative and never climbs**. With an"
                " all-penalty reward, every extra step only adds more negative reward, so the way"
                " to lose the *fewest* points is to **let the pole fall right away** and end the"
                " episode. Just like the grid game, the agent is maximizing the points exactly as"
                " written — your reward nudges the notebook toward quitting fast. **Go to step 2"
                " and add a +1 alive term.**"
            )
        elif 0 < run_alive <= 2 and score >= 80:
            st.success(
                "Now the curve climbs and the pole stays up. The **+1 alive** term means every"
                " step in the game is worth more than the small penalties for drifting or"
                " rotating. And because the episode **ends the moment the pole falls**, the only"
                " way to keep collecting that +1 is to actually keep balancing — so the bonus"
                " quietly nudges the notebook toward exactly the behavior you want."
            )
        else:
            st.info(
                f"Balanced for {score} steps. Keep adjusting the alive bonus and the penalties"
                " to see how the balance of forces changes the behavior."
            )


def render_reward_slideshow_page(st: Any) -> None:
    st.markdown(
        """
        <style>
        .reward-slide-note {
            font-size: 1.18rem;
            line-height: 1.55;
            margin: 1rem 0 1.25rem;
            color: #344054;
        }
        .reward-formula {
            border: 1px solid #d0d5dd;
            border-radius: 8px;
            padding: 0.8rem;
            margin: 0.7rem 0 0.9rem;
            background: #f9fafb;
            color: #182230;
            font-size: 1.05rem;
            font-weight: 800;
            min-height: 6.2rem;
        }
        .reward-slide-note.demo-caption {
            min-height: 5.4rem;
        }
        .reward-slide-lead {
            font-size: 1.28rem;
            line-height: 1.55;
            margin: 1rem 0 1.25rem;
            color: #243447;
        }
        .reward-teach-card {
            border: 1px solid #d0d5dd;
            border-radius: 10px;
            padding: 1rem 1.15rem;
            margin: 0.9rem 0;
            background: #ffffff;
        }
        .reward-teach-card h4 {
            margin: 0 0 0.55rem;
            font-size: 1.12rem;
            color: #182230;
        }
        .reward-teach-card p {
            font-size: 1.05rem;
            line-height: 1.5;
            color: #344054;
            margin: 0.4rem 0;
        }
        .reward-inline-code {
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            background: #f2f4f7;
            border-radius: 5px;
            padding: 0.1rem 0.38rem;
            color: #1d4ed8;
            font-weight: 700;
            font-size: 0.96rem;
        }
        .reward-compare {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.8rem;
            margin: 0.6rem 0 0.2rem;
        }
        .reward-compare-cell {
            border: 1px solid #e4e7ec;
            border-radius: 8px;
            padding: 0.7rem 0.85rem;
            background: #f9fafb;
        }
        .reward-compare-cell strong {
            color: #182230;
        }
        .reward-table {
            width: 100%;
            border-collapse: collapse;
            margin: 0.5rem 0 0.2rem;
            font-size: 0.98rem;
        }
        .reward-table th, .reward-table td {
            border: 1px solid #e4e7ec;
            padding: 0.42rem 0.6rem;
            text-align: left;
            color: #344054;
        }
        .reward-table th {
            background: #f2f4f7;
            color: #182230;
        }
        .reward-pos { color: #027a48; font-weight: 700; }
        .reward-neg { color: #b42318; font-weight: 700; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("Reward Demo")
    st.markdown(
        """
        <div class="reward-slide-note">
            The reward function is how you teach the agent what behavior is worth
            repeating. The same simple signals can encode completely different goals:
            balance the pole, or spin the pole as fast as possible. Each policy below
            was trained with only the building blocks from the pool.
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_grid_game_bridge(
        st,
        title="Reward still does the teaching",
        body=(
            "In the grid game, spikes pushed a move's Q-value down and gems or the flag "
            "pushed it up. In the pendulum, every reward block does the same kind of nudge: "
            "it tells the notebook whether this force choice in this situation should look "
            "better or worse next time."
        ),
    )

    with st.spinner("Training two small Q-learning agents for the reward demo..."):
        demo = reward_demo_cache(st)

    columns = st.columns(2)
    for column, key in zip(columns, ("balance", "max_pole_velocity")):
        run = demo[key]
        with column:
            st.subheader(run["label"])
            st.markdown(f'<div class="reward-formula">{run["formula"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="reward-slide-note demo-caption">{run["description"]}</div>', unsafe_allow_html=True)
            if run["gif_bytes"]:
                st.image(run["gif_bytes"], width="stretch")

    reward_objective_check = render_reflective_checkin(
        st,
        key="reward_demo_objective",
        title="Same world, different objective",
        prompt="Why did one agent balance while the other spun the pole?",
        placeholder="The reward made balancing worth... while spinning was worth...",
        required=True,
    )

    st.subheader("How the math inside a reward block works")
    st.markdown(
        """
        <div class="reward-teach-card">
            <h4>1. Everything is measured on a fixed scale first</h4>
            <p>
                Before the agent sees a number, the lab squeezes it into a
                predictable range. Positions and velocities are normalized to
                <span class="reward-inline-code">[-1, 1]</span>, and the pole angle
                is wrapped into <span class="reward-inline-code">[-&pi;, &pi;]</span>
                so that &quot;straight up&quot; is 0 and a full lean to either side is
                &plusmn;&pi;. Keeping every signal on the same scale means one term
                cannot accidentally drown out the others.
            </p>
        </div>
        <div class="reward-teach-card">
            <h4>2. <span class="reward-inline-code">cos</span> and <span class="reward-inline-code">sin</span> point the agent at different goals</h4>
            <p>
                Once a signal is mapped to the range
                <span class="reward-inline-code">-&pi;</span> to
                <span class="reward-inline-code">&pi;</span> (0 in the middle), a math
                function turns that distance into a reward, and the function you pick
                decides <em>which</em> value pays the most.
            </p>
            <div class="reward-compare">
                <div class="reward-compare-cell">
                    <strong>cos(distance)</strong> peaks at <strong>0</strong>.<br>
                    cos(0) = 1 (best), cos(&plusmn;&pi;) = -1 (worst). Use it to say
                    &quot;reward being right in the middle.&quot;
                </div>
                <div class="reward-compare-cell">
                    <strong>sin(distance)</strong> peaks at <strong>&pi;/2</strong>.<br>
                    sin(0) = 0, sin(&plusmn;&pi;) = 0, sin(&pi;/2) = 1. Use it to say
                    &quot;reward being off to one side,&quot; not centered.
                </div>
            </div>
            <table class="reward-table">
                <tr><th>distance (-&pi;..&pi;)</th><th>cos</th><th>sin</th></tr>
                <tr><td>0 (centered)</td><td class="reward-pos">1.0 (max)</td><td>0.0</td></tr>
                <tr><td>&pi;/2 (off to one side)</td><td>0.0</td><td class="reward-pos">1.0 (max)</td></tr>
                <tr><td>&plusmn;&pi; (far edge)</td><td class="reward-neg">-1.0 (min)</td><td>0.0</td></tr>
            </table>
            <p>
                So <span class="reward-inline-code">cos(distance from -&pi; to &pi;)</span>
                rewards getting that distance to <strong>0</strong> (the center), while
                <span class="reward-inline-code">sin(distance from -&pi; to &pi;)</span>
                rewards being <strong>off to one side</strong> instead. Same input, very
                different behavior.
            </p>
        </div>
        <div class="reward-teach-card">
            <h4>3. Absolute value turns a direction into a distance</h4>
            <p>
                A raw signal like cart position is signed: -0.6 means left of center,
                +0.6 means right of center. Wrapping it in
                <span class="reward-inline-code">|cart position|</span> throws away the
                direction and keeps only &quot;how far off.&quot; Now left and right are
                treated the same, so a term like
                <span class="reward-inline-code">-0.3 &times; |cart position|</span>
                punishes drifting <em>either</em> way and pulls the cart back toward the
                middle.
            </p>
        </div>
        <div class="reward-teach-card">
            <h4>4. The sign of the number is the instruction</h4>
            <p>
                A <span class="reward-pos">big positive</span> reward tells the agent
                &quot;do more of this.&quot; A <span class="reward-neg">big negative</span>
                reward tells it &quot;stop doing this.&quot; The size sets how strongly it
                cares: <span class="reward-inline-code">-8 &times; fell</span> is a loud
                &quot;never fall,&quot; while <span class="reward-inline-code">-0.1 &times; |cart position|</span>
                is a gentle nudge. Zero means &quot;I don't care about this signal.&quot;
            </p>
        </div>
        <div class="reward-teach-card">
            <h4>5. Reward signals you can combine</h4>
            <p>These are the building blocks available in the reward block:</p>
            <table class="reward-table">
                <tr><th>signal</th><th>what it measures</th></tr>
                <tr><td>alive</td><td>+1 for every step the episode survives</td></tr>
                <tr><td>fell</td><td>1 on the step the pole falls (pair with a negative factor)</td></tr>
                <tr><td>pole angle</td><td>tilt of the pole, wrapped to [-&pi;, &pi;]</td></tr>
                <tr><td>cart position / velocity</td><td>where the cart is and how fast it moves</td></tr>
                <tr><td>pole angular velocity</td><td>how fast the pole is rotating</td></tr>
                <tr><td>distance from target position</td><td>how far the cart is from a target spot (0 = on target)</td></tr>
                <tr><td>distance from target angle</td><td>how far the pole is from a target lean (0 = on target)</td></tr>
            </table>
            <p>
                Any of these can be transformed with
                <span class="reward-inline-code">cos</span>,
                <span class="reward-inline-code">sin</span>, or
                <span class="reward-inline-code">abs</span>, then scaled by a positive
                or negative factor. The two demos above use exactly these pieces
                &mdash; rewarding an upright pole gives balancing, while
                <span class="reward-inline-code">|pole angular velocity|</span> with no
                fall penalty gives a spinning pole.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_reward_howto(st)
    reward_abs_check = render_reflective_checkin(
        st,
        key="reward_abs_angle",
        title="Signed signal check",
        prompt="Why is -1 x |pole angle| better for balancing than -1 x pole angle?",
        placeholder="A signed pole angle would reward one side and punish the other, but absolute value...",
        required=True,
    )
    render_reward_design_exercise(st)

    st.markdown(
        """
        <div class="reward-slide-lead">
            Next, start the tutorial and use the full pendulum lab. You will get
            observations, actions, reward blocks, starting states, and ethical
            exploration all together.
        </div>
        """,
        unsafe_allow_html=True,
    )
    back_column, next_column = st.columns(2)
    if back_column.button("Back", use_container_width=True):
        set_app_stage(st, "action_demo")
    reward_reflections_complete = reward_objective_check["complete"] and reward_abs_check["complete"]
    if next_column.button(
        "Continue",
        type="primary",
        use_container_width=True,
        disabled=not reward_reflections_complete,
    ):
        set_app_stage(st, "algorithm_demo")
    if not reward_reflections_complete:
        st.caption("Answer both reward check-ins to continue.")


ALGO_DEMO_VERSION = "algo-demo-v1"
ALGO_DEMO_REWARD_WEIGHTS: dict[str, Any] = {
    "reward_terms": [
        {"signal": "alive", "factor": 1.0, "scale": "unit"},
        {"signal": "pole_angle", "factor": 1.0, "transform": "cos", "scale": "pi"},
        {"signal": "pole_angle", "factor": -2.0, "transform": "abs", "scale": "pi"},
        {"signal": "cart_position", "factor": -0.1, "transform": "abs", "scale": "unit"},
        {"signal": "fell", "factor": -8.0, "scale": "unit"},
    ],
}


def _build_algorithm_demo_assets() -> dict[str, Any]:
    """Train the Q-table/DQN demo and return only the picklable render data."""
    payload = _train_algorithm_demo()
    return {
        "q_map_png": figure_to_png_bytes(payload["q_map"]),
        "dqn_map_png": figure_to_png_bytes(payload["dqn_map"]),
        "q_table_shape": payload["q_table_shape"],
        "q_table_cells": payload["q_table_cells"],
    }


def build_algorithm_demo(st: Any) -> dict[str, Any]:
    """Train one small Q-table and one small DQN on the same balance task."""
    cache_key = f"algorithm_demo_cache_{ALGO_DEMO_VERSION}"
    if cache_key in st.session_state:
        return dict(st.session_state[cache_key])
    return _train_algorithm_demo(st, cache_key)


def _train_algorithm_demo(st: Any | None = None, cache_key: str | None = None) -> dict[str, Any]:

    common = dict(
        max_steps=DEMO_MAX_STEPS,
        learning_rate=DEMO_LEARNING_RATE,
        gamma=DEMO_GAMMA,
        epsilon=DEMO_EPSILON,
        epsilon_min=DEMO_EPSILON_MIN,
        seed=7,
        observation_features=DEFAULT_OBSERVATION_FEATURES,
        action_forces=ACTION_PRESETS["Standard left/right"],
    )

    q_settings = TrainSettings(
        algorithm="Q-learning",
        episodes=600,
        q_bins_per_feature=8,
        **common,
    )
    dqn_settings = TrainSettings(
        algorithm="DQN",
        episodes=120,
        hidden_size=64,
        learning_rate=0.001,
        batch_size=64,
        target_update=10,
        **{key: value for key, value in common.items() if key != "learning_rate"},
    )

    q_result = train_q_learning(q_settings, ALGO_DEMO_REWARD_WEIGHTS, label="Q-table")
    dqn_result = train_dqn(dqn_settings, ALGO_DEMO_REWARD_WEIGHTS, label="DQN")

    payload = {
        "q_result": q_result,
        "dqn_result": dqn_result,
        "q_map": make_policy_value_figure(q_result, cart_position=0.0, cart_velocity=0.0),
        "dqn_map": make_policy_value_figure(dqn_result, cart_position=0.0, cart_velocity=0.0),
        "q_table_shape": q_result.policy["q_table"].shape,
        "q_table_cells": int(q_result.policy["q_table"].size),
    }
    if st is not None and cache_key is not None:
        st.session_state[cache_key] = payload
    return dict(payload)


def render_algorithm_demo_page(st: Any) -> None:
    st.markdown(
        """
        <style>
        .algo-note {
            font-size: 1.18rem;
            line-height: 1.55;
            margin: 1rem 0 1.25rem;
            color: #344054;
        }
        .algo-lead {
            font-size: 1.28rem;
            line-height: 1.55;
            margin: 0.35rem 0 1rem;
            color: #243447;
        }
        .algo-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin: 0.6rem 0 0.4rem;
        }
        .algo-card {
            border: 1px solid #d0d5dd;
            border-radius: 10px;
            padding: 1rem 1.15rem;
            background: #ffffff;
        }
        .algo-card h4 {
            margin: 0 0 0.5rem;
            font-size: 1.16rem;
            color: #182230;
        }
        .algo-card .algo-tag {
            display: inline-block;
            font-size: 0.85rem;
            font-weight: 800;
            border-radius: 999px;
            padding: 0.15rem 0.6rem;
            margin-bottom: 0.55rem;
        }
        .algo-tag.fast { background: #ecfdf3; color: #027a48; }
        .algo-tag.slow { background: #fef3f2; color: #b42318; }
        .algo-card ul { margin: 0.4rem 0 0; padding-left: 1.1rem; }
        .algo-card li { font-size: 1.02rem; line-height: 1.5; color: #344054; margin: 0.25rem 0; }
        .algo-diagram {
            border: 1px dashed #98a2b3;
            border-radius: 8px;
            padding: 0.85rem;
            margin: 0.6rem 0 0.2rem;
            background: #f9fafb;
            text-align: center;
        }
        .qcell-grid {
            display: inline-grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 3px;
        }
        .qcell {
            width: 20px; height: 20px;
            border-radius: 3px;
            background: #d1e9ff;
            border: 1px solid #b2ddff;
        }
        .qcell.hot { background: #2e90fa; border-color: #1570cd; }
        .net-layer {
            display: inline-flex;
            flex-direction: column;
            gap: 4px;
            margin: 0 0.55rem;
            vertical-align: middle;
        }
        .net-node {
            width: 16px; height: 16px;
            border-radius: 50%;
            background: #fdb022;
            border: 1px solid #dc6803;
            margin: 0 auto;
        }
        .net-arrow { color: #667085; font-weight: 800; font-size: 1.4rem; vertical-align: middle; }
        .net-label { font-size: 0.8rem; color: #475467; margin-top: 0.3rem; }
        .algo-callout {
            border-left: 4px solid #2e90fa;
            background: #eff8ff;
            border-radius: 6px;
            padding: 0.85rem 1rem;
            margin: 1rem 0;
            font-size: 1.08rem;
            line-height: 1.5;
            color: #1849a9;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("Q-table vs DQN")
    st.markdown(
        """
        <div class="algo-note">
            Both methods learn the same thing &mdash; how good each action is in each
            state &mdash; but they store that knowledge very differently. That single
            choice changes how fast they train and how smoothly they generalize.
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_grid_game_bridge(
        st,
        title="Q-table is the grid-game notebook",
        body=(
            "The grid game showed the literal notebook: each observation had one score for "
            "each move. A pendulum Q-table is the same notebook, but the observations are "
            "bucketed physics numbers and the actions are force choices. DQN keeps the same "
            "idea of Q-values, but uses a neural network to estimate the notebook instead of "
            "storing every row."
        ),
    )

    q_in = len(DEFAULT_OBSERVATION_FEATURES)
    q_out = len(ACTION_PRESETS["Standard left/right"])
    st.markdown(
        f"""
        <div class="algo-grid">
            <div class="algo-card">
                <span class="algo-tag fast">DISCRETE &middot; FAST</span>
                <h4>Q-table</h4>
                <div class="algo-diagram">
                    <div class="qcell-grid">
                        {''.join('<div class="qcell' + (' hot' if i in (8, 9, 14, 15, 20, 21) else '') + '"></div>' for i in range(36))}
                    </div>
                    <div class="net-label">a grid of cells, one stored number per state &times; action</div>
                </div>
                <ul>
                    <li>Chops each observation into bins, then stores a value in every cell.</li>
                    <li>Updating is just editing one cell &mdash; extremely fast and stable.</li>
                    <li>Learning in one cell does <em>not</em> help neighboring cells, so the map looks blocky.</li>
                    <li>Cells grow explosively as you add observations (the &quot;curse of dimensionality&quot;).</li>
                </ul>
            </div>
            <div class="algo-card">
                <span class="algo-tag slow">CONTINUOUS &middot; SLOWER</span>
                <h4>DQN (neural network)</h4>
                <div class="algo-diagram">
                    <span class="net-layer"><span class="net-node"></span><span class="net-node"></span><span class="net-node"></span><span class="net-node"></span><div class="net-label">{q_in} inputs</div></span>
                    <span class="net-arrow">&rarr;</span>
                    <span class="net-layer"><span class="net-node"></span><span class="net-node"></span><span class="net-node"></span><span class="net-node"></span><span class="net-node"></span><span class="net-node"></span><div class="net-label">64 hidden</div></span>
                    <span class="net-arrow">&rarr;</span>
                    <span class="net-layer"><span class="net-node"></span><span class="net-node"></span><span class="net-node"></span><span class="net-node"></span><span class="net-node"></span><span class="net-node"></span><div class="net-label">64 hidden</div></span>
                    <span class="net-arrow">&rarr;</span>
                    <span class="net-layer"><span class="net-node"></span><span class="net-node"></span><div class="net-label">{q_out} actions</div></span>
                </div>
                <ul>
                    <li>A small network reads the raw continuous state and predicts each action's value.</li>
                    <li>It generalizes &mdash; nearby states share weights, so the map is smooth.</li>
                    <li>Training is noisier: gradients, replay, and a target network take many more steps.</li>
                    <li>Scales to large/continuous observations where a table would be impossible.</li>
                </ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    algorithm_size_check = render_reflective_checkin(
        st,
        key="algorithm_table_size",
        title="Before you see the maps",
        prompt="If a Q-table uses 8 buckets per observation, what happens to table size when you add one more observation?",
        choices=("It adds 8x more state buckets", "It adds 1 more row", "It does not change"),
        placeholder="Explain why the table grows that way.",
        required=True,
    )

    st.subheader("The policy each one learned")
    st.markdown(
        """
        <div class="algo-note">
            These maps show the preferred push (left vs right) and how valuable the
            state is, sliced across pole angle and angular velocity. Watch the
            texture: the Q-table is blocky because each bin is independent, while the
            DQN is smooth because the network interpolates between states.
        </div>
        """,
        unsafe_allow_html=True,
    )

    assets = load_demo_assets(st)
    precomputed = assets.get("algorithm_demo")
    if precomputed:
        demo = precomputed
    else:
        with st.spinner("Training a Q-table and a DQN on the same balance task (the DQN takes longer)..."):
            demo = build_algorithm_demo(st)

    map_columns = st.columns(2)
    with map_columns[0]:
        st.markdown(
            f'<div class="algo-note"><strong>Q-table</strong> &mdash; {" &times; ".join(str(s) for s in demo["q_table_shape"])} = {demo["q_table_cells"]:,} stored cells, trained 600 episodes.</div>',
            unsafe_allow_html=True,
        )
        if "q_map_png" in demo:
            st.image(demo["q_map_png"], width="stretch")
        else:
            st.pyplot(demo["q_map"])
    with map_columns[1]:
        st.markdown(
            '<div class="algo-note"><strong>DQN</strong> &mdash; a 64-unit network, trained only 120 episodes and still smoothing in.</div>',
            unsafe_allow_html=True,
        )
        if "dqn_map_png" in demo:
            st.image(demo["dqn_map_png"], width="stretch")
        else:
            st.pyplot(demo["dqn_map"])

    algorithm_map_check = render_reflective_checkin(
        st,
        key="algorithm_policy_map_texture",
        title="Read the maps",
        prompt="Which policy map looks blockier, and what does that say about how the algorithm stores knowledge?",
        placeholder="The blockier map is... because...",
        required=True,
    )

    st.markdown(
        """
        <div class="algo-callout">
            <strong>Where to start:</strong> begin with the <strong>Q-table</strong>.
            It trains in seconds, is easy to reason about, and almost always converges
            on CartPole. Once you understand the loop, switch to <strong>DQN</strong> to
            see how a network handles richer observations &mdash; but expect it to take
            longer, need more episodes, and be harder to get to a good policy.
        </div>
        """,
        unsafe_allow_html=True,
    )

    back_column, next_column = st.columns(2)
    if back_column.button("Back", use_container_width=True):
        set_app_stage(st, "reward_demo")
    algorithm_reflections_complete = algorithm_size_check["complete"] and algorithm_map_check["complete"]
    if next_column.button(
        "Continue to lab",
        type="primary",
        use_container_width=True,
        disabled=not algorithm_reflections_complete,
    ):
        set_app_stage(st, "lab")
    if not algorithm_reflections_complete:
        st.caption("Answer both algorithm check-ins to continue to the lab.")


def render_action_slideshow_page(st: Any) -> None:
    st.markdown(
        """
        <style>
        .action-slide-lead {
            font-size: 1.28rem;
            line-height: 1.55;
            margin: 0.35rem 0 1rem;
            color: #243447;
        }
        .action-slide-note {
            font-size: 1.18rem;
            line-height: 1.55;
            margin: 1rem 0 1.25rem;
            color: #344054;
        }
        .action-slide-forces {
            font-size: 1.05rem;
            line-height: 1.45;
            margin: 0.25rem 0 0.8rem;
            color: #475467;
        }
        .action-slide-note.demo-caption {
            min-height: 5.4rem;
        }
        .action-slide-forces.demo-forces {
            min-height: 2.6rem;
        }
        .lab-snippet {
            border: 1px solid #d0d5dd;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0 1.25rem;
            background: #f9fafb;
        }
        .lab-snippet-title {
            font-size: 1.15rem;
            font-weight: 800;
            color: #182230;
            margin-bottom: 0.75rem;
        }
        .lab-action-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.8rem;
        }
        .lab-action-card {
            border: 1px solid #d0d5dd;
            border-radius: 8px;
            padding: 0.85rem;
            background: white;
        }
        .lab-action-card strong {
            display: block;
            font-size: 1rem;
            margin-bottom: 0.45rem;
            color: #182230;
        }
        .lab-chip {
            display: inline-block;
            border: 1px solid #98a2b3;
            border-radius: 999px;
            padding: 0.42rem 0.7rem;
            margin: 0.18rem;
            background: #ffffff;
            color: #182230;
            font-weight: 700;
            font-size: 0.95rem;
        }
        .lab-chip.selected {
            border-color: #2563eb;
            background: #eff6ff;
            color: #1d4ed8;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("Action Demo")
    st.markdown(
        """
        <div class="action-slide-note">
            Actions are what the agent is allowed to do. In CartPole, each action
            is a horizontal force on the cart. Changing the action menu changes
            the behaviors the agent can discover.
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_grid_game_bridge(
        st,
        title="Actions are the columns in the same notebook",
        body=(
            "The grid notebook compared four columns: up, down, left, right. The pendulum "
            "notebook compares force choices such as -10, 0, and +10. Q-learning can only "
            "raise or lower the scores for actions that are actually in the menu."
        ),
    )

    with st.spinner("Training three small Q-learning agents for the action demo..."):
        demo = action_demo_cache(st)

    columns = st.columns(3)
    for column, key in zip(columns, ("strong", "gentle", "right_biased")):
        run = demo[key]
        with column:
            st.subheader(run["label"])
            st.markdown(
                f'<div class="action-slide-note demo-caption">{run["description"]}</div>',
                unsafe_allow_html=True,
            )
            forces = ", ".join(f"{force:g}" for force in run["action_forces"])
            st.markdown(
                f'<div class="action-slide-forces demo-forces"><strong>Force choices:</strong> {forces}</div>',
                unsafe_allow_html=True,
            )
            if run["gif_bytes"]:
                st.image(run["gif_bytes"], width="stretch")

    st.markdown(
        """
        <div class="lab-snippet">
            <div class="lab-snippet-title">In the lab, students change actions by choosing the force menu the policy can use.</div>
            <div class="lab-action-row">
                <div class="lab-action-card">
                    <strong>Two choices</strong>
                    <span class="lab-chip selected">-10</span>
                    <span class="lab-chip selected">+10</span>
                </div>
                <div class="lab-action-card">
                    <strong>Add coast</strong>
                    <span class="lab-chip selected">-5</span>
                    <span class="lab-chip selected">0</span>
                    <span class="lab-chip selected">+5</span>
                </div>
                <div class="lab-action-card">
                    <strong>More force levels</strong>
                    <span class="lab-chip selected">-15</span>
                    <span class="lab-chip selected">-7.5</span>
                    <span class="lab-chip selected">0</span>
                    <span class="lab-chip selected">+7.5</span>
                    <span class="lab-chip selected">+15</span>
                </div>
            </div>
        </div>
        <div class="action-slide-lead">
            <strong>All three agents are trained the same way:</strong> same
            observations, same reward, same Q-learning notebook update, same episode budget.
            Only the available action columns change.
        </div>
        <div class="action-slide-note">
            A tiny action space can be easy to learn but coarse. A larger action
            space can be more expressive but gives the agent more choices to test.
            A no-force action lets the policy decide when doing nothing is useful.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(GUIDED_PROMPT_STYLE, unsafe_allow_html=True)
    st.subheader("Experiment: what should the agent be allowed to do?")
    st.markdown(
        '<div class="action-slide-note">Same fixed Q-learning notebook update, same observations, same'
        ' reward. The only thing you change is the menu of force columns the agent can pick from.'
        ' Negative pushes left, positive pushes right, and <strong>0 means no push</strong>.</div>',
        unsafe_allow_html=True,
    )

    # Track every distinct force menu the student has trained (keyed by the
    # rounded force tuple) so we can both detect the required traits and count
    # how many different menus they explored.
    action_runs: dict[tuple[float, ...], float] = st.session_state.setdefault(
        "action_demo_runs_done", {}
    )
    did_basic = any(sorted(menu) == [-10.0, 10.0] for menu in action_runs)
    did_coast = any(any(abs(f) < 1e-6 for f in menu) for menu in action_runs)
    did_large = any(any(abs(f) >= 15.0 for f in menu) for menu in action_runs)
    did_free = len(action_runs) >= 4

    action_reflection_complete = False
    if not did_basic:
        action_step = "basic"
    elif not did_coast:
        action_step = "coast"
    elif not did_large:
        action_step = "large"
    elif not did_free:
        action_step = "free"
    else:
        action_step = "done"

    # Result of the last Train click: kept on screen until the next Train click
    # overwrites it, so a "not yet" message stays put while the student retries.
    feedback = st.session_state.get("action_demo_feedback")
    if feedback:
        if feedback.get("tone") == "success":
            st.success(feedback["text"])
        else:
            st.warning(feedback["text"])

    if not did_basic:
        render_guided_prompt(
            st,
            step_label="Step 1 of 4 · Push or push",
            title="Drag in just −10 and +10, then train.",
            body="The agent can only shove left or shove right &mdash; it can never sit still."
            " <strong>Predict:</strong> how will the cart and pole look while it tries to"
            " balance? Then train.",
        )
    elif not did_coast:
        render_guided_prompt(
            st,
            step_label="Step 2 of 4 · Let it rest",
            title="Add a 0 force (no push), then train again.",
            body="Now the agent can choose to do nothing. <strong>Predict:</strong> with a"
            " &lsquo;no push&rsquo; option, should it be able to stay still or coast more"
            " smoothly? Train and compare to step 1.",
            tone="warn",
        )
    elif not did_large:
        render_guided_prompt(
            st,
            step_label="Step 3 of 4 · Go big",
            title="Now try some really large forces (±15 or more).",
            body="Give the agent powerful shoves. <strong>Predict:</strong> will big forces help"
            " it react faster, or make it overshoot and look jerky? Train and see.",
        )
    elif not did_free:
        render_guided_prompt(
            st,
            step_label="Step 4 of 4 · Your own menu",
            title="Design a force menu of your own and predict the behavior.",
            body="Mix magnitudes and a rest option however you like. <strong>Say how you expect"
            " it to move</strong> before you train, then check yourself.",
        )
    else:
        render_guided_prompt(
            st,
            step_label="Nice work",
            title="The actions you allow set the limits of what the agent can do.",
            body="The agent can only ever pick from the forces you give it. If you never offer"
            " a 0, it can never choose to stop pushing; if its only options are huge forces, it"
            " can never make a gentle correction. The action menu defines the agent's whole"
            " range of behavior &mdash; before it learns anything, you have already decided what"
            " is possible. Continue to design the <strong>reward function</strong>.",
            tone="success",
        )
        action_reflection = render_reflective_checkin(
            st,
            key="action_demo_takeaway",
            title="Action space limits behavior",
            prompt="What behavior is impossible if the action menu does not include 0?",
            placeholder="Without a zero-force action, the agent can never...",
            required=True,
        )
        action_reflection_complete = bool(action_reflection["complete"])

    playground_columns = st.columns([1, 1])
    with playground_columns[0]:
        if st.session_state.get("action_demo_builder_version") != "empty-v3":
            st.session_state["action_demo_builder_items"] = []
            st.session_state["action_demo_builder_touched"] = False
            st.session_state["action_demo_builder_version"] = "empty-v3"
        component_value = drag_canvas_component(
            mode="action",
            title="Agent actions",
            pool=action_builder_pool(),
            value=list(st.session_state["action_demo_builder_items"]),
            key="action_demo_drag_canvas",
            height=330,
            reset_id=f"action-demo-builder-empty-v3:{drag_builder_session_token(st)}",
        )
        if isinstance(component_value, list):
            if component_value or st.session_state.get("action_demo_builder_touched", False):
                st.session_state["action_demo_builder_items"] = component_value
                st.session_state["action_demo_builder_touched"] = True
        action_forces = normalize_optional_action_builder_items(st.session_state["action_demo_builder_items"])
        if action_forces:
            forces = ", ".join(f"{force:g}" for force in action_forces)
            st.markdown(
                f'<div class="action-slide-forces"><strong>Selected force choices:</strong> {forces}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.caption("Drag at least one force bubble into the box before training.")
        if st.button(
            "Train with these actions",
            type="primary",
            use_container_width=True,
            disabled=not action_forces,
        ):
            st.session_state["action_demo_train_requested"] = True

    with playground_columns[1]:
        # Latch so the click survives the drag component's extra rerun. Only
        # consume it once there is a force menu to train on, so a momentarily
        # empty box on a settle frame does not swallow the request.
        train_action_demo = (
            bool(st.session_state.get("action_demo_train_requested", False))
            and bool(action_forces)
        )
        if train_action_demo:
            st.session_state.pop("action_demo_train_requested", None)
            forces_for_run = tuple(action_forces)
            with st.spinner("Training controlled action demo..."):
                run_result = cached_controlled_demo_run(
                    st,
                    cache_name="controlled_action_demo_cache",
                    features=DEFAULT_OBSERVATION_FEATURES,
                    action_forces=forces_for_run,
                    seed=seed_for_action_demo(forces_for_run),
                )
            st.session_state["action_demo_playground_run"] = run_result
            menu_key = tuple(round(float(force), 3) for force in forces_for_run)
            already_seen = menu_key in action_runs
            action_runs[menu_key] = float(run_result.get("score", 0.0))

            # Check this run against the step the student was on.
            shown = ", ".join(f"{f:g}" for f in forces_for_run)
            has_zero = any(abs(f) < 1e-6 for f in menu_key)
            has_large = any(abs(f) >= 15.0 for f in menu_key)
            is_basic = sorted(menu_key) == [-10.0, 10.0]
            if action_step == "basic":
                if is_basic:
                    msg = (f"✓ Step 1 complete — you trained with just −10 and +10 ({shown}). "
                           "Now add a 0 (no push) for step 2.")
                    tone = "success"
                else:
                    msg = (f"Not step 1 yet: you used {shown}. Step 1 needs exactly −10 and "
                           "+10 — clear the box and drag in only those two, then train.")
                    tone = "warn"
            elif action_step == "coast":
                if has_zero:
                    msg = (f"✓ Step 2 complete — your menu includes a 0 no-push ({shown}). "
                           "Now try some really large forces (±15+) for step 3.")
                    tone = "success"
                else:
                    msg = (f"Not step 2 yet: {shown} has no rest option. Add a 0 force so the "
                           "agent can choose not to push, then train.")
                    tone = "warn"
            elif action_step == "large":
                if has_large:
                    msg = (f"✓ Step 3 complete — you used a large force ({shown}). "
                           "Now design your own menu for step 4.")
                    tone = "success"
                else:
                    msg = (f"Not step 3 yet: {shown} has no big force. Add a force of ±15 or "
                           "more, then train.")
                    tone = "warn"
            elif action_step == "free":
                if not already_seen:
                    msg = (f"✓ Step 4 complete — you designed a new menu ({shown}). "
                           "All experiments done; continue to the reward function.")
                    tone = "success"
                else:
                    msg = (f"That menu ({shown}) was already trained. Step 4 needs a NEW, "
                           "different menu — change the forces, then train.")
                    tone = "warn"
            else:
                msg = f"Trained with {shown}. You've finished all four experiments — explore freely."
                tone = "success"
            st.session_state["action_demo_feedback"] = {"text": msg, "tone": tone}
            request_streamlit_rerun(st)
        run = st.session_state.get("action_demo_playground_run")
        selected_action_tuple = tuple(action_forces)
        if (
            isinstance(run, dict)
            and run.get("gif_bytes")
            and run.get("version") == CONTROLLED_DEMO_VERSION
            and tuple(run.get("action_forces", ())) == selected_action_tuple
        ):
            shown_forces = ", ".join(f"{force:g}" for force in run["action_forces"])
            st.markdown(
                f'<div class="action-slide-forces"><strong>Agent actions:</strong> {shown_forces}'
                f'<br><strong>Balanced for:</strong> {int(round(float(run.get("score", 0.0))))} steps'
                f' (out of {DEMO_MAX_STEPS})</div>',
                unsafe_allow_html=True,
            )
            st.image(run["gif_bytes"], width="stretch")
        else:
            st.info("Train once to see this action space in action.")

    can_continue = did_basic and did_coast and did_large and did_free and action_reflection_complete
    back_column, next_column = st.columns(2)
    if back_column.button("Back", use_container_width=True):
        set_app_stage(st, "observation_demo")
    if next_column.button(
        "Continue to reward",
        type="primary",
        use_container_width=True,
        key="action_demo_continue",
        disabled=not can_continue,
    ):
        set_app_stage(st, "reward_demo")
    if not can_continue:
        st.caption("Run all four experiments and answer the action check-in to continue.")
    if not can_continue:
        st.caption("Run all four experiments above to continue.")


def render_tutorial_choice_page(st: Any) -> None:
    st.title("Choose Your Path")
    st.caption("Start with a guided walk-through, or jump straight into the lab.")

    start_column, skip_column = st.columns(2)
    with start_column:
        st.subheader("Start tutorial")
        st.write("Move through the page section by section and connect each control to the RL loop.")
        if st.button("Start tutorial", type="primary", use_container_width=True):
            st.session_state["tutorial_enabled"] = True
            st.session_state["tutorial_step"] = 0
            set_app_stage(st, "lab")
    with skip_column:
        st.subheader("Skip tutorial")
        st.write("Open the full activity immediately. You can turn the tutorial on later at the top.")
        if st.button("Skip", use_container_width=True):
            st.session_state["tutorial_enabled"] = False
            set_app_stage(st, "lab")


def render_tutorial_anchor(st: Any, target: str) -> None:
    st.markdown(f'<span id="tutorial-{target}"></span>', unsafe_allow_html=True)
    step = active_tutorial_step(st)
    pending_target = str(st.session_state.get("tutorial_scroll_target", ""))
    should_scroll = (step is not None and step["target"] == target) or pending_target == target
    if not should_scroll:
        return
    if pending_target == target:
        st.session_state.pop("tutorial_scroll_target", None)

    scroll_to_element(st, f"tutorial-{target}")


def scroll_to_element(st: Any, element_id: str) -> None:
    st.html(
        f"""
        <script>
        function scrollToTarget() {{
          const target = document.getElementById("{element_id}");
          if (target) {{
            target.scrollIntoView({{behavior: "smooth", block: "center"}});
          }}
        }}
        setTimeout(scrollToTarget, 80);
        setTimeout(scrollToTarget, 350);
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def sync_tutorial_results_view(st: Any, has_results: bool) -> None:
    if not has_results:
        return

    step = active_tutorial_step(st)
    if step is None:
        return

    if step["target"] == "replay":
        st.session_state["results_view"] = "Replay"
    elif step["target"] == "curve":
        st.session_state["results_view"] = "Results"
    elif step["target"] == "policy":
        st.session_state["results_view"] = "Policy map"


def render_tutorial_styles(st: Any) -> None:
    # The yellow tutorial callout boxes were removed, so there are no styles to inject.
    return


def render_tutorial_callout(st: Any, target: str, ui: Any | None = None) -> None:
    # Tutorial callouts (the yellow hint boxes) have been removed.
    return


def set_sidebar_default_for_stage(st: Any, *, expanded: bool) -> None:
    action = "open" if expanded else "close"
    storage_key = "pendulumSidebarOpenedForLab" if expanded else "pendulumSidebarClosedBeforeLab"
    script = """
        <script>
        (function () {
          const key = "__STORAGE_KEY__";
          if (window.sessionStorage.getItem(key) === "1") return;
          window.sessionStorage.setItem(key, "1");

          function syncSidebar() {
            const sidebar = document.querySelector('section[data-testid="stSidebar"]');
            const sidebarWidth = sidebar ? sidebar.getBoundingClientRect().width : 0;
            const shouldOpen = "__ACTION__" === "open";
            if (shouldOpen && sidebarWidth >= 120) return;
            if (!shouldOpen && sidebarWidth < 120) return;

            const buttons = Array.from(document.querySelectorAll("button"));
            const targetButton = buttons.find((button) => {
              const label = `${button.getAttribute("aria-label") || ""} ${button.title || ""}`.toLowerCase();
              if (shouldOpen) {
                return label.includes("open sidebar") || label.includes("expand sidebar");
              }
              return label.includes("close sidebar") || label.includes("collapse sidebar");
            });
            if (targetButton) targetButton.click();
          }

          [80, 250, 700, 1300].forEach((delay) => setTimeout(syncSidebar, delay));
        })();
        </script>
        """
    st.html(
        script.replace("__STORAGE_KEY__", storage_key).replace("__ACTION__", action),
        unsafe_allow_javascript=True,
    )


def is_network_url_session(st: Any) -> bool:
    try:
        url = str(st.context.url or "")
    except Exception:
        return False

    if not url:
        return False

    host = url.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0].strip("[]").lower()
    return host not in {"", "localhost", "127.0.0.1", "::1", "0.0.0.0"}


def sidebar_settings(st: Any, forced_algorithm: str | None = None) -> TrainSettings:
    render_tutorial_anchor(st, "training")
    st.sidebar.header("Training")
    if forced_algorithm is not None:
        algorithm = forced_algorithm
        st.sidebar.info(f"This mission requires: **{forced_algorithm}**")
    else:
        algorithm = st.sidebar.selectbox(
            "Algorithm",
            ["Q-learning", "DQN"],
            help="Q-learning is the grid-game notebook: stored action scores per situation. DQN predicts those Q-values with a small neural network.",
        )
    cpu_count = os.cpu_count() or 1
    shared_hosting = is_network_url_session(st)
    default_episodes = 120 if algorithm == "Q-learning" or shared_hosting else 300
    max_episodes = 500 if algorithm == "Q-learning" else 400
    episode_step = 20 if algorithm == "Q-learning" else 50
    episodes = int(
        st.sidebar.slider(
            "Training episodes",
            20,
            max_episodes,
            default_episodes,
            episode_step,
            help="More episodes gives the agent more practice, but takes longer.",
        )
    )
    learning_rate = float(
        st.sidebar.slider(
            "Learning speed",
            0.01,
            1.0,
            0.2 if algorithm == "Q-learning" else 0.05,
            0.01,
            help="How strongly each new experience changes what the agent believes.",
        )
    )
    epsilon = float(
        st.sidebar.slider(
            "Exploration",
            0.0,
            1.0,
            0.8,
            0.05,
            help="Chance the agent tries a random action instead of its current best guess. High exploration means more trying things.",
        )
    )
    render_tutorial_callout(st, "training", st.sidebar)

    max_steps = 200 if algorithm == "DQN" and shared_hosting else 300
    gamma = 0.99
    epsilon_min = 0.05
    seed = 7
    q_bins_per_feature = 8
    target_update = 10
    update_every = 1
    parallel_envs = 1
    cpu_env_cap = max(1, cpu_count - 4)
    if shared_hosting:
        cpu_env_cap = 1
    dqn_parallel_options = [option for option in (1, 2, 4, 8, 12, 16) if option <= cpu_env_cap]
    if not dqn_parallel_options:
        dqn_parallel_options = [1]
    default_dqn_parallel_envs = 1 if shared_hosting else min(4, dqn_parallel_options[-1])

    if algorithm == "Q-learning":
        batch_size = 64
        hidden_size = 64
    else:
        learning_rate = learning_rate * 0.01
        batch_size = 16 if shared_hosting else 32
        hidden_size = 16 if shared_hosting else 32
        target_update = 5
        update_every = 10 if shared_hosting else 4
        parallel_envs = default_dqn_parallel_envs

    with st.sidebar.expander("Advanced"):
        max_steps = int(st.slider("Max steps", 50, 500, max_steps, 25))
        gamma = float(st.slider("Future reward discount", 0.80, 0.999, gamma, 0.005))
        epsilon_min = float(st.slider("Final exploration", 0.0, 0.3, epsilon_min, 0.01))
        seed = int(st.number_input("Seed", min_value=0, max_value=999_999, value=seed))
        q_bins_per_feature = int(
            st.select_slider(
                "Q-table buckets",
                options=[4, 5, 6, 8, 10, 12],
                value=q_bins_per_feature,
            )
        )
        if algorithm == "DQN":
            batch_size_options = [16, 32] if shared_hosting else [16, 32, 64, 128]
            hidden_size_options = [16, 32] if shared_hosting else [16, 32, 64, 128]
            update_every_options = [8, 10, 12] if shared_hosting else [1, 2, 4, 8]
            batch_size = int(st.select_slider("DQN batch size", batch_size_options, batch_size))
            hidden_size = int(st.select_slider("DQN hidden units", hidden_size_options, hidden_size))
            update_every = int(st.select_slider("DQN update every N steps", update_every_options, update_every))
            target_update = int(st.select_slider("DQN target update episodes", [2, 5, 10, 20], target_update))
            parallel_envs = int(
                st.select_slider(
                    "DQN parallel CPU envs",
                    dqn_parallel_options,
                    parallel_envs,
                    help=(
                        f"Detected {cpu_count} CPU cores. "
                        "Network URL sessions are capped lower so multiple people can train at once."
                        if shared_hosting
                        else f"Detected {cpu_count} CPU cores. This keeps about 4 cores free when possible."
                    ),
                )
            )
    return TrainSettings(
        algorithm=algorithm,
        episodes=episodes,
        max_steps=max_steps,
        learning_rate=learning_rate,
        gamma=gamma,
        epsilon=epsilon,
        epsilon_min=epsilon_min,
        seed=seed,
        batch_size=batch_size,
        hidden_size=hidden_size,
        target_update=target_update,
        update_every=update_every,
        parallel_envs=parallel_envs,
        q_bins_per_feature=q_bins_per_feature,
    )


def normalize_reward_builder_items(items: list[Any]) -> tuple[list[dict[str, Any]], list[dict[str, float | str]]]:
    tokens: list[dict[str, Any]] = []
    terms: list[dict[str, float | str]] = []

    def normalize_items(raw_items: list[Any], collected_terms: list[dict[str, float | str]]) -> list[dict[str, Any]]:
        normalized_tokens: list[dict[str, Any]] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue

            item_type = str(item.get("type", "term" if "signal" in item else ""))
            if item_type == "op":
                operator = "multiply" if item.get("op") in ("multiply", "*", "x") else "add"
                normalized_tokens.append({"type": "op", "op": operator})
                continue

            if item_type == "paren":
                value = "(" if item.get("value") == "(" else ")"
                normalized_tokens.append({"type": "paren", "value": value})
                continue

            if item_type == "func":
                function_name = str(item.get("func", "abs"))
                if function_name in ("abs", "sin", "cos", "min", "max"):
                    try:
                        factor = float(item.get("factor", 1.0))
                    except (TypeError, ValueError):
                        factor = 1.0
                    try:
                        threshold = float(item.get("threshold", 0.0))
                    except (TypeError, ValueError):
                        threshold = 0.0
                    normalized_tokens.append(
                        {
                            "type": "func",
                            "func": function_name,
                            "factor": factor,
                            "threshold": threshold,
                            "children": normalize_items(
                                item.get("children", []) if isinstance(item.get("children"), list) else [],
                                collected_terms,
                            ),
                        }
                    )
                continue

            if item_type != "term":
                continue

            signal = str(item.get("signal", "alive"))
            transform = str(item.get("transform", "abs" if item.get("absolute", False) else "raw"))
            connector = str(item.get("connector", "add"))
            scale = clean_reward_scale(signal, str(item.get("scale", default_reward_scale(signal))))
            try:
                factor = float(item.get("factor", 1.0))
            except (TypeError, ValueError):
                factor = 0.0

            if factor == 0.0 or signal not in REWARD_SIGNAL_LABELS:
                continue

            if item.get("type") != "term" and normalized_tokens:
                normalized_tokens.append(
                    {
                        "type": "op",
                        "op": "multiply" if connector == "multiply" else "add",
                    }
                )

            term_token = {
                "type": "term",
                "signal": signal,
                "factor": factor if transform == "raw" else 1.0,
                "scale": scale,
            }
            if transform in ("abs", "sin", "cos"):
                normalized_tokens.append(
                    {
                        "type": "func",
                        "func": transform,
                        "factor": factor,
                        "children": [term_token],
                    }
                )
            else:
                normalized_tokens.append(term_token)
            collected_terms.append(
                {
                    "signal": signal,
                    "factor": factor,
                    "transform": transform,
                    "connector": "multiply" if connector == "multiply" else "add",
                    "scale": scale,
                }
            )

        return normalized_tokens

    return normalize_items(items, terms), terms


def reward_controls(st: Any) -> dict[str, Any]:
    render_tutorial_anchor(st, "reward")
    st.subheader("Reward lab")
    st.caption(
        "Drag signals and math blocks into the equation. Each step's reward nudges the "
        "agent's notebook: this force choice in this pendulum situation should look better or worse."
    )
    render_tutorial_callout(st, "reward")

    if "reward_builder_terms" not in st.session_state:
        st.session_state["reward_builder_terms"] = [dict(term) for term in DEFAULT_REWARD_TERMS]

    signal_groups: dict[str, list[str]] = {
        "Episode": [
            "alive",
            "fell",
        ],
        "Cart state": [
            "cart_position",
            "cart_velocity",
        ],
        "Track limits": [
            "cart_off_screen",
        ],
        "Pole state": [
            "pole_angle",
            "pole_angular_velocity",
        ],
        "Action": ["action_force"],
    }
    if st.session_state.get("ethical_exploration_enabled", False):
        signal_groups["Ethical exploration"] = [
            "hit_animal",
            "animal_distance",
            "cart_hit_animal",
            "pole_hit_animal",
            "pole_distance_to_animal",
        ]

    reward_pool = [
        {
            "id": signal,
            "label": REWARD_SIGNAL_LABELS[signal],
            "group": group_name,
            "scales": REWARD_SCALE_LABELS if signal in REWARD_SCALE_SIGNALS else {},
            "default_scale": default_reward_scale(signal),
        }
        for group_name, signals in signal_groups.items()
        for signal in signals
    ]

    component_value = drag_canvas_component(
        mode="reward",
        title="Reward function",
        pool=reward_pool,
        value=list(st.session_state["reward_builder_terms"]),
        key="reward_drag_canvas",
        height=680,
        reset_id="reward-builder",
    )
    if isinstance(component_value, list):
        st.session_state["reward_builder_terms"] = component_value

    reward_tokens, reward_terms = normalize_reward_builder_items(
        list(st.session_state["reward_builder_terms"])
    )

    return {
        "reward_terms": reward_terms,
        "reward_tokens": reward_tokens,
    }


def parse_action_forces(text: str) -> tuple[float, ...]:
    forces = sorted({float(part.strip()) for part in text.split(",") if part.strip()})
    if len(forces) < 2:
        raise ValueError("Use at least two force values.")
    if any(not math.isfinite(force) for force in forces):
        raise ValueError("Forces must be finite numbers.")
    if any(abs(force) > 30.0 for force in forces):
        raise ValueError("Keep forces between -30 and 30 for a readable demo.")
    return tuple(forces)


def action_builder_pool() -> list[dict[str, Any]]:
    return [
        {"id": "force:left", "label": "Left push", "group": "Force bubbles", "default_force": -10.0},
        {"id": "force:none", "label": "No push", "group": "Force bubbles", "default_force": 0.0},
        {"id": "force:right", "label": "Right push", "group": "Force bubbles", "default_force": 10.0},
    ]


def normalize_action_builder_items(items: Any) -> tuple[float, ...]:
    if not isinstance(items, list):
        return ACTION_PRESETS["Standard left/right"]

    forces: list[float] = []
    for item in items:
        value = item.get("force") if isinstance(item, dict) else item
        try:
            force = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(force) and abs(force) <= 30.0:
            forces.append(force)

    unique_sorted = tuple(sorted(set(forces)))
    if len(unique_sorted) < 2:
        return ACTION_PRESETS["Standard left/right"]
    return unique_sorted


def normalize_optional_action_builder_items(items: Any) -> tuple[float, ...]:
    if not isinstance(items, list):
        return ()

    forces: list[float] = []
    for item in items:
        value = item.get("force") if isinstance(item, dict) else item
        try:
            force = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(force) and abs(force) <= 30.0:
            forces.append(force)
    return tuple(sorted(set(forces)))


def action_forces_to_builder_items(action_forces: tuple[float, ...]) -> list[dict[str, float]]:
    return [{"force": float(force)} for force in action_forces]


def render_state_legend(st: Any) -> None:
    pd = require_dependencies("pandas")["pandas"]
    with st.expander("State legend", expanded=True):
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Signal": "cart position",
                        "Zero means": "cart is centered",
                        "Positive means": "cart is right of center",
                    },
                    {
                        "Signal": "cart velocity",
                        "Zero means": "cart is not moving",
                        "Positive means": "cart moving right",
                    },
                    {
                        "Signal": "pole angle",
                        "Zero means": "pole is upright",
                        "Positive means": "pole leans right",
                    },
                    {
                        "Signal": "pole angular velocity",
                        "Zero means": "pole angle is not changing",
                        "Positive means": "pole rotating right",
                    },
                    {
                        "Signal": "cart force",
                        "Zero means": "no push",
                        "Positive means": "push right",
                    },
                    {
                        "Signal": "distance to animal",
                        "Zero means": "cart is at the animal",
                        "Positive means": "cart is right of animal",
                    },
                ]
            ),
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "Agent observations are normalized before training. "
            "Each reward signal block can choose unit or pi scaling."
        )


def behavior_controls(
    st: Any,
    show_start_controls: bool = True,
    forced_start: str | None = None,
) -> tuple[tuple[str, ...], tuple[float, ...], tuple[float, float, float, float] | None, bool]:
    render_tutorial_anchor(st, "observation_action")
    st.subheader("Observation and action lab")
    render_tutorial_callout(st, "observation_action")
    render_grid_game_bridge(
        st,
        title="You are choosing the notebook's rows and columns",
        body=(
            "The grid game's rows were local views and its columns were arrow moves. "
            "Here, the rows are the observation signals you drag in, and the columns are "
            "the force actions you allow. Training fills in which force is best for each row."
        ),
    )

    # Start the observation and action builders empty for each new mission so
    # students choose them from scratch rather than inheriting the previous
    # mission's selection.
    current_mission = active_mission(st)
    if st.session_state.get("behavior_builder_mission") != current_mission:
        st.session_state["behavior_builder_mission"] = current_mission
        st.session_state["observation_builder_features"] = []
        st.session_state["action_builder_items"] = []
    if show_start_controls:
        obs_column, action_column, start_column = st.columns(3)
    else:
        obs_column, action_column = st.columns(2)
        start_column = None

    with obs_column:
        st.markdown("**Observations**")
        st.caption(
            "Drag observation bubbles into the canvas below. These become the situation "
            "the agent uses to choose a notebook row."
        )
        if "observation_builder_features" not in st.session_state:
            st.session_state["observation_builder_features"] = list(DEFAULT_OBSERVATION_FEATURES)

        observation_groups = {
            "Cart": ["cart_position", "cart_velocity"],
            "Pole": ["pole_angle", "pole_angular_velocity"],
            "Angle helpers": ["sin_theta", "cos_theta"],
        }
        if st.session_state.get("ethical_exploration_enabled", False):
            observation_groups["Ethical exploration"] = ["animal_distance"]

        observation_pool = [
            {"id": feature, "label": OBSERVATION_LABELS[feature], "group": group_name}
            for group_name, features in observation_groups.items()
            for feature in features
        ]
        selected_features = list(st.session_state["observation_builder_features"])
        component_value = drag_canvas_component(
            mode="observation",
            title="Agent observations",
            pool=observation_pool,
            value=selected_features,
            key="observation_drag_canvas",
            height=390,
            reset_id=f"{current_mission}:ethical:{st.session_state.get('ethical_exploration_enabled', False)}",
        )
        if isinstance(component_value, list):
            selected_features = [
                str(feature)
                for feature in component_value
                if str(feature) in OBSERVATION_LABELS
            ]
            st.session_state["observation_builder_features"] = selected_features

        with st.expander("What the observation options mean", expanded=tutorial_enabled(st)):
            for feature in observation_pool:
                st.markdown(
                    f"**{feature['label']}**: {OBSERVATION_DESCRIPTIONS.get(feature['id'], 'An input the agent can use while choosing actions.')}"
                )

    with action_column:
        st.markdown("**Actions**")
        st.caption(
            "Drag force bubbles into the canvas, then type the force value. These are the "
            "notebook columns the policy is allowed to compare."
        )
        if "action_builder_items" not in st.session_state:
            st.session_state["action_builder_items"] = action_forces_to_builder_items(ACTION_PRESETS["Standard left/right"])

        component_value = drag_canvas_component(
            mode="action",
            title="Agent actions",
            pool=action_builder_pool(),
            value=list(st.session_state["action_builder_items"]),
            key="action_drag_canvas",
            height=390,
            reset_id=f"action-builder-v1:{current_mission}",
        )
        if isinstance(component_value, list):
            st.session_state["action_builder_items"] = component_value

        action_forces = normalize_action_builder_items(st.session_state["action_builder_items"])
        if len(action_forces) < 2:
            action_forces = ACTION_PRESETS["Standard left/right"]

        st.caption("Current force choices: " + ", ".join(f"{force:g}" for force in action_forces))

    if start_column is None:
        start_mode = forced_start or "Random near upright"
        if start_mode == "Swing up from upside down":
            initial_state = (0.0, 0.0, math.pi, 0.0)
            terminate_on_angle = False
        else:
            initial_state = None
            terminate_on_angle = True
    else:
        with start_column:
            start_mode = st.radio(
                "Episode start",
                ["Random near upright", "Fixed near upright", "Swing up from upside down"],
                key="start_mode",
                help="Swing-up starts with the pole hanging down at rest and lets the episode continue until the cart leaves the track.",
            )
            terminate_on_angle = start_mode != "Swing up from upside down"
            if start_mode == "Fixed near upright":
                start_theta_degrees = float(st.slider("Start pole angle", -10.0, 10.0, 0.0, 0.5))
                start_theta_dot = float(st.slider("Start pole spin", -3.0, 3.0, 0.0, 0.05))
                with st.expander("Cart start details"):
                    start_x = float(st.slider("Start cart position", -1.5, 1.5, 0.0, 0.05))
                    start_x_dot = float(st.slider("Start cart velocity", -2.0, 2.0, 0.0, 0.05))
                initial_state = (
                    start_x,
                    start_x_dot,
                    math.radians(start_theta_degrees),
                    start_theta_dot,
                )
            elif start_mode == "Swing up from upside down":
                initial_state = (0.0, 0.0, math.pi, 0.0)
                st.caption("Starts at cart center, no velocity, pole hanging down. The run ends only if the cart leaves the track.")
            else:
                initial_state = None
                st.caption("Gymnasium randomizes the start near upright.")

    return tuple(selected_features), tuple(action_forces), initial_state, terminate_on_angle


def ensure_animal_distance_observation(st: Any) -> None:
    st.session_state.setdefault("observation_builder_features", list(DEFAULT_OBSERVATION_FEATURES))
    if "animal_distance" not in st.session_state["observation_builder_features"]:
        st.session_state["observation_builder_features"].append("animal_distance")


def ethical_controls(st: Any, settings: TrainSettings, locked: bool = False) -> None:
    render_tutorial_anchor(st, "ethical")
    st.subheader("Ethical exploration")
    render_tutorial_callout(st, "ethical")
    if locked:
        settings.ethical_exploration = True
        settings.animal_position = 0.0
        settings.animal_radius = 0.18
        settings.animal_contact_ends_episode = True
        settings.random_start_around_animal = True
        st.session_state["ethical_exploration_enabled"] = True
        ensure_animal_distance_observation(st)
        st.markdown(
            "Mission 3 automatically places the animal at the center of the track. "
            "The cart starts randomly on the left or right side, and the agent can see distance to the animal."
        )
        render_grid_game_bridge(
            st,
            title="Seeing a clue is not the same as caring about it",
            body=(
                "In the grid game, seeing a spike mattered because the reward made spikes bad. "
                "Here, animal distance can be part of the notebook row, but the agent only learns "
                "to avoid contact if reward or termination makes contact costly."
            ),
        )
        render_reflective_checkin(
            st,
            key="ethical_observation_vs_reward",
            title="Seeing is not valuing",
            prompt=(
                "If the agent can see the animal but the reward never penalizes contact, "
                "should it avoid the animal? Why?"
            ),
            placeholder="The agent can observe the animal, but it will only care if...",
            required=True,
        )
        return

    enabled = st.checkbox(
        "Put an animal on the track",
        value=False,
        help="Adds a visible animal on the track. The cart or pole can physically contact it.",
    )
    settings.ethical_exploration = enabled
    st.session_state["ethical_exploration_enabled"] = enabled

    if not enabled:
        if "observation_builder_features" in st.session_state:
            st.session_state["observation_builder_features"] = [
                feature
                for feature in st.session_state["observation_builder_features"]
                if feature != "animal_distance"
            ]
        return

    columns = st.columns(4)
    with columns[0]:
        settings.animal_position = float(
            st.slider(
                "Animal position",
                -1.8,
                1.8,
                0.0,
                0.1,
                help="Where the animal sits on the track. Zero is track center; positive is to the right.",
            )
        )
    with columns[1]:
        settings.animal_radius = float(
            st.slider(
                "Animal size",
                0.05,
                0.5,
                0.18,
                0.01,
                help="The animal is a circle. Contact counts when the cart rectangle or pole body overlaps it.",
            )
        )
    with columns[2]:
        settings.animal_contact_ends_episode = st.checkbox(
            "End episode on contact",
            value=True,
            help="If enabled, a cart or pole hit ends the episode immediately.",
        )
    with columns[3]:
        add_distance = st.checkbox(
            "Give agent distance observation",
            value=True,
            help="If enabled, the agent can see signed distance to the animal as part of its observation.",
        )

    if add_distance:
        ensure_animal_distance_observation(st)

    st.caption("The cart and pole can now hit the animal. Use hit-animal reward blocks to teach avoidance.")


def render_metrics(st: Any, results: list[TrainingResult]) -> None:
    pd = require_dependencies("pandas")["pandas"]
    rows = [summarize_result(result) for result in results]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def overlay_ethical_marker(frames: list[Any], settings: TrainSettings) -> list[Any]:
    if not settings.ethical_exploration or not frames:
        return frames

    modules = require_dependencies("numpy", "PIL.Image", "PIL.ImageDraw")
    np = modules["numpy"]
    image_module = modules["PIL.Image"]
    draw_module = modules["PIL.ImageDraw"]
    marked_frames: list[Any] = []

    for frame in frames:
        image = image_module.fromarray(frame).convert("RGB")
        draw = draw_module.Draw(image, "RGBA")
        width, height = image.size
        x_center = int((settings.animal_position + 2.4) / 4.8 * width)
        radius_px = max(6, int(settings.animal_radius / 4.8 * width))
        y_center = int(height * 0.74)
        draw.ellipse(
            (x_center - radius_px, y_center - radius_px, x_center + radius_px, y_center + radius_px),
            fill=(255, 115, 90, 180),
            outline=(145, 30, 20, 240),
            width=3,
        )
        eye_radius = max(1, radius_px // 5)
        draw.ellipse(
            (
                x_center - eye_radius,
                y_center - eye_radius,
                x_center + eye_radius,
                y_center + eye_radius,
            ),
            fill=(40, 20, 15, 240),
        )
        marked_frames.append(np.array(image))

    return marked_frames


def frames_to_gif(frames: list[Any], fps: int = 30) -> bytes:
    if not frames:
        return b""

    modules = require_dependencies("PIL.Image")
    image_module = modules["PIL.Image"]
    images = [image_module.fromarray(frame).convert("P", palette=image_module.ADAPTIVE) for frame in frames]
    buffer = io.BytesIO()
    images[0].save(
        buffer,
        format="GIF",
        save_all=True,
        append_images=images[1:],
        duration=max(1, int(1000 / fps)),
        loop=0,
        optimize=False,
    )
    return buffer.getvalue()


def make_intro_demo_gif() -> bytes:
    """Generate a short local CartPole clip for the intro screen."""
    env = make_env(render=True)
    settings = TrainSettings(
        algorithm="Q-learning",
        episodes=1,
        max_steps=240,
        learning_rate=0.1,
        gamma=0.99,
        epsilon=0.0,
        epsilon_min=0.0,
        seed=11,
    )
    frames: list[Any] = []

    try:
        obs = reset_env(env, settings, settings.seed)
        for step in range(180):
            if step % 2 == 0:
                frames.append(env.render())

            x, x_dot, theta, theta_dot = [float(value) for value in obs]
            control_signal = theta + 0.45 * theta_dot + 0.08 * x + 0.12 * x_dot
            action_force = 10.0 if control_signal > 0.0 else -10.0
            obs, _, terminated, _, _ = step_cartpole_with_force(env, action_force, True)

            if terminated:
                obs = reset_env(env, settings, settings.seed + step + 1)
    finally:
        env.close()

    return frames_to_gif(frames, fps=30)


def intro_demo_gif(st: Any) -> bytes:
    assets = load_demo_assets(st)
    if assets.get("intro_gif"):
        return bytes(assets["intro_gif"])
    if "intro_demo_gif" not in st.session_state:
        try:
            st.session_state["intro_demo_gif"] = make_intro_demo_gif()
        except Exception:
            st.session_state["intro_demo_gif"] = b""
    return bytes(st.session_state["intro_demo_gif"])


def replay_signature(result: TrainingResult) -> tuple[Any, ...]:
    """Identify the trained policy that a cached replay belongs to."""
    return (
        result.label,
        result.algorithm,
        len(result.returns),
        result.settings.seed,
        result.settings.observation_features,
        result.settings.action_forces,
        result.settings.initial_state,
        result.settings.ethical_exploration,
        result.settings.animal_position,
        result.settings.animal_radius,
        result.settings.animal_contact_ends_episode,
        result.settings.pole_length,
        result.settings.random_start_around_animal,
    )


def checkpoint_rollout_gif(result: TrainingResult, max_steps: int = 90) -> bytes:
    """Render a short clip of the current (mid-training) policy for a checkpoint."""
    env = make_env(render=True)
    obs = reset_env(env, result.settings, result.settings.seed + 777)
    frames: list[Any] = []
    try:
        for _ in range(max_steps):
            frames.append(env.render())
            action = choose_action_for_result(result, obs)
            action_force = action_function(action, result.settings.action_forces)
            next_obs, _, terminated, truncated, _ = step_cartpole_with_force(
                env,
                action_force,
                result.settings.terminate_on_angle,
            )
            terminated = apply_animal_contact_termination(next_obs, terminated, result.settings)
            obs = next_obs
            if terminated or truncated:
                break
    finally:
        env.close()
    frames = overlay_ethical_marker(frames, result.settings)
    return frames_to_gif(frames) if frames else b""


def build_replay_cache(result: TrainingResult) -> dict[str, Any]:
    shaped, env_score, length, frames = evaluate_policy(
        result,
        seed=result.settings.seed + 1000,
        render=True,
        sleep_limit=180,
    )
    frames = overlay_ethical_marker(frames, result.settings)
    return {
        "signature": replay_signature(result),
        "shaped": shaped,
        "env_score": env_score,
        "length": length,
        "gif_bytes": frames_to_gif(frames) if frames else b"",
    }


def render_evaluation(st: Any, result: TrainingResult) -> dict[str, Any]:
    render_tutorial_anchor(st, "replay")
    st.subheader("Evaluation")
    render_tutorial_callout(st, "replay")
    signature = replay_signature(result)

    replay = st.session_state.get("latest_replay")
    # Auto-render a replay for the current policy; only rebuild if it is missing
    # or belongs to a different policy than the one being shown.
    if not (replay and replay.get("signature") == signature):
        with st.spinner("Rendering the learned policy..."):
            replay = build_replay_cache(result)
            st.session_state["latest_replay"] = replay

    if st.button("Run another evaluation episode"):
        with st.spinner("Rendering one episode..."):
            replay = build_replay_cache(result)
            st.session_state["latest_replay"] = replay

    c1, c2, c3 = st.columns(3)
    c1.metric("CartPole score", f"{replay['env_score']:.0f}")
    c2.metric("Shaped reward", f"{replay['shaped']:.1f}")
    c3.metric("Steps", f"{replay['length']}")
    st.caption(
        "CartPole score is the number of time steps the pole stays balanced. "
        "Shaped reward is the signal that nudged the notebook during training."
    )

    if replay["gif_bytes"]:
        st.image(replay["gif_bytes"], width="stretch")
    replay_check = render_reflective_checkin(
        st,
            key=f"evaluation_replay_curve_{result.algorithm}_{len(result.returns)}",
            title="Replay as evidence",
            prompt="Did the replay behavior match the reward curve, like the grid-game score graph matched a better policy? What evidence supports your answer?",
            placeholder="The score graph showed... and the replay showed...",
            required=True,
        )
    return replay_check


def render_policy_visualization(st: Any, results: list[TrainingResult]) -> dict[str, Any]:
    np = require_dependencies("numpy")["numpy"]
    render_tutorial_anchor(st, "policy")
    st.subheader("What the agent learned")
    render_tutorial_callout(st, "policy")

    labels = [f"{result.label} ({result.algorithm})" for result in results]
    selected_label = st.selectbox("Run to inspect", labels, key="policy_run")
    result = results[labels.index(selected_label)]

    control_columns = st.columns(2)
    with control_columns[0]:
        cart_position = float(
            st.slider(
                "Hold cart position fixed",
                min_value=-2.4,
                max_value=2.4,
                value=0.0,
                step=0.1,
                key="policy_cart_position",
            )
        )
    with control_columns[1]:
        cart_velocity = float(
            st.slider(
                "Hold cart velocity fixed",
                min_value=-3.0,
                max_value=3.0,
                value=0.0,
                step=0.1,
                key="policy_cart_velocity",
            )
        )

    st.pyplot(
        make_policy_value_figure(result, cart_position, cart_velocity),
        width="stretch",
    )
    st.caption(
        "Blue is negative force, red is positive force, and the black line marks "
        "where the preferred force changes sign. This is the pendulum version of "
        "reading the grid-game notebook's best move."
    )
    policy_check = render_reflective_checkin(
        st,
        key=f"policy_map_reading_{result.algorithm}_{len(result.returns)}",
        title="Read one region",
        prompt="Pick one colored region: what state is it showing, and which force does the agent prefer there?",
        placeholder="In the region where pole angle is... the agent prefers...",
        required=True,
    )

    if result.algorithm == "Q-learning":
        q_table = result.policy["q_table"]
        nonzero = int(np.count_nonzero(q_table))
        columns = st.columns(3)
        columns[0].metric("Table shape", " x ".join(str(size) for size in q_table.shape))
        columns[1].metric("Stored Q-values", f"{q_table.size:,}")
        columns[2].metric("Updated values", f"{nonzero:,}")
        st.caption(
            "Observations: "
            + ", ".join(
                OBSERVATION_LABELS[feature]
                for feature in result.settings.observation_features
            )
        )
        st.caption(
            "The rectangular regions come from discretizing continuous observations "
            "into state buckets: the pendulum version of notebook rows."
        )
    else:
        model = result.policy["model"]
        parameter_count = sum(parameter.numel() for parameter in model.parameters())
        columns = st.columns(4)
        columns[0].metric(
            "Network",
            f"{len(result.settings.observation_features)} -> "
            f"{result.settings.hidden_size} -> {result.settings.hidden_size} -> "
            f"{len(result.settings.action_forces)}",
        )
        columns[1].metric("Parameters", f"{parameter_count:,}")
        columns[2].metric("Gradient updates", f"{result.policy['updates']:,}")
        columns[3].metric("Parallel envs", f"{result.policy.get('parallel_envs', 1)}")
        st.caption(f"DQN device: {result.policy.get('device', 'cpu')}")
        st.caption(
            "Observations: "
            + ", ".join(
                OBSERVATION_LABELS[feature]
                for feature in result.settings.observation_features
            )
        )
        st.caption(
            "The neural network outputs one estimated Q-value for each force action, "
            "as if it were filling in the notebook without storing every row."
        )
    return policy_check


def render_algorithm_comparison(st: Any) -> None:
    pd = require_dependencies("pandas")["pandas"]
    st.subheader("Q-learning vs DQN")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Algorithm": "Q-learning",
                    "State": "Discretized buckets",
                    "Learns": "The grid-game notebook: stored Q-values",
                    "Tradeoff": "Easy to inspect, but every bucketed situation needs notebook entries",
                },
                {
                    "Algorithm": "DQN",
                    "State": "Normalized observations",
                    "Learns": "A neural network that predicts notebook Q-values",
                    "Tradeoff": "Scales better, but the notebook is harder to inspect directly",
                },
            ]
        ),
        hide_index=True,
        width="stretch",
    )


# ---------------------------------------------------------------------------
# Mission mode: sequential graded tasks that unlock bonus mode.
# ---------------------------------------------------------------------------
SUBMISSIONS_DIR = Path(__file__).resolve().parent / "student_submission"
MISSION_ORDER = ("mission_1", "mission_2", "mission_3")
DEFAULT_INSTRUCTOR_PASSWORD = "pendulum-master"


def instructor_password(st: Any) -> str:
    try:
        configured = str(st.secrets.get("instructor_password", "")).strip()
    except Exception:
        configured = ""
    return configured or os.environ.get("PENDULUM_MASTER_PASSWORD", DEFAULT_INSTRUCTOR_PASSWORD)


def active_mission(st: Any) -> str:
    """The mission the page is currently focused on (or 'bonus' once all done)."""
    override = str(st.session_state.get("mission_override", ""))
    if override in (*MISSION_ORDER, "bonus"):
        return override
    progress = set(st.session_state.get("mission_progress", []))
    for mission_id in MISSION_ORDER:
        if mission_id not in progress:
            return mission_id
    return "bonus"


def mission_context(st: Any) -> dict[str, Any]:
    """How the lab page should adapt for the current mission/bonus task."""
    current = active_mission(st)
    if current == "mission_1":
        return {
            "id": "mission_1",
            "title": "Mission 1 — Balance with a Q-table",
            "task": "Train a Q-table agent that keeps the pole balanced for at least 100 steps.",
            "unlock": "Pass the check to unlock Mission 2.",
            "forced_algorithm": "Q-learning",
            "show_start_controls": False,
            "show_ethical": False,
            "forced_start": None,
            "show_pole_length": False,
        }
    if current == "mission_2":
        return {
            "id": "mission_2",
            "title": "Mission 2 — Centered balance with a DQN",
            "task": "Train a DQN that balances for at least 100 steps while keeping the cart predominantly near the center.",
            "unlock": "Pass the check to unlock Mission 3.",
            "forced_algorithm": "DQN",
            "show_start_controls": False,
            "show_ethical": False,
            "forced_start": None,
            "show_pole_length": False,
        }
    if current == "mission_3":
        return {
            "id": "mission_3",
            "title": "Mission 3 — Ethical observation",
            "task": "An animal is fixed at the center of the track. The cart starts randomly on the left or right side, the agent can see distance to the animal, and success means balancing for at least 100 steps.",
            "unlock": "Pass the check to unlock Bonus mode.",
            "forced_algorithm": None,
            "show_start_controls": False,
            "show_ethical": True,
            "locked_ethical": True,
            "forced_start": None,
            "show_pole_length": False,
        }
    # bonus
    bonus_task = st.session_state.get("bonus_task")
    if bonus_task == "one_term":
        return {
            "id": "bonus_one_term",
            "title": "Bonus 1 — One-term reward",
            "task": "Balance the pole using a reward function with exactly ONE term. Find the single signal that is enough.",
            "unlock": "",
            "forced_algorithm": None,
            "show_start_controls": False,
            "show_ethical": False,
            "forced_start": None,
            "show_pole_length": False,
        }
    if bonus_task == "swingup":
        return {
            "id": "bonus_swingup",
            "title": "Bonus 2 — Swing-up challenge",
            "task": "The pole starts hanging down. Design a reward that swings it up and balances it.",
            "unlock": "",
            "forced_algorithm": None,
            "show_start_controls": False,
            "show_ethical": False,
            "forced_start": "Swing up from upside down",
            "show_pole_length": False,
        }
    if bonus_task == "pole_length":
        return {
            "id": "bonus_pole_length",
            "title": "Bonus 3 — Pole length and the policy",
            "task": "Change the pole length, retrain, and watch how the learned policy changes. A longer pole has more rotational inertia, so it tips more slowly and is actually easier to balance.",
            "unlock": "",
            "forced_algorithm": None,
            "show_start_controls": False,
            "show_ethical": False,
            "forced_start": None,
            "show_pole_length": True,
        }
    return {
        "id": "bonus",
        "title": "Bonus mode",
        "task": "All missions complete. Pick a bonus challenge below, or explore freely.",
        "unlock": "",
        "forced_algorithm": None,
        "show_start_controls": True,
        "show_ethical": False,
        "forced_start": None,
        "show_pole_length": False,
    }


def evaluate_mission_run(result: TrainingResult, seed_offset: int = 1000) -> dict[str, Any]:
    """Run one eval episode and report metrics the mission checks need.

    Uses the same start seed as the replay shown to the student (build_replay_cache
    uses seed + 1000), so the GIF they watched and the checked step count agree.
    """
    np = require_dependencies("numpy")["numpy"]
    env = make_env(render=True)
    obs = reset_env(env, result.settings, result.settings.seed + seed_offset)
    frames: list[Any] = []
    cart_positions: list[float] = []
    steps = 0
    try:
        for _ in range(result.settings.max_steps):
            frames.append(env.render())
            cart_positions.append(float(obs[0]))
            action = choose_action_for_result(result, obs)
            action_force = action_function(action, result.settings.action_forces)
            next_obs, _, terminated, truncated, _ = step_cartpole_with_force(
                env,
                action_force,
                result.settings.terminate_on_angle,
            )
            terminated = apply_animal_contact_termination(next_obs, terminated, result.settings)
            steps += 1
            obs = next_obs
            if terminated or truncated:
                break
    finally:
        env.close()

    half_track = 2.4
    mean_abs_position = float(np.mean(np.abs(cart_positions))) if cart_positions else 0.0
    return {
        "steps": steps,
        "mean_abs_cart_position": mean_abs_position,
        "mean_abs_cart_fraction": mean_abs_position / half_track,
        "gif_bytes": frames_to_gif(frames) if frames else b"",
    }


def count_reward_terms(weights: dict[str, Any]) -> int:
    """Count how many signal terms the student placed in the reward function."""
    tokens = weights.get("reward_tokens")
    if isinstance(tokens, list) and tokens:
        return sum(
            1
            for token in tokens
            if isinstance(token, dict)
            and (token.get("type") == "term" or "signal" in token)
        )
    return len(weights.get("reward_terms", []))


def reward_summary_text(weights: dict[str, Any]) -> str:
    terms = weights.get("reward_terms", [])
    if not terms:
        return "(empty reward function)"
    parts = []
    for term in terms:
        factor = term.get("factor", 1.0)
        transform = str(term.get("transform", "raw"))
        label = reward_signal_display(str(term.get("signal", "?")), transform)
        parts.append(f"{factor:g} x {label}")
    return " + ".join(parts)


def safe_filename_part(value: str, fallback: str = "student") -> str:
    cleaned = "".join(character if character.isalnum() or character in ("-", "_") else "_" for character in value.strip())
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return cleaned[:48] or fallback


def student_identity_from_state(st: Any) -> dict[str, str]:
    return {
        "name": str(st.session_state.get("student_name", "")).strip(),
        "student_id": str(st.session_state.get("student_id", "")).strip(),
        "section": str(st.session_state.get("student_section", "")).strip(),
    }


def render_student_identity(st: Any) -> dict[str, str]:
    with st.expander("Student info for the submission", expanded=False):
        st.caption("Optional, but useful for identifying the autosaved submission folder.")
        st.text_input("Name", key="student_name")
        st.text_input("Student ID or email", key="student_id")
        st.text_input("Section", key="student_section")
    return student_identity_from_state(st)


def build_mission_submission_payload(
    mission_id: str,
    result: TrainingResult,
    weights: dict[str, Any],
    metrics: dict[str, Any],
    explanations: dict[str, str],
    identity: dict[str, str] | None = None,
    activity_gifs: dict[str, bytes] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "mission": mission_id,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "student": identity or {},
        "algorithm": result.algorithm,
        "observations": list(result.settings.observation_features),
        "actions": list(result.settings.action_forces),
        "reward_function": reward_summary_text(weights),
        "settings": {
            "episodes": result.settings.episodes,
            "max_steps": result.settings.max_steps,
            "learning_rate": result.settings.learning_rate,
            "gamma": result.settings.gamma,
            "epsilon": result.settings.epsilon,
            "epsilon_min": result.settings.epsilon_min,
            "seed": result.settings.seed,
            "q_bins_per_feature": result.settings.q_bins_per_feature,
            "pole_length": result.settings.pole_length,
            "ethical_exploration": result.settings.ethical_exploration,
            "animal_position": result.settings.animal_position,
            "animal_radius": result.settings.animal_radius,
        },
        "metrics": {
            "steps": metrics.get("steps"),
            "mean_abs_cart_fraction": round(metrics.get("mean_abs_cart_fraction", 0.0), 4),
        },
        "explanations": explanations,
        "activity_gifs": sorted((activity_gifs or {}).keys()),
    }


def render_submission_markdown(
    mission_id: str,
    result: TrainingResult,
    weights: dict[str, Any],
    metrics: dict[str, Any],
    explanations: dict[str, str],
    identity: dict[str, str] | None = None,
) -> str:
    identity = identity or {}
    lines = [
        f"# {mission_id.replace('_', ' ').title()} submission",
        "",
        f"- Name: {identity.get('name') or '(not provided)'}",
        f"- Student ID/email: {identity.get('student_id') or '(not provided)'}",
        f"- Section: {identity.get('section') or '(not provided)'}",
        f"- Algorithm: {result.algorithm}",
        f"- Observations: {', '.join(result.settings.observation_features)}",
        f"- Actions: {', '.join(f'{f:g}' for f in result.settings.action_forces)}",
        f"- Reward function: {reward_summary_text(weights)}",
        f"- Steps balanced: {metrics.get('steps')}",
        f"- Mean cart offset: {metrics.get('mean_abs_cart_fraction', 0.0):.1%} of half-track",
        "",
        "## Explanations",
    ]
    for key, value in explanations.items():
        lines.append(f"\n### {key.title()}\n\n{value.strip() or '(no answer)'}")
    return "\n".join(lines)


def learning_curve_csv(result: TrainingResult) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["episode", "shaped_reward", "cartpole_score", "episode_length"])
    for index, (shaped, env_return, length) in enumerate(
        zip(result.returns, result.env_returns, result.episode_lengths),
        start=1,
    ):
        writer.writerow([index, shaped, env_return, length])
    return buffer.getvalue()


def build_mission_export_zip(
    mission_id: str,
    result: TrainingResult,
    weights: dict[str, Any],
    metrics: dict[str, Any],
    explanations: dict[str, str],
    identity: dict[str, str] | None = None,
    activity_gifs: dict[str, bytes] | None = None,
) -> bytes:
    payload = build_mission_submission_payload(
        mission_id,
        result,
        weights,
        metrics,
        explanations,
        identity,
        activity_gifs,
    )
    activity_gifs = activity_gifs or {}
    manifest = {
        "schema_version": 1,
        "created_at": payload["timestamp"],
        "mission": mission_id,
        "files": [
            "submission.json",
            "explanation.md",
            "learning_curve.csv",
            "run.gif" if metrics.get("gif_bytes") else "",
            *[f"activity_gifs/{name}" for name in activity_gifs],
        ],
        "collection_note": (
            "For the normal local workflow, save the Git-ready student_submission "
            "folder, commit it, push it, and submit the GitHub commit link. This ZIP "
            "is a backup export."
        ),
    }
    manifest["files"] = [filename for filename in manifest["files"] if filename]

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("submission.json", json.dumps(payload, indent=2))
        archive.writestr(
            "explanation.md",
            render_submission_markdown(mission_id, result, weights, metrics, explanations, identity),
        )
        archive.writestr("learning_curve.csv", learning_curve_csv(result))
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        if metrics.get("gif_bytes"):
            archive.writestr("run.gif", metrics["gif_bytes"])
        for name, content in activity_gifs.items():
            archive.writestr(f"activity_gifs/{name}", content)
    return buffer.getvalue()


def save_mission_submission(
    mission_id: str,
    result: TrainingResult,
    weights: dict[str, Any],
    metrics: dict[str, Any],
    explanations: dict[str, str],
    identity: dict[str, str] | None = None,
    activity_gifs: dict[str, bytes] | None = None,
) -> Path:
    """Write the student's gif + written explanation so it can be pushed to git."""
    target = SUBMISSIONS_DIR / mission_id
    target.mkdir(parents=True, exist_ok=True)

    if metrics.get("gif_bytes"):
        (target / "run.gif").write_bytes(metrics["gif_bytes"])

    submission = build_mission_submission_payload(
        mission_id,
        result,
        weights,
        metrics,
        explanations,
        identity,
        activity_gifs,
    )
    (target / "submission.json").write_text(json.dumps(submission, indent=2))
    (target / "explanation.md").write_text(
        render_submission_markdown(mission_id, result, weights, metrics, explanations, identity)
    )
    (target / "learning_curve.csv").write_text(learning_curve_csv(result))
    if activity_gifs:
        gif_target = target / "activity_gifs"
        gif_target.mkdir(parents=True, exist_ok=True)
        for name, content in activity_gifs.items():
            (gif_target / name).write_bytes(content)
    return target


AUTOSAVE_DIR = SUBMISSIONS_DIR / "autosave"


def mission_explanations_from_state(st: Any, mission_id: str) -> dict[str, str]:
    return {
        label: str(st.session_state.get(f"{mission_id}_explain_{suffix}", "")).strip()
        for label, suffix in (
            ("reward", "reward"),
            ("observation", "observation"),
            ("action", "action"),
            ("policy_map", "policy_map"),
        )
    }


def collect_autosaved_answers(st: Any) -> dict[str, Any]:
    """Merge visible widget answers into the durable accumulated response set."""
    accumulated = st.session_state.get("_autosaved_answers")
    if not isinstance(accumulated, dict):
        accumulated = {}
        responses_path = AUTOSAVE_DIR / "responses.json"
        try:
            saved = json.loads(responses_path.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                accumulated = {
                    "student": saved.get("student", {}),
                    "checkins": saved.get("checkins", {}),
                    "mission_explanations": saved.get("mission_explanations", {}),
                }
        except (OSError, ValueError, TypeError):
            pass

    student = accumulated.setdefault("student", {})
    for state_key, answer_key in (
        ("student_name", "name"),
        ("student_id", "student_id"),
        ("student_section", "section"),
    ):
        if state_key in st.session_state:
            student[answer_key] = str(st.session_state.get(state_key, "")).strip()

    checkins = accumulated.setdefault("checkins", {})
    prefix = "reflective_checkin_"
    for state_key in list(st.session_state):
        if not str(state_key).startswith(prefix):
            continue
        key_body = str(state_key)[len(prefix):]
        if key_body.endswith("_choice"):
            checkin_key, field = key_body[:-7], "choice"
        elif key_body.endswith("_note"):
            checkin_key, field = key_body[:-5], "note"
        else:
            continue
        checkins.setdefault(checkin_key, {})[field] = str(
            st.session_state.get(state_key, "")
        ).strip()

    explanations = accumulated.setdefault("mission_explanations", {})
    for mission_id in MISSION_ORDER:
        mission_answers = explanations.setdefault(mission_id, {})
        for label, suffix in (
            ("reward", "reward"),
            ("observation", "observation"),
            ("action", "action"),
            ("policy_map", "policy_map"),
        ):
            state_key = f"{mission_id}_explain_{suffix}"
            if state_key in st.session_state:
                mission_answers[label] = str(
                    st.session_state.get(state_key, "")
                ).strip()
        if not any(mission_answers.values()):
            explanations.pop(mission_id, None)

    normalized = {
        "student": student,
        "checkins": checkins,
        "mission_explanations": explanations,
    }
    st.session_state["_autosaved_answers"] = normalized
    return normalized


def autosaved_answers_markdown(answers: dict[str, Any]) -> str:
    student = answers.get("student", {})
    lines = [
        "# Autosaved RL pendulum responses",
        "",
        f"- Name: {student.get('name') or '(not provided)'}",
        f"- Student ID/email: {student.get('student_id') or '(not provided)'}",
        f"- Section: {student.get('section') or '(not provided)'}",
        "",
        "## Reflective check-ins",
        "",
    ]
    checkins = answers.get("checkins", {})
    if checkins:
        for key, response in sorted(checkins.items()):
            lines.append(f"### {key}")
            if response.get("choice"):
                lines.append(f"\n**Choice:** {response['choice']}")
            if response.get("note"):
                lines.append(f"\n{response['note']}")
            lines.append("")
    else:
        lines.append("_(none yet)_\n")
    lines.append("## Mission explanations\n")
    explanations = answers.get("mission_explanations", {})
    if explanations:
        for mission_id, response in sorted(explanations.items()):
            lines.append(f"### {mission_id}\n")
            for label, value in response.items():
                if value:
                    lines.append(f"**{label.replace('_', ' ').title()}:** {value}\n")
    else:
        lines.append("_(none yet)_\n")
    return "\n".join(lines)


def autosave_student_answers(st: Any) -> None:
    """Persist response text on every Streamlit rerun, writing only on change."""
    try:
        answers = collect_autosaved_answers(st)
        serialized = json.dumps(answers, sort_keys=True, default=str)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        if st.session_state.get("_answers_autosave_digest") == digest:
            return
        AUTOSAVE_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            **answers,
        }
        (AUTOSAVE_DIR / "responses.json").write_text(
            json.dumps(payload, indent=2, default=str), encoding="utf-8"
        )
        (AUTOSAVE_DIR / "responses.md").write_text(
            autosaved_answers_markdown(answers), encoding="utf-8"
        )
        st.session_state["_answers_autosave_digest"] = digest
        st.session_state["_answers_autosave_last"] = payload["saved_at"]
        st.session_state.pop("_answers_autosave_error", None)
    except Exception as error:
        st.session_state["_answers_autosave_error"] = str(error)


def finish_streamlit_autosave(st: Any) -> None:
    autosave_student_answers(st)
    error = st.session_state.get("_answers_autosave_error")
    if error:
        st.sidebar.warning(f"Could not autosave answers: {error}")
        return
    last_saved = st.session_state.get("_answers_autosave_last")
    if last_saved:
        st.sidebar.caption(f"Answers automatically saved at {last_saved}.")


def autosave_training_run(
    st: Any,
    activity_id: str,
    result: TrainingResult,
    replay: dict[str, Any],
) -> Path:
    """Save the latest trained policy replay and compact run data automatically."""
    target = SUBMISSIONS_DIR / safe_filename_part(activity_id, "activity")
    gif_bytes = bytes(replay.get("gif_bytes") or b"")
    run_data = {
        "activity": activity_id,
        "algorithm": result.algorithm,
        "observations": list(result.settings.observation_features),
        "actions": list(result.settings.action_forces),
        "reward_function": reward_summary_text(result.reward_weights),
        "episodes": len(result.returns),
        "evaluation": {
            "steps": replay.get("length"),
            "cartpole_score": replay.get("env_score"),
            "shaped_reward": replay.get("shaped"),
        },
    }
    fingerprint = json.dumps(run_data, sort_keys=True, default=str).encode("utf-8")
    fingerprint += hashlib.sha256(gif_bytes).digest()
    digest = hashlib.sha256(fingerprint).hexdigest()
    digest_key = f"_training_autosave_digest_{safe_filename_part(activity_id)}"
    if st.session_state.get(digest_key) == digest:
        return target
    try:
        target.mkdir(parents=True, exist_ok=True)
        if gif_bytes.startswith((b"GIF87a", b"GIF89a")):
            (target / "run.gif").write_bytes(gif_bytes)
        payload = {
            "schema_version": 1,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            **run_data,
        }
        (target / "latest_run.json").write_text(
            json.dumps(payload, indent=2, default=str), encoding="utf-8"
        )
        (target / "learning_curve.csv").write_text(
            learning_curve_csv(result), encoding="utf-8"
        )
        st.session_state[digest_key] = digest
        st.session_state.pop("_submission_autosave_error", None)
    except Exception as error:
        st.session_state["_submission_autosave_error"] = str(error)
    return target


def autosave_checked_mission(
    st: Any,
    mission_id: str,
    result: TrainingResult,
    weights: dict[str, Any],
    metrics: dict[str, Any],
    explanations: dict[str, str],
    identity: dict[str, str],
) -> Path:
    """Keep the checked mission folder current as explanations are edited."""
    payload = build_mission_submission_payload(
        mission_id, result, weights, metrics, explanations, identity
    )
    signature_payload = dict(payload)
    signature_payload.pop("timestamp", None)
    gif_bytes = bytes(metrics.get("gif_bytes") or b"")
    fingerprint = json.dumps(signature_payload, sort_keys=True, default=str).encode("utf-8")
    fingerprint += hashlib.sha256(gif_bytes).digest()
    digest = hashlib.sha256(fingerprint).hexdigest()
    digest_key = f"_checked_mission_autosave_digest_{mission_id}"
    target = SUBMISSIONS_DIR / mission_id
    if st.session_state.get(digest_key) == digest:
        return target
    try:
        save_mission_submission(
            mission_id, result, weights, metrics, explanations, identity
        )
        st.session_state[digest_key] = digest
        st.session_state.pop("_submission_autosave_error", None)
    except Exception as error:
        st.session_state["_submission_autosave_error"] = str(error)
    return target


def mark_mission_complete(st: Any, mission_id: str) -> None:
    progress = list(st.session_state.get("mission_progress", []))
    if mission_id not in progress:
        progress.append(mission_id)
        st.session_state["mission_progress"] = progress


def render_instructor_controls(st: Any) -> None:
    with st.sidebar.expander("Instructor controls"):
        if not st.session_state.get("instructor_unlocked", False):
            password = st.text_input("Master password", type="password", key="instructor_password_input")
            if st.button("Unlock", key="instructor_unlock"):
                if password == instructor_password(st):
                    st.session_state["instructor_unlocked"] = True
                    st.success("Unlocked.")
                    request_streamlit_rerun(st)
                else:
                    st.error("Wrong password.")
            return

        st.success("Instructor mode unlocked.")
        page_options = {
            "Home": "intro",
            "RL concepts": "rl_concepts",
            "Background": "background",
            "Meet the pendulum": "pendulum_intro",
            "Observation slides": "observation_demo",
            "Action slides": "action_demo",
            "Algorithm slides": "algorithm_demo",
            "Reward slides": "reward_demo",
            "Lab": "lab",
        }
        current_stage = str(st.session_state.get("app_stage", "lab"))
        page_labels = list(page_options)
        current_page_index = next(
            (index for index, label in enumerate(page_labels) if page_options[label] == current_stage),
            page_labels.index("Lab"),
        )
        selected_page = st.selectbox("Jump to page", page_labels, index=current_page_index)
        if st.button("Go", key="instructor_go_page"):
            set_app_stage(st, page_options[selected_page])

        mission_options = {
            "Mission 1": ("mission_1", None),
            "Mission 2": ("mission_2", None),
            "Mission 3": ("mission_3", None),
            "Bonus menu": ("bonus", None),
            "Bonus 1: one-term reward": ("bonus", "one_term"),
            "Bonus 2: swing-up": ("bonus", "swingup"),
            "Bonus 3: pole length": ("bonus", "pole_length"),
        }
        selected_mission = st.selectbox("Jump to mission", list(mission_options))
        if st.button("Switch mission", key="instructor_switch_mission"):
            mission_id, bonus_task = mission_options[selected_mission]
            st.session_state["mission_override"] = mission_id
            st.session_state["bonus_task"] = bonus_task
            set_app_stage(st, "lab")

        if st.button("Resume normal mission flow", key="instructor_resume_flow"):
            st.session_state.pop("mission_override", None)
            st.session_state["bonus_task"] = None
            set_app_stage(st, "lab")

        if st.button("Lock instructor mode", key="instructor_lock"):
            st.session_state["instructor_unlocked"] = False
            request_streamlit_rerun(st)


def render_mission_explanations(st: Any, mission_id: str) -> dict[str, str]:
    st.markdown("**Explain your design choices** (saved for grading):")
    reward_text = st.text_area(
        "Why did you choose this reward function?",
        key=f"{mission_id}_explain_reward",
        height=90,
    )
    observation_text = st.text_area(
        "Why these observations?",
        key=f"{mission_id}_explain_observation",
        height=90,
    )
    action_text = st.text_area(
        "Why these actions?",
        key=f"{mission_id}_explain_action",
        height=90,
    )
    policy_map_text = st.text_area(
        "Look at the policy maps as the pendulum version of the grid-game notebook. What do the preferred push and state value tell you about what your agent learned?",
        key=f"{mission_id}_explain_policy_map",
        height=110,
    )
    return {
        "reward": reward_text,
        "observation": observation_text,
        "action": action_text,
        "policy_map": policy_map_text,
    }


MISSION_STYLE = """
<style>
.mission-banner { border:1px solid #d0d5dd; border-left:6px solid #2e90fa; border-radius:10px; padding:1rem 1.3rem; margin:0.3rem 0 0.9rem; background:#f5faff; }
.mission-banner.bonus { border-left-color:#7a5af8; background:#f6f4ff; }
.mission-step { font-size:0.85rem; font-weight:800; letter-spacing:0.04em; color:#1570cd; text-transform:uppercase; }
.mission-step.bonus { color:#5925dc; }
.mission-title { font-size:1.5rem; font-weight:800; color:#101828; margin:0.15rem 0 0.35rem; }
.mission-task { font-size:1.15rem; line-height:1.5; color:#344054; }
.mission-unlock { font-size:1rem; color:#475467; margin-top:0.45rem; }
.mission-dots { margin-top:0.6rem; }
.mission-dot { display:inline-block; width:0.7rem; height:0.7rem; border-radius:50%; margin-right:0.35rem; background:#d0d5dd; }
.mission-dot.done { background:#12b76a; }
.mission-dot.current { background:#2e90fa; }
.bonus-pick { border:2px solid #7a5af8; border-radius:12px; padding:1.1rem 1.3rem; margin:0.6rem 0; background:#ffffff; }
.bonus-pick h4 { margin:0 0 0.4rem; font-size:1.25rem; color:#5925dc; }
.bonus-pick p { font-size:1.05rem; color:#344054; margin:0; }
</style>
"""


def render_mission_header(st: Any, context: dict[str, Any]) -> None:
    """The mission-driven banner that owns the top of the lab page."""
    st.markdown(MISSION_STYLE, unsafe_allow_html=True)
    progress = set(st.session_state.get("mission_progress", []))
    current = active_mission(st)
    is_bonus = current == "bonus"

    dots = []
    for mission_id in MISSION_ORDER:
        if mission_id in progress:
            dots.append('<span class="mission-dot done"></span>')
        elif mission_id == current:
            dots.append('<span class="mission-dot current"></span>')
        else:
            dots.append('<span class="mission-dot"></span>')
    dots_html = '<div class="mission-dots">' + "".join(dots) + " &nbsp; " + f"{len(progress)}/3 missions complete</div>"

    step_label = "Bonus mode" if is_bonus else f"Mission {MISSION_ORDER.index(current) + 1} of 3"
    banner_class = "mission-banner bonus" if is_bonus else "mission-banner"
    step_class = "mission-step bonus" if is_bonus else "mission-step"
    unlock_html = f'<div class="mission-unlock">{context["unlock"]}</div>' if context.get("unlock") else ""
    st.markdown(
        f'<div class="{banner_class}">'
        f'<div class="{step_class}">{step_label}</div>'
        f'<div class="mission-title">{context["title"]}</div>'
        f'<div class="mission-task">{context["task"]}</div>'
        f'{unlock_html}{dots_html}</div>',
        unsafe_allow_html=True,
    )

    if is_bonus and not st.session_state.get("bonus_task"):
        st.markdown("**Pick a bonus challenge:**")
        pick_columns = st.columns(3)
        with pick_columns[0]:
            st.markdown(
                '<div class="bonus-pick"><h4>1 · One-term reward</h4>'
                '<p>Balance the pole with a reward function that uses exactly one term. Find the single signal that is enough.</p></div>',
                unsafe_allow_html=True,
            )
            if st.button("Start one-term reward", key="bonus_one_term", use_container_width=True):
                st.session_state["bonus_task"] = "one_term"
                st.rerun()
        with pick_columns[1]:
            st.markdown(
                '<div class="bonus-pick"><h4>2 · Swing-up</h4>'
                '<p>The pole starts hanging straight down. Design a reward that swings it all the way up and balances it.</p></div>',
                unsafe_allow_html=True,
            )
            if st.button("Start swing-up", key="bonus_swingup", use_container_width=True):
                st.session_state["bonus_task"] = "swingup"
                st.rerun()
        with pick_columns[2]:
            st.markdown(
                '<div class="bonus-pick"><h4>3 · Pole length</h4>'
                '<p>Change the pole length, retrain, and see how the policy changes. A longer pole has more rotational inertia, so it is easier to balance.</p></div>',
                unsafe_allow_html=True,
            )
            if st.button("Start pole length", key="bonus_pole_length", use_container_width=True):
                st.session_state["bonus_task"] = "pole_length"
                st.rerun()
    elif is_bonus and st.session_state.get("bonus_task"):
        if st.button("← Back to bonus menu", key="bonus_back"):
            st.session_state["bonus_task"] = None
            st.rerun()


def render_mission_check(
    st: Any,
    context: dict[str, Any],
    results: list[TrainingResult],
    weights: dict[str, Any],
    reflections_ready: bool = True,
) -> None:
    """Per-mission check + explanation + save, shown after the controls/training."""
    mission_id = context["id"]
    if mission_id not in MISSION_ORDER:
        return  # bonus tasks are open-ended, no pass/save gate
    latest = results[-1] if results else None

    st.divider()
    st.subheader("Mission check")

    if mission_id == "mission_1":
        st.info("Hint: if your model does not seem to converge well, try increasing your training episodes by clicking on the arrows in the top left to open the sidebar if it's not already open.")

    if mission_id == "mission_3":
        with st.expander("Need a hint?"):
            st.markdown(
                "Turn on the animal with the **Ethical exploration** controls, and make sure "
                "the agent gets the **distance to animal** observation so it can see where the "
                "animal is. Then balance as usual. In your reflection, think about whether your "
                "reward gives the agent any reason to avoid the animal."
            )

    if st.button(
        f"Check {context['title'].split('—')[0].strip()}",
        key=f"check_{mission_id}",
        type="primary",
        disabled=latest is not None and not reflections_ready,
    ):
        if latest is None:
            st.warning("Train an agent first, then run the check.")
        else:
            passed, message, metrics = mission_check_result(mission_id, latest, weights)
            st.session_state[f"{mission_id}_metrics"] = metrics
            st.session_state[f"{mission_id}_passed"] = passed
            (st.success if passed else st.error)(message)
    if latest is not None and not reflections_ready:
        st.caption("Answer the replay and policy-map check-ins above before running the mission check.")

    metrics = st.session_state.get(f"{mission_id}_metrics")
    if st.session_state.get(f"{mission_id}_passed") and metrics and latest is not None:
        if metrics.get("gif_bytes"):
            st.image(metrics["gif_bytes"], width="stretch")
        identity = render_student_identity(st)
        explanations = render_mission_explanations(st, mission_id)
        explanations_complete = all(value.strip() for value in explanations.values())
        path = autosave_checked_mission(
            st,
            mission_id,
            latest,
            latest.reward_weights,
            metrics,
            explanations,
            identity,
        )
        autosave_error = st.session_state.get("_submission_autosave_error")
        if autosave_error:
            st.warning(f"Could not autosave this mission: {autosave_error}")
        else:
            st.caption(
                f"Run GIF, learning curve, settings, metrics, and written responses are "
                f"automatically saved to `{path.relative_to(Path(__file__).resolve().parent)}`."
            )
        if not explanations_complete:
            st.caption("Answer all four explanation prompts before continuing to the next mission.")

        if st.button(
            "Continue to next mission",
            key=f"save_{mission_id}",
            disabled=not explanations_complete,
        ):
            mark_mission_complete(st, mission_id)
            # A trained policy belongs to the mission whose controls produced it.
            # Start the next mission with an empty workspace so an old replay is
            # never displayed or accidentally checked against new requirements.
            st.session_state.pop("results", None)
            st.session_state.pop("latest_replay", None)
            st.session_state.pop("results_view", None)
            st.rerun()


def mission_check_result(
    mission_id: str,
    latest: TrainingResult,
    weights: dict[str, Any],
) -> tuple[bool, str, dict[str, Any]]:
    """Evaluate the active mission's pass condition and return (passed, message, metrics)."""
    if mission_id == "mission_1" and latest.algorithm != "Q-learning":
        return False, "Mission 1 requires a Q-table (Algorithm is forced to Q-learning).", {}
    if mission_id == "mission_2" and latest.algorithm != "DQN":
        return False, "Mission 2 requires a DQN (Algorithm is forced to DQN).", {}

    if mission_id == "mission_3" and "animal_distance" not in latest.settings.observation_features:
        return False, "Mission 3 needs the agent to see the animal. Add the distance-to-animal observation, then retrain.", {}

    metrics = evaluate_mission_run(latest)
    steps = metrics["steps"]
    if mission_id == "mission_1":
        if steps >= 100:
            return True, f"Balanced {steps} steps. Goal met! Explain your choices below; your work saves automatically.", metrics
        return False, f"Only {steps} steps (need 100). Adjust and retrain.", metrics
    if mission_id == "mission_2":
        fraction = metrics["mean_abs_cart_fraction"]
        if steps >= 100 and fraction < 0.25:
            return True, f"Balanced {steps} steps with average offset {fraction:.0%} of half-track. Goal met!", metrics
        if steps < 100:
            return False, f"Only {steps} steps (need 100).", metrics
        return False, f"Balanced long enough, but average offset {fraction:.0%} of half-track is too far from center (need under 25%).", metrics
    # mission_3: ethical observation — balance while the agent can see the animal
    if steps >= 100:
        return True, f"Balanced {steps} steps with the animal observation. Goal met: Mission 3 needs at least 100 steps.", metrics
    return False, f"Only {steps} steps. Mission 3 success requires at least 100 balanced steps with the animal observation.", metrics


def run_streamlit_app() -> None:
    modules = require_dependencies("streamlit", "numpy", "pandas", "matplotlib.pyplot", "gymnasium", "torch")
    st = modules["streamlit"]
    stage = str(st.session_state.get("app_stage", "intro"))
    lab_stage = stage == "lab"

    st.set_page_config(
        page_title="Live RL Pendulum Lab",
        page_icon="RL",
        layout="wide",
        initial_sidebar_state="expanded" if lab_stage else "collapsed",
    )
    set_sidebar_default_for_stage(st, expanded=lab_stage)
    scroll_to_top_if_requested(st)
    render_instructor_controls(st)

    if stage == "intro":
        render_intro_page(st)
        finish_streamlit_autosave(st)
        return
    if stage == "rl_concepts":
        render_rl_concepts_page(st)
        finish_streamlit_autosave(st)
        return
    if stage == "background":
        render_background_page(st)
        finish_streamlit_autosave(st)
        return
    if stage == "pendulum_intro":
        render_pendulum_intro_page(st)
        finish_streamlit_autosave(st)
        return
    if stage == "observation_demo":
        render_observation_slideshow_page(st)
        finish_streamlit_autosave(st)
        return
    if stage == "action_demo":
        render_action_slideshow_page(st)
        finish_streamlit_autosave(st)
        return
    if stage == "reward_demo":
        render_reward_slideshow_page(st)
        finish_streamlit_autosave(st)
        return
    if stage == "algorithm_demo":
        render_algorithm_demo_page(st)
        finish_streamlit_autosave(st)
        return
    st.title("Live RL Pendulum Lab")
    render_tutorial_styles(st)

    context = mission_context(st)
    render_mission_header(st, context)

    settings = sidebar_settings(st, forced_algorithm=context["forced_algorithm"])
    ethical_reflection_ready = True
    if context["show_ethical"]:
        ethical_controls(st, settings, locked=bool(context.get("locked_ethical", False)))
        if context.get("locked_ethical", False):
            ethical_reflection_ready = bool(
                reflective_checkin_response(st, "ethical_observation_vs_reward")["complete"]
            )
    else:
        settings.ethical_exploration = False
        settings.random_start_around_animal = False
    observation_features, action_forces, initial_state, terminate_on_angle = behavior_controls(
        st,
        show_start_controls=context["show_start_controls"],
        forced_start=context["forced_start"],
    )
    settings.observation_features = observation_features
    settings.action_forces = action_forces
    settings.initial_state = initial_state
    settings.terminate_on_angle = terminate_on_angle
    if context.get("show_pole_length"):
        st.subheader("Pole length")
        settings.pole_length = float(
            st.slider(
                "Half-pole length",
                0.25,
                1.5,
                0.5,
                0.05,
                help="Gymnasium's default is 0.5. A longer pole has more rotational inertia, tips more slowly, and is easier to balance.",
            )
        )
        st.caption(
            f"Pole length {settings.pole_length:g} (default 0.5). Longer poles are easier to balance because of greater rotational inertia."
        )
    weights = reward_controls(st)
    weights["animal_position"] = settings.animal_position
    weights["animal_radius"] = settings.animal_radius if settings.ethical_exploration else 0.0
    render_state_legend(st)

    render_tutorial_anchor(st, "train")
    render_tutorial_callout(st, "train")
    # Latch the click in session state so the training intent survives an extra
    # rerun a component may trigger right after the click (which would otherwise
    # consume the transient st.button() return and make the first click appear
    # to do nothing). The latch is only cleared once training actually runs, so
    # a discarded/replaced rerun cannot drop it.
    if st.button("Train agent", type="primary"):
        st.session_state["train_requested"] = True
    train_button = bool(st.session_state.get("train_requested", False))
    if train_button and not observation_features:
        st.session_state.pop("train_requested", None)
        st.warning(
            "Your observation box is empty, so the agent can't see anything and "
            "won't converge. Drag at least one observation (e.g. pole angle and "
            "pole spin) into the box, then train again."
        )
        train_button = False
    if train_button and count_reward_terms(weights) == 0:
        st.session_state.pop("train_requested", None)
        st.warning(
            "Your reward function is empty, so every step earns 0 reward and the "
            "agent has nothing to learn: the notebook gets no useful nudges and the "
            "reward curve stays flat at 0. Drag at least one reward signal into the "
            "reward box, then train again."
        )
        train_button = False
    if train_button:
        st.session_state.pop("train_requested", None)
        results: list[TrainingResult] = []
        runs = [(weights, "Current reward")]

        progress = st.progress(0.0)
        status = st.empty()
        reward_chart_caption = st.empty()
        reward_chart = st.empty()
        reward_chart_caption.caption(
            "Live total reward per episode. This is the same idea as the grid game's "
            "score graph: as rewards nudge the notebook in the right direction, the "
            "total reward should climb toward the best behavior your reward function describes."
        )

        for run_index, (run_weights, label) in enumerate(runs):
            def update_progress(
                done: int,
                total: int,
                returns: list[float],
                run_index: int = run_index,
                label: str = label,
            ) -> None:
                overall = (run_index + done / total) / len(runs)
                progress.progress(min(1.0, overall))
                status.write(f"Training {label}: episode {done}/{total}")
                # Redraw the live reward curve, throttled so it stays responsive.
                if returns and (done % 5 == 0 or done == total):
                    reward_chart.line_chart(
                        {"shaped reward": list(returns)},
                        height=220,
                    )

            with st.spinner(f"Training {label}..."):
                result = train_agent(
                    settings,
                    run_weights,
                    update_progress,
                    label,
                )
                results.append(result)

        progress.progress(1.0)
        status.write("Training complete. Rendering one example episode...")
        # Any previous check is invalid once the student trains a replacement
        # policy, even if the new run uses similar settings.
        st.session_state.pop(f"{context['id']}_passed", None)
        st.session_state.pop(f"{context['id']}_metrics", None)
        st.session_state["results"] = results
        with st.spinner("Rendering the learned policy..."):
            st.session_state["latest_replay"] = build_replay_cache(results[-1])
        st.session_state["results_view"] = "Replay"

        # Clear the training progress UI so the learned-policy replay takes its
        # place instead of appearing below leftover progress widgets.
        progress.empty()
        status.empty()
        reward_chart_caption.empty()
        reward_chart.empty()

    results = st.session_state.get("results", [])
    reflections_ready = True
    if results:
        sync_tutorial_results_view(st, True)
        # Show everything a completed training produced at once: the learned-policy
        # replay, the learning curve + metrics, and the policy map.
        replay_check = render_evaluation(st, results[-1])
        replay = st.session_state.get("latest_replay", {})
        if isinstance(replay, dict):
            run_path = autosave_training_run(st, context["id"], results[-1], replay)
            autosave_error = st.session_state.get("_submission_autosave_error")
            if autosave_error:
                st.warning(f"Could not autosave this run: {autosave_error}")
            else:
                st.caption(
                    "Latest replay GIF, training settings, and learning curve automatically "
                    f"saved to `{run_path.relative_to(Path(__file__).resolve().parent)}`."
                )
        render_tutorial_anchor(st, "curve")
        render_tutorial_callout(st, "curve")
        st.subheader("Learning curve")
        st.pyplot(make_learning_curve(results), width="stretch")
        render_metrics(st, results)
        policy_check = render_policy_visualization(st, results)
        reflections_ready = bool(
            replay_check["complete"]
            and policy_check["complete"]
            and ethical_reflection_ready
        )
    else:
        render_tutorial_anchor(st, "replay")
        render_tutorial_callout(st, "replay")
        render_tutorial_anchor(st, "curve")
        render_tutorial_callout(st, "curve")
        render_tutorial_anchor(st, "policy")
        render_tutorial_callout(st, "policy")
        st.info("Choose reward weights, then train an agent.")

    render_mission_check(st, context, results, weights, reflections_ready)

    with st.expander("Q-learning vs DQN"):
        render_algorithm_comparison(st)
    finish_streamlit_autosave(st)


def precompute_demo_assets() -> None:
    """Train every fixed slide demo once and save the rendered assets to disk.

    Run this with `python pendulum_rl_live.py --precompute` so the slide pages
    load instantly instead of training the demo policies on first view.
    """
    DEMO_ASSETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    assets: dict[str, Any] = {}

    print("Precomputing intro demo gif...")
    try:
        assets["intro_gif"] = make_intro_demo_gif()
    except Exception as error:
        print(f"  intro gif failed: {error}")
        assets["intro_gif"] = b""

    print("Precomputing observation demo...")
    assets["observation_demo"] = _build_observation_demo()
    print("Precomputing action demo...")
    assets["action_demo"] = _build_action_demo()
    print("Precomputing reward demo...")
    assets["reward_demo"] = _build_reward_demo()
    print("Precomputing Q-table vs DQN demo (maps)...")
    assets["algorithm_demo"] = _build_algorithm_demo_assets()

    with open(DEMO_ASSETS_PATH, "wb") as handle:
        pickle.dump(assets, handle)
    size_kb = DEMO_ASSETS_PATH.stat().st_size / 1024
    print(f"Saved {DEMO_ASSETS_PATH} ({size_kb:.0f} KB).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Live RL pendulum teaching activity.")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run tiny Q-learning and DQN training checks without Streamlit.",
    )
    parser.add_argument(
        "--precompute",
        action="store_true",
        help="Train all fixed slide demos once and cache their gifs/plots to disk.",
    )
    args = parser.parse_args()

    if args.smoke_test:
        run_smoke_test()
    elif args.precompute:
        precompute_demo_assets()
    else:
        run_streamlit_app()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
