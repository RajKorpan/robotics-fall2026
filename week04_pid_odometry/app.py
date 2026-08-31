"""Local Streamlit lab for teaching PID control and differential-drive odometry.

Run locally with:

    streamlit run week04_pid_odometry/app.py

Run a non-interactive sanity check with:

    python week04_pid_odometry/app.py --smoke-test
"""

from __future__ import annotations

import argparse
import base64
import csv
import functools
import hashlib
import html as html_module
import io
import json
import math
import os
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


os.environ.setdefault("MPLCONFIGDIR", "/tmp/pid_odometry_matplotlib")


# ---------------------------------------------------------------------------
# Lazy imports -- keep startup fast and produce friendly error messages.
# ---------------------------------------------------------------------------

def require(module_name: str) -> Any:
    import importlib

    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as error:
        raise SystemExit(
            f"Missing dependency: {module_name}\n\n"
            "From the repo root, activate the virtual environment and run:\n"
            "  python -m pip install -r requirements.txt"
        ) from error


st: Any = None  # set during run_streamlit_app / guarded for smoke-test
np: Any = None
plt: Any = None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DT = 0.02
MISSION_ORDER = ("mission_1", "mission_2", "mission_3")
DEFAULT_INSTRUCTOR_PASSWORD = "pid-odometry-master"
SUBMISSIONS_DIR = Path(__file__).resolve().parent / "student_submission"

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class PIDResult:
    time: list[float]
    position: list[float]
    velocity: list[float]
    command: list[float]
    error: list[float]
    p_term: list[float]
    i_term: list[float]
    d_term: list[float]
    target: float


@dataclass
class OdomResult:
    time: list[float]
    true_x: list[float]
    true_y: list[float]
    true_theta: list[float]
    odom_x: list[float]
    odom_y: list[float]
    odom_theta: list[float]
    left_distance: list[float]
    right_distance: list[float]
    commands: list[tuple[float, float]]


@dataclass
class OpenLoopTrial:
    battery: float
    friction: float
    final_distance: float
    error: float


@dataclass
class WaypointNavResult:
    time: list[float]
    true_x: list[float]
    true_y: list[float]
    true_theta: list[float]
    odom_x: list[float]
    odom_y: list[float]
    odom_theta: list[float]
    waypoints: list[tuple[float, float]]
    reached_flags: list[bool]          # per-waypoint: did the robot BELIEVE it arrived
    true_gap_at_reach: list[float]     # true distance from waypoint when it believed it arrived
    heading_error: list[float]
    command: list[float]
    num_reached: int                   # waypoints the robot believed it reached
    num_truly_reached: int             # waypoints it actually got close to (ground truth)
    final_true_gap: float              # true distance to the last waypoint at the end
    mean_true_gap_at_reach: float      # avg ground-truth miss across believed-reached waypoints
    calibration_ratio: float           # wheel_radius_estimate / true_wheel_radius
    pedestrians: list[tuple[float, float]]   # fixed pedestrian positions near the path
    safe_radius: float                 # required clearance around each pedestrian (m)
    min_pedestrian_gap: float          # closest the robot's TRUE path came to any pedestrian
    hit_pedestrian: bool               # did the true path breach any pedestrian's safe radius


@dataclass
class PathFollowResult:
    time: list[float]
    true_x: list[float]
    true_y: list[float]
    true_theta: list[float]
    odom_x: list[float]
    odom_y: list[float]
    odom_theta: list[float]
    path_x: list[float]
    path_y: list[float]
    heading_error: list[float]
    command: list[float]
    mean_tracking_error: float
    max_tracking_error: float


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def wrap_angle(theta: float) -> float:
    return ((float(theta) + math.pi) % (2 * math.pi)) - math.pi


# ---------------------------------------------------------------------------
# Streamlit components (declared lazily)
# ---------------------------------------------------------------------------

_PID_CONCEPTS_COMPONENT: Any | None = None


def pid_concepts_component(*, key: str = "pid_concepts") -> Any:
    global _PID_CONCEPTS_COMPONENT
    components = require("streamlit.components.v1")
    if _PID_CONCEPTS_COMPONENT is None:
        _PID_CONCEPTS_COMPONENT = components.declare_component(
            "pid_concepts",
            path=str(Path(__file__).parent / "pid_concepts"),
        )
    return _PID_CONCEPTS_COMPONENT(key=key)


_PID_PLAYGROUND_COMPONENT: Any | None = None


def pid_playground_component(*, key: str = "pid_playground") -> Any:
    global _PID_PLAYGROUND_COMPONENT
    components = require("streamlit.components.v1")
    if _PID_PLAYGROUND_COMPONENT is None:
        _PID_PLAYGROUND_COMPONENT = components.declare_component(
            "pid_playground",
            path=str(Path(__file__).parent / "pid_playground"),
        )
    return _PID_PLAYGROUND_COMPONENT(key=key)


_ODOMETRY_PLAYGROUND_COMPONENT: Any | None = None


def odometry_playground_component(*, key: str = "odometry_playground") -> Any:
    global _ODOMETRY_PLAYGROUND_COMPONENT
    components = require("streamlit.components.v1")
    if _ODOMETRY_PLAYGROUND_COMPONENT is None:
        _ODOMETRY_PLAYGROUND_COMPONENT = components.declare_component(
            "odometry_playground",
            path=str(Path(__file__).parent / "odometry_playground"),
        )
    return _ODOMETRY_PLAYGROUND_COMPONENT(key=key)


_ARM_PLAYGROUND_COMPONENT: Any | None = None


def arm_playground_component(*, key: str = "arm_playground") -> Any:
    global _ARM_PLAYGROUND_COMPONENT
    components = require("streamlit.components.v1")
    if _ARM_PLAYGROUND_COMPONENT is None:
        _ARM_PLAYGROUND_COMPONENT = components.declare_component(
            "arm_playground",
            path=str(Path(__file__).parent / "arm_playground"),
        )
    return _ARM_PLAYGROUND_COMPONENT(key=key)


_WAYPOINT_DRAW_COMPONENT: Any | None = None


def waypoint_draw_component(initial_state: dict[str, Any], *, key: str = "waypoint_draw") -> Any:
    """Mount the Mission 3 route planner and simulator as a CCv2 component."""
    global _WAYPOINT_DRAW_COMPONENT
    if _WAYPOINT_DRAW_COMPONENT is None:
        asset_dir = Path(__file__).parent / "waypoint_draw"
        _WAYPOINT_DRAW_COMPONENT = st.components.v2.component(
            "waypoint_draw_and_drive",
            html=(asset_dir / "component.html").read_text(encoding="utf-8"),
            css=(asset_dir / "component.css").read_text(encoding="utf-8"),
            js=(asset_dir / "component.js").read_text(encoding="utf-8"),
        )

    # Hydrate from the component widget's own current state. The separate
    # m3_component_state mirror is updated after mount, so using only that mirror
    # here makes the frontend one rerun stale after a drive completes.
    widget_state = st.session_state.get(key)
    if isinstance(widget_state, dict):
        live_state = widget_state.get("state")
    else:
        live_state = getattr(widget_state, "state", None)
    hydrated_state = live_state if isinstance(live_state, dict) else initial_state

    return _WAYPOINT_DRAW_COMPONENT(
        key=key,
        data={"state": hydrated_state},
        default={"state": hydrated_state},
        on_state_change=lambda: None,
        width="stretch",
        height="content",
    )


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

def request_streamlit_rerun() -> None:
    rerun = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if rerun is not None:
        rerun()


def set_stage(stage: str) -> None:
    st.session_state["stage"] = stage
    st.session_state["scroll_to_top_pending"] = True
    request_streamlit_rerun()


def scroll_to_top_if_requested() -> None:
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


def set_sidebar_default_for_stage(*, expanded: bool) -> None:
    action = "open" if expanded else "close"
    storage_key = "pidSidebarOpenedForLab" if expanded else "pidSidebarClosedBeforeLab"
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
              const label = (button.getAttribute("aria-label") || "") + " " + (button.title || "");
              if (shouldOpen) return label.toLowerCase().includes("open sidebar") || label.toLowerCase().includes("expand sidebar");
              return label.toLowerCase().includes("close sidebar") || label.toLowerCase().includes("collapse sidebar");
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


def is_network_url_session() -> bool:
    try:
        url = str(st.context.url or "")
    except Exception:
        return False
    if not url:
        return False
    host = url.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0].strip("[]").lower()
    return host not in {"", "localhost", "127.0.0.1", "::1", "0.0.0.0"}


# ---------------------------------------------------------------------------
# Check-in and bridge-card rendering
# ---------------------------------------------------------------------------

CHECKIN_STYLE = """
<style>
.checkin-card {
    border: 1px solid #d0d5dd;
    border-left: 6px solid #12b76a;
    border-radius: 10px;
    padding: 0.9rem 1.2rem;
    margin: 0.8rem 0 1rem;
    background: #f7fdf9;
}
.checkin-label {
    color: #027a48;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.checkin-title {
    color: #101828;
    font-size: 1.18rem;
    font-weight: 800;
    margin: 0.15rem 0 0.35rem;
}
.checkin-prompt {
    color: #344054;
    font-size: 1.02rem;
    line-height: 1.5;
}
</style>
"""

BRIDGE_STYLE = """
<style>
.bridge-card {
    border: 1px solid #bfdbfe;
    border-left: 6px solid #2563eb;
    border-radius: 10px;
    padding: 0.9rem 1.2rem;
    margin: 0.9rem 0;
    background: #eff6ff;
}
.bridge-label {
    color: #1d4ed8;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.bridge-title {
    color: #101828;
    font-size: 1.18rem;
    font-weight: 800;
    margin: 0.15rem 0 0.35rem;
}
.bridge-body {
    color: #344054;
    font-size: 1.02rem;
    line-height: 1.5;
}
</style>
"""


def checkin_key(key: str, suffix: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "_-" else "_" for char in key)
    return f"pid_odom_checkin_{cleaned}_{suffix}"


def checkin_response(key: str) -> dict[str, Any]:
    note = str(st.session_state.get(checkin_key(key, "note"), "")).strip()
    choice = str(st.session_state.get(checkin_key(key, "choice"), "")).strip()
    return {"note": note, "choice": choice, "complete": bool(note or choice)}


def render_checkin(
    *,
    key: str,
    title: str,
    prompt: str,
    label: str = "Check-in",
    choices: tuple[str, ...] = (),
    placeholder: str = "",
    required: bool = True,
) -> dict[str, Any]:
    st.markdown(CHECKIN_STYLE, unsafe_allow_html=True)
    st.markdown(
        '<div class="checkin-card">'
        f'<div class="checkin-label">{html_module.escape(label)}</div>'
        f'<div class="checkin-title">{html_module.escape(title)}</div>'
        f'<div class="checkin-prompt">{html_module.escape(prompt)}</div>'
        "</div>",
        unsafe_allow_html=True,
    )
    if choices:
        choice_key = checkin_key(key, "choice")
        current = st.session_state.get(choice_key)
        index = list(choices).index(current) if current in choices else None
        st.radio(
            "Choose one",
            choices,
            index=index,
            key=choice_key,
            horizontal=True,
            label_visibility="collapsed",
        )
    st.text_area(
        "Your answer",
        key=checkin_key(key, "note"),
        height=90,
        placeholder=placeholder,
    )
    response = checkin_response(key)
    if required and not response["complete"]:
        st.caption("Answer this check-in to continue.")
    return response


def render_bridge(title: str, body: str) -> None:
    st.markdown(BRIDGE_STYLE, unsafe_allow_html=True)
    st.markdown(
        '<div class="bridge-card">'
        '<div class="bridge-label">Connection to the next activity</div>'
        f'<div class="bridge-title">{html_module.escape(title)}</div>'
        f'<div class="bridge-body">{body}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Mission system
# ---------------------------------------------------------------------------

MISSION_STYLE = """
<style>
.mission-banner { border:1px solid #d0d5dd; border-left:6px solid #2e90fa; border-radius:10px; padding:1rem 1.3rem; margin:0.3rem 0 0.9rem; background:#f5faff; }
.mission-step { font-size:0.85rem; font-weight:800; letter-spacing:0.04em; color:#1570cd; text-transform:uppercase; }
.mission-title { font-size:1.5rem; font-weight:800; color:#101828; margin:0.15rem 0 0.35rem; }
.mission-task { font-size:1.15rem; line-height:1.5; color:#344054; }
.mission-unlock { font-size:1rem; color:#475467; margin-top:0.45rem; }
.mission-dots { margin-top:0.6rem; }
.mission-dot { display:inline-block; width:0.7rem; height:0.7rem; border-radius:50%; margin-right:0.35rem; background:#d0d5dd; }
.mission-dot.done { background:#12b76a; }
.mission-dot.current { background:#2e90fa; }
</style>
"""


def instructor_password() -> str:
    try:
        configured = str(st.secrets.get("instructor_password", "")).strip()
    except Exception:
        configured = ""
    return configured or os.environ.get("PID_MASTER_PASSWORD", DEFAULT_INSTRUCTOR_PASSWORD)


def active_mission() -> str:
    override = str(st.session_state.get("mission_override", ""))
    if override in MISSION_ORDER:
        return override
    progress = set(st.session_state.get("mission_progress", [])) & set(MISSION_ORDER)
    for mission_id in MISSION_ORDER:
        if mission_id not in progress:
            return mission_id
    return "mission_3"


def mission_context() -> dict[str, Any]:
    current = active_mission()
    if current == "mission_1":
        return {
            "id": "mission_1",
            "title": "Mission 1 -- Two-Link Robot Arm",
            "task": "Tune the shoulder and elbow PID controllers in the two-link arm until it settles cleanly on the target poses.",
            "unlock": "Pass the check to unlock Mission 2.",
        }
    if current == "mission_2":
        return {
            "id": "mission_2",
            "title": "Mission 2 -- Odometry Calibration",
            "task": "Calibrate wheel radius and track width so position error < 0.15 m and heading error < 8 degrees.",
            "unlock": "Pass the check to unlock Mission 3.",
        }
    if current == "mission_3":
        return {
            "id": "mission_3",
            "title": "Mission 3 -- Sidewalk Delivery",
            "task": "Draw a smooth safe route around pedestrians and visit all four waypoints in order. Tune heading PID and odometry until the real robot follows it precisely.",
            "unlock": "Pass the check to continue to the final submission.",
        }
    raise ValueError(f"Unknown mission: {current}")


def mark_mission_complete(mission_id: str) -> None:
    progress = [
        item for item in st.session_state.get("mission_progress", [])
        if item in MISSION_ORDER
    ]
    if mission_id not in progress:
        progress.append(mission_id)
        st.session_state["mission_progress"] = progress


def render_mission_header(context: dict[str, Any]) -> None:
    st.markdown(MISSION_STYLE, unsafe_allow_html=True)
    progress = set(st.session_state.get("mission_progress", [])) & set(MISSION_ORDER)
    current = active_mission()

    dots = []
    for mission_id in MISSION_ORDER:
        if mission_id in progress:
            dots.append('<span class="mission-dot done"></span>')
        elif mission_id == current:
            dots.append('<span class="mission-dot current"></span>')
        else:
            dots.append('<span class="mission-dot"></span>')
    dots_html = (
        '<div class="mission-dots">'
        + "".join(dots)
        + " &nbsp; "
        + f"{len(progress)}/3 missions complete</div>"
    )

    step_label = f"Mission {MISSION_ORDER.index(current) + 1} of 3"
    banner_class = "mission-banner"
    step_class = "mission-step"
    unlock_html = f'<div class="mission-unlock">{context["unlock"]}</div>' if context.get("unlock") else ""
    st.markdown(
        f'<div class="{banner_class}">'
        f'<div class="{step_class}">{step_label}</div>'
        f'<div class="mission-title">{context["title"]}</div>'
        f'<div class="mission-task">{context["task"]}</div>'
        f'{unlock_html}{dots_html}</div>',
        unsafe_allow_html=True,
    )


def render_mission_explanations(mission_id: str) -> dict[str, str]:
    st.markdown("**Explain your design choices** (saved for grading):")
    if mission_id == "mission_1":
        gain_text = st.text_area(
            "How did you tune the shoulder and elbow gains?",
            key=f"{mission_id}_explain_gains",
            height=90,
        )
        tradeoff_text = st.text_area(
            "What did gravity compensation change about the arm behavior?",
            key=f"{mission_id}_explain_tradeoff",
            height=90,
        )
        return {"joint_gains": gain_text, "gravity_comp": tradeoff_text}
    if mission_id == "mission_2":
        calibration_text = st.text_area(
            "How did you find the right wheel radius and track width?",
            key=f"{mission_id}_explain_calibration",
            height=90,
        )
        drift_text = st.text_area(
            "What causes odometry drift even after calibration?",
            key=f"{mission_id}_explain_drift",
            height=90,
        )
        return {"calibration": calibration_text, "drift": drift_text}
    if mission_id == "mission_3":
        heading_text = st.text_area(
            "How does the heading PID turn a goal point into a steering command?",
            key=f"{mission_id}_explain_heading",
            height=90,
        )
        integration_text = st.text_area(
            "Why does a well-tuned controller still fail when odometry is miscalibrated?",
            key=f"{mission_id}_explain_integration",
            height=90,
        )
        return {"heading": heading_text, "integration": integration_text}
    return {}


def mission_explanations_from_state(mission_id: str) -> dict[str, str]:
    keys = {
        "mission_1": {
            "joint_gains": "mission_1_explain_gains",
            "gravity_comp": "mission_1_explain_tradeoff",
        },
        "mission_2": {
            "calibration": "mission_2_explain_calibration",
            "drift": "mission_2_explain_drift",
        },
        "mission_3": {
            "heading": "mission_3_explain_heading",
            "integration": "mission_3_explain_integration",
        },
    }
    return {
        label: str(st.session_state.get(state_key, "")).strip()
        for label, state_key in keys.get(mission_id, {}).items()
    }


def render_student_identity() -> dict[str, str]:
    with st.expander("Student info for the export", expanded=False):
        st.caption("Optional, but useful if your instructor collects submissions from a class.")
        st.text_input("Name", key="student_name")
        st.text_input("Student ID or email", key="student_id")
        st.text_input("Section", key="student_section")
    return {
        "name": str(st.session_state.get("student_name", "")).strip(),
        "student_id": str(st.session_state.get("student_id", "")).strip(),
        "section": str(st.session_state.get("student_section", "")).strip(),
    }


# ---------------------------------------------------------------------------
# Instructor controls
# ---------------------------------------------------------------------------

def render_instructor_controls() -> None:
    with st.sidebar.expander("Instructor controls"):
        if not st.session_state.get("instructor_unlocked", False):
            password = st.text_input("Master password", type="password", key="instructor_password_input")
            if st.button("Unlock", key="instructor_unlock"):
                if password == instructor_password():
                    st.session_state["instructor_unlocked"] = True
                    st.success("Unlocked.")
                    request_streamlit_rerun()
                else:
                    st.error("Wrong password.")
            return

        st.success("Instructor mode unlocked.")
        page_options = {
            "Home": "intro",
            "PID concepts": "pid_concepts",
            "Background": "background",
            "PID playground": "pid_playground",
            "Odometry background": "odom_background",
            "Lab": "lab",
            "Final export": "export",
        }
        current_stage = str(st.session_state.get("stage", "intro"))
        page_labels = list(page_options)
        current_page_index = next(
            (index for index, label in enumerate(page_labels) if page_options[label] == current_stage),
            page_labels.index("Lab"),
        )
        selected_page = st.selectbox("Jump to page", page_labels, index=current_page_index)
        if st.button("Go", key="instructor_go_page"):
            set_stage(page_options[selected_page])

        mission_options = {
            "Mission 1": "mission_1",
            "Mission 2": "mission_2",
            "Mission 3": "mission_3",
        }
        selected_mission = st.selectbox("Jump to mission", list(mission_options))
        if st.button("Switch mission", key="instructor_switch_mission"):
            st.session_state["mission_override"] = mission_options[selected_mission]
            set_stage("lab")

        if st.button("Resume normal mission flow", key="instructor_resume_flow"):
            st.session_state.pop("mission_override", None)
            set_stage("lab")

        if st.button("Lock instructor mode", key="instructor_lock"):
            st.session_state["instructor_unlocked"] = False
            request_streamlit_rerun()


# ---------------------------------------------------------------------------
# Simulation functions
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=64)
def simulate_pid(
    kp: float,
    ki: float,
    kd: float,
    target: float = 2.0,
    total_time: float = 6.0,
    mass: float = 1.0,
    damping: float = 0.7,
    max_command: float = 5.0,
) -> PIDResult:
    steps = int(total_time / DT)
    x = 0.0
    v = 0.0
    integral = 0.0
    previous_error = target - x
    rows: dict[str, list[float]] = {
        "time": [], "position": [], "velocity": [], "command": [],
        "error": [], "p_term": [], "i_term": [], "d_term": [],
    }
    for step in range(steps + 1):
        now = step * DT
        error = target - x
        integral = clamp(integral + error * DT, -3.0, 3.0)
        derivative = (error - previous_error) / DT if step else 0.0
        p_term = kp * error
        i_term = ki * integral
        d_term = kd * derivative
        command = clamp(p_term + i_term + d_term, -max_command, max_command)
        acceleration = (command - damping * v) / mass
        v += acceleration * DT
        x += v * DT
        previous_error = error

        rows["time"].append(now)
        rows["position"].append(x)
        rows["velocity"].append(v)
        rows["command"].append(command)
        rows["error"].append(error)
        rows["p_term"].append(p_term)
        rows["i_term"].append(i_term)
        rows["d_term"].append(d_term)
    return PIDResult(target=target, **rows)


@functools.lru_cache(maxsize=64)
def simulate_open_loop_trials(power: float, run_time: float, target: float = 2.0) -> list[OpenLoopTrial]:
    scenarios = [(1.0, 1.0), (0.84, 1.0), (1.0, 1.24)]
    trials: list[OpenLoopTrial] = []
    for battery, friction in scenarios:
        distance = 0.0
        velocity = 0.0
        for _ in range(int(run_time / DT)):
            command = clamp(power, -1.0, 1.0) * battery
            acceleration = 2.2 * command - friction * 0.9 * velocity
            velocity += acceleration * DT
            distance += velocity * DT
        trials.append(
            OpenLoopTrial(
                battery=battery, friction=friction,
                final_distance=distance, error=target - distance,
            )
        )
    return trials


def integrate_odometry(
    left_delta: float, right_delta: float, track_width: float,
    x: float, y: float, theta: float,
) -> tuple[float, float, float]:
    center_delta = (left_delta + right_delta) / 2.0
    theta_delta = (right_delta - left_delta) / track_width
    mid_theta = theta + theta_delta / 2.0
    x += center_delta * math.cos(mid_theta)
    y += center_delta * math.sin(mid_theta)
    theta = wrap_angle(theta + theta_delta)
    return x, y, theta


def square_path_commands(
    side_length: float = 1.2, speed: float = 0.4, turn_rate: float = 1.4,
) -> list[tuple[float, float, float]]:
    commands: list[tuple[float, float, float]] = []
    drive_time = side_length / speed
    turn_time = (math.pi / 2.0) / turn_rate
    for _ in range(4):
        commands.append((drive_time, speed, 0.0))
        commands.append((turn_time, 0.0, turn_rate))
    return commands


@functools.lru_cache(maxsize=64)
def simulate_odometry(
    wheel_radius_estimate: float,
    track_width_estimate: float,
    *,
    true_wheel_radius: float = 0.050,
    true_track_width: float = 0.34,
    left_scale_error: float = 0.012,
    right_scale_error: float = -0.006,
) -> OdomResult:
    true_x = true_y = true_theta = 0.0
    odom_x = odom_y = odom_theta = 0.0
    t = 0.0
    rows: dict[str, list] = {
        "time": [0.0], "true_x": [0.0], "true_y": [0.0], "true_theta": [0.0],
        "odom_x": [0.0], "odom_y": [0.0], "odom_theta": [0.0],
        "left_distance": [0.0], "right_distance": [0.0], "commands": [(0.0, 0.0)],
    }
    for duration, linear, angular in square_path_commands():
        steps = max(1, int(duration / DT))
        for _ in range(steps):
            left_true = (linear - angular * true_track_width / 2.0) * DT
            right_true = (linear + angular * true_track_width / 2.0) * DT
            true_x, true_y, true_theta = integrate_odometry(
                left_true, right_true, true_track_width, true_x, true_y, true_theta,
            )
            left_ticks = left_true * (1.0 + left_scale_error) / true_wheel_radius
            right_ticks = right_true * (1.0 + right_scale_error) / true_wheel_radius
            left_est = left_ticks * wheel_radius_estimate
            right_est = right_ticks * wheel_radius_estimate
            odom_x, odom_y, odom_theta = integrate_odometry(
                left_est, right_est, track_width_estimate, odom_x, odom_y, odom_theta,
            )
            t += DT
            rows["time"].append(t)
            rows["true_x"].append(true_x)
            rows["true_y"].append(true_y)
            rows["true_theta"].append(true_theta)
            rows["odom_x"].append(odom_x)
            rows["odom_y"].append(odom_y)
            rows["odom_theta"].append(odom_theta)
            rows["left_distance"].append(left_est)
            rows["right_distance"].append(right_est)
            rows["commands"].append((linear, angular))
    return OdomResult(**rows)


@functools.lru_cache(maxsize=32)
def simulate_path_following(
    heading_kp: float,
    heading_ki: float,
    heading_kd: float,
    *,
    wheel_radius_estimate: float = 0.050,
    track_width_estimate: float = 0.34,
    true_wheel_radius: float = 0.050,
    true_track_width: float = 0.34,
    forward_speed: float = 0.35,
    lookahead: float = 0.30,
    total_time: float = 20.0,
) -> PathFollowResult:
    """Simulate path following using pure pursuit for desired heading and a
    student-tuned heading PID controller.  Uses sim_core for the heavy lifting."""
    import sim_core

    # Build a square path with waypoints.
    side = 1.2
    waypoints: list[tuple[float, float]] = [
        (0.0, 0.0), (side, 0.0), (side, side), (0.0, side), (0.0, 0.0),
    ]
    path = sim_core.interpolate_path(waypoints, spacing=0.05)
    path_x = [p[0] for p in path]
    path_y = [p[1] for p in path]

    # Heading PID
    controller = sim_core.PIDController(
        kp=heading_kp, ki=heading_ki, kd=heading_kd,
        output_limits=(-3.0, 3.0),
        integral_limits=(-2.0, 2.0),
    )

    # State
    true_x, true_y, true_theta = 0.0, 0.0, 0.0
    odom_x, odom_y, odom_theta = 0.0, 0.0, 0.0

    rows: dict[str, list[float]] = {
        "time": [], "true_x": [], "true_y": [], "true_theta": [],
        "odom_x": [], "odom_y": [], "odom_theta": [],
        "heading_error": [], "command": [],
    }

    steps = int(total_time / DT)
    for step in range(steps + 1):
        t = step * DT
        pose = (true_x, true_y, true_theta)

        # Pure pursuit on true pose
        cmd = sim_core.pure_pursuit_command(
            pose, path, lookahead, forward_speed, wheel_base=true_track_width,
        )
        desired_heading = math.atan2(
            path[min(sim_core.lookahead_point(pose, path, lookahead)[0], len(path) - 1)][1] - true_y,
            path[min(sim_core.lookahead_point(pose, path, lookahead)[0], len(path) - 1)][0] - true_x,
        )

        # Heading PID update
        heading_error = sim_core.angle_error(desired_heading, true_theta)
        angular_command = controller.update(true_theta, DT, desired_heading, wrap_error=True)

        # Convert to wheel speeds
        left_speed, right_speed = sim_core.unicycle_to_wheel_speeds(
            forward_speed, angular_command, true_track_width,
        )

        # Integrate true state
        left_delta = left_speed * DT
        right_delta = right_speed * DT
        true_x, true_y, true_theta = integrate_odometry(
            left_delta, right_delta, true_track_width, true_x, true_y, true_theta,
        )

        # Odometry estimate (with slight bias)
        left_est = left_delta * (true_wheel_radius / wheel_radius_estimate)
        right_est = right_delta * (true_wheel_radius / wheel_radius_estimate)
        odom_x, odom_y, odom_theta = integrate_odometry(
            left_est * wheel_radius_estimate / true_wheel_radius,
            right_est * wheel_radius_estimate / true_wheel_radius,
            track_width_estimate, odom_x, odom_y, odom_theta,
        )

        rows["time"].append(t)
        rows["true_x"].append(true_x)
        rows["true_y"].append(true_y)
        rows["true_theta"].append(true_theta)
        rows["odom_x"].append(odom_x)
        rows["odom_y"].append(odom_y)
        rows["odom_theta"].append(odom_theta)
        rows["heading_error"].append(heading_error)
        rows["command"].append(angular_command)

    # Compute tracking error using sim_core
    poses = list(zip(rows["true_x"], rows["true_y"], rows["true_theta"]))
    tracking = sim_core.path_tracking_error(poses, path)

    return PathFollowResult(
        time=rows["time"],
        true_x=rows["true_x"], true_y=rows["true_y"], true_theta=rows["true_theta"],
        odom_x=rows["odom_x"], odom_y=rows["odom_y"], odom_theta=rows["odom_theta"],
        path_x=path_x, path_y=path_y,
        heading_error=rows["heading_error"],
        command=rows["command"],
        mean_tracking_error=tracking["mean"],
        max_tracking_error=tracking["max"],
    )


@functools.lru_cache(maxsize=64)
def simulate_waypoint_nav(
    heading_kp: float,
    heading_ki: float,
    heading_kd: float,
    *,
    wheel_radius_estimate: float = 0.050,
    true_wheel_radius: float = 0.050,
    track_width: float = 0.34,
    forward_speed: float = 0.35,
    arrive_radius: float = 0.12,
    safe_radius: float = 0.25,
    total_time: float = 40.0,
) -> WaypointNavResult:
    """Drive to a sequence of waypoints on a shared path steering by the robot's
    OWN odometry estimate, keeping clear of pedestrians standing near the path.

    This is the heart of the PID + odometry integration: the heading PID acts on
    the *estimated* pose, while the wheels move the *true* pose.  If odometry is
    miscalibrated (wheel_radius_estimate != true_wheel_radius), the robot believes
    it is somewhere it is not, so a perfectly tuned controller confidently drives
    to the wrong place -- and can clip a pedestrian it thinks it is clear of.
    """
    import sim_core

    waypoints: list[tuple[float, float]] = [
        (1.2, 0.0), (1.2, 1.2), (0.0, 1.2), (0.0, 0.0),
    ]
    # Pedestrians stand just outside the path corners -- far enough that a
    # well-calibrated robot clears them (min gap > safe_radius), close enough that
    # odometry drift, which swings the true path outward, steers within the unsafe
    # radius. Placed near the outer corner each miscalibration overshoots toward.
    pedestrians: list[tuple[float, float]] = [
        (1.53, 0.40),   # just outside leg 1; an under-read radius swings right into them
        (0.30, 1.51),   # just outside leg 2; an over-read radius swings up into them
    ]

    controller = sim_core.PIDController(
        kp=heading_kp, ki=heading_ki, kd=heading_kd,
        output_limits=(-3.0, 3.0),
        integral_limits=(-2.0, 2.0),
    )

    # True pose (ground truth) and estimated pose (what the robot "knows").
    true_x = true_y = true_theta = 0.0
    odom_x = odom_y = odom_theta = 0.0

    rows: dict[str, list[float]] = {
        "time": [], "true_x": [], "true_y": [], "true_theta": [],
        "odom_x": [], "odom_y": [], "odom_theta": [],
        "heading_error": [], "command": [],
    }

    target_idx = 0
    reached_flags = [False] * len(waypoints)
    true_gap_at_reach = [float("nan")] * len(waypoints)
    min_pedestrian_gap = float("inf")

    def update_ped_gap(px: float, py: float) -> None:
        nonlocal min_pedestrian_gap
        for ped in pedestrians:
            g = math.hypot(ped[0] - px, ped[1] - py)
            if g < min_pedestrian_gap:
                min_pedestrian_gap = g

    steps = int(total_time / DT)
    for step in range(steps + 1):
        t = step * DT
        if target_idx >= len(waypoints):
            # Mission complete: coast in place for the remaining record.
            rows["time"].append(t)
            rows["true_x"].append(true_x); rows["true_y"].append(true_y); rows["true_theta"].append(true_theta)
            rows["odom_x"].append(odom_x); rows["odom_y"].append(odom_y); rows["odom_theta"].append(odom_theta)
            rows["heading_error"].append(0.0); rows["command"].append(0.0)
            continue

        goal = waypoints[target_idx]

        # The controller only sees the ESTIMATE.
        desired_heading = math.atan2(goal[1] - odom_y, goal[0] - odom_x)
        heading_error = sim_core.angle_error(desired_heading, odom_theta)
        angular_command = controller.update(odom_theta, DT, desired_heading, wrap_error=True)

        # Slow down while turning hard so the robot doesn't scribe wide arcs.
        speed = forward_speed * clamp(1.0 - abs(heading_error) / (math.pi / 2), 0.25, 1.0)

        left_speed, right_speed = sim_core.unicycle_to_wheel_speeds(
            speed, angular_command, track_width,
        )

        # True motion uses the true wheel radius (wheel commands are in rad/s-equiv;
        # here left/right_speed are linear speeds already, so true travel is direct).
        left_delta = left_speed * DT
        right_delta = right_speed * DT
        true_x, true_y, true_theta = integrate_odometry(
            left_delta, right_delta, track_width, true_x, true_y, true_theta,
        )
        update_ped_gap(true_x, true_y)

        # Odometry integrates the SAME wheel rotation but converts it to distance
        # with the ESTIMATED wheel radius.  A wrong radius scales the believed travel.
        calib = wheel_radius_estimate / true_wheel_radius
        odom_x, odom_y, odom_theta = integrate_odometry(
            left_delta * calib, right_delta * calib, track_width, odom_x, odom_y, odom_theta,
        )

        # Has the robot's ESTIMATE arrived at the waypoint?
        est_gap = math.hypot(goal[0] - odom_x, goal[1] - odom_y)
        if est_gap <= arrive_radius:
            reached_flags[target_idx] = True
            true_gap_at_reach[target_idx] = math.hypot(goal[0] - true_x, goal[1] - true_y)
            controller.reset()
            target_idx += 1

        rows["time"].append(t)
        rows["true_x"].append(true_x); rows["true_y"].append(true_y); rows["true_theta"].append(true_theta)
        rows["odom_x"].append(odom_x); rows["odom_y"].append(odom_y); rows["odom_theta"].append(odom_theta)
        rows["heading_error"].append(heading_error); rows["command"].append(angular_command)

    num_reached = sum(1 for f in reached_flags if f)
    # Ground-truth success: did the robot ACTUALLY get near each waypoint?
    num_truly_reached = sum(
        1 for g in true_gap_at_reach if not math.isnan(g) and g <= arrive_radius * 2.0
    )
    final_true_gap = math.hypot(
        waypoints[-1][0] - true_x, waypoints[-1][1] - true_y,
    )
    believed = [g for g in true_gap_at_reach if not math.isnan(g)]
    mean_true_gap = (sum(believed) / len(believed)) if believed else float("nan")
    if min_pedestrian_gap == float("inf"):
        min_pedestrian_gap = 999.0
    hit_pedestrian = min_pedestrian_gap < safe_radius

    return WaypointNavResult(
        time=rows["time"],
        true_x=rows["true_x"], true_y=rows["true_y"], true_theta=rows["true_theta"],
        odom_x=rows["odom_x"], odom_y=rows["odom_y"], odom_theta=rows["odom_theta"],
        waypoints=waypoints,
        reached_flags=reached_flags,
        true_gap_at_reach=true_gap_at_reach,
        heading_error=rows["heading_error"],
        command=rows["command"],
        num_reached=num_reached,
        num_truly_reached=num_truly_reached,
        final_true_gap=final_true_gap,
        mean_true_gap_at_reach=mean_true_gap,
        calibration_ratio=wheel_radius_estimate / true_wheel_radius,
        pedestrians=pedestrians,
        safe_radius=safe_radius,
        min_pedestrian_gap=min_pedestrian_gap,
        hit_pedestrian=hit_pedestrian,
    )

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def pid_metrics(result: PIDResult) -> dict[str, float]:
    position = np.array(result.position)
    error = np.array(result.error)
    time = np.array(result.time)
    target = result.target
    overshoot = max(0.0, float(position.max() - target))
    final_error = abs(float(error[-1]))
    within = np.abs(position - target) < 0.08
    settling_time = float(time[-1])
    for index in range(len(within)):
        if within[index] and within[index:].all():
            settling_time = float(time[index])
            break
    command_effort = float(np.mean(np.abs(result.command)))
    return {
        "overshoot": overshoot,
        "final_error": final_error,
        "settling_time": settling_time,
        "command_effort": command_effort,
    }


def odom_metrics(result: OdomResult) -> dict[str, float]:
    final_position_error = math.hypot(
        result.odom_x[-1] - result.true_x[-1],
        result.odom_y[-1] - result.true_y[-1],
    )
    final_heading_error = abs(wrap_angle(result.odom_theta[-1] - result.true_theta[-1]))
    path_error = float(
        np.mean(
            np.hypot(
                np.array(result.odom_x) - np.array(result.true_x),
                np.array(result.odom_y) - np.array(result.true_y),
            )
        )
    )
    return {
        "final_position_error": final_position_error,
        "final_heading_error_deg": math.degrees(final_heading_error),
        "mean_path_error": path_error,
    }


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_open_loop(trials: list[OpenLoopTrial], target: float = 2.0) -> Any:
    figure, axis = plt.subplots(figsize=(7, 3.5))
    labels = ["normal", "low battery", "high friction"]
    distances = [trial.final_distance for trial in trials]
    colors = ["#2563eb", "#f79009", "#7a5af8"]
    axis.bar(labels, distances, color=colors)
    axis.axhline(target, color="#12b76a", linestyle="--", label="target")
    axis.set_ylabel("final distance (m)")
    axis.set_title("Same command, different outcomes")
    axis.grid(axis="y", alpha=0.25)
    axis.legend(loc="best")
    figure.tight_layout()
    return figure


def plot_pid(result: PIDResult) -> Any:
    figure, axes = plt.subplots(2, 1, figsize=(8, 5), sharex=True)
    axes[0].plot(result.time, result.position, label="robot position")
    axes[0].axhline(result.target, color="#12b76a", linestyle="--", label="target")
    axes[0].set_ylabel("position")
    axes[0].legend(loc="best")
    axes[0].grid(alpha=0.25)

    axes[1].plot(result.time, result.p_term, label="P")
    axes[1].plot(result.time, result.i_term, label="I")
    axes[1].plot(result.time, result.d_term, label="D")
    axes[1].plot(result.time, result.command, color="#101828", linewidth=2, label="command")
    axes[1].set_xlabel("time (s)")
    axes[1].set_ylabel("output")
    axes[1].legend(loc="best", ncols=4)
    axes[1].grid(alpha=0.25)
    figure.tight_layout()
    return figure


def plot_odometry(result: OdomResult) -> Any:
    figure, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].plot(result.true_x, result.true_y, label="true path", linewidth=2)
    axes[0].plot(result.odom_x, result.odom_y, label="odometry estimate", linestyle="--")
    axes[0].scatter([result.true_x[-1]], [result.true_y[-1]], color="#12b76a", label="true end")
    axes[0].scatter([result.odom_x[-1]], [result.odom_y[-1]], color="#f04438", label="odom end")
    axes[0].axis("equal")
    axes[0].set_xlabel("x (m)")
    axes[0].set_ylabel("y (m)")
    axes[0].grid(alpha=0.25)
    axes[0].legend(loc="best")

    heading_error = [math.degrees(wrap_angle(o - t)) for o, t in zip(result.odom_theta, result.true_theta)]
    axes[1].plot(result.time, heading_error)
    axes[1].axhline(0.0, color="#98a2b3", linewidth=1)
    axes[1].set_xlabel("time (s)")
    axes[1].set_ylabel("heading error (deg)")
    axes[1].grid(alpha=0.25)
    figure.tight_layout()
    return figure


def plot_path_following(result: PathFollowResult) -> Any:
    figure, axes = plt.subplots(1, 2, figsize=(10, 5))

    # XY path
    axes[0].plot(result.path_x, result.path_y, color="#98a2b3", linewidth=1.5, label="reference path", zorder=1)
    axes[0].plot(result.true_x, result.true_y, color="#2563eb", linewidth=2, label="true path", zorder=2)
    axes[0].plot(result.odom_x, result.odom_y, color="#f79009", linewidth=1.5, linestyle="--", label="odometry", zorder=2)
    axes[0].scatter([result.true_x[0]], [result.true_y[0]], color="#12b76a", s=60, zorder=3, label="start")
    axes[0].scatter([result.true_x[-1]], [result.true_y[-1]], color="#f04438", s=60, zorder=3, label="end")
    axes[0].axis("equal")
    axes[0].set_xlabel("x (m)")
    axes[0].set_ylabel("y (m)")
    axes[0].set_title("Path following")
    axes[0].legend(loc="best", fontsize=8)
    axes[0].grid(alpha=0.25)

    # Heading error over time
    heading_deg = [math.degrees(e) for e in result.heading_error]
    axes[1].plot(result.time, heading_deg, color="#7a5af8", linewidth=1.5)
    axes[1].axhline(0.0, color="#98a2b3", linewidth=1)
    axes[1].set_xlabel("time (s)")
    axes[1].set_ylabel("heading error (deg)")
    axes[1].set_title("Heading error")
    axes[1].grid(alpha=0.25)

    figure.tight_layout()
    return figure


# ---------------------------------------------------------------------------
# CSV and ZIP helpers
# ---------------------------------------------------------------------------

def figure_png(figure: Any) -> bytes:
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", dpi=120, bbox_inches="tight")
    return buffer.getvalue()


def csv_for_pid(result: PIDResult) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["time", "position", "velocity", "command", "error", "p_term", "i_term", "d_term"])
    for row in zip(result.time, result.position, result.velocity, result.command, result.error, result.p_term, result.i_term, result.d_term):
        writer.writerow(row)
    return buffer.getvalue()


def csv_for_odom(result: OdomResult) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["time", "true_x", "true_y", "true_theta", "odom_x", "odom_y", "odom_theta", "left_distance", "right_distance"])
    for row in zip(result.time, result.true_x, result.true_y, result.true_theta, result.odom_x, result.odom_y, result.odom_theta, result.left_distance, result.right_distance):
        writer.writerow(row)
    return buffer.getvalue()


def csv_for_baseline(trials: list[OpenLoopTrial]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["scenario", "battery", "friction", "final_distance", "error"])
    for label, trial in zip(("normal", "low_battery", "high_friction"), trials):
        writer.writerow([label, trial.battery, trial.friction, trial.final_distance, trial.error])
    return buffer.getvalue()


def csv_for_path_follow(result: PathFollowResult) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["time", "true_x", "true_y", "true_theta", "odom_x", "odom_y", "odom_theta", "heading_error", "command"])
    for row in zip(result.time, result.true_x, result.true_y, result.true_theta, result.odom_x, result.odom_y, result.odom_theta, result.heading_error, result.command):
        writer.writerow(row)
    return buffer.getvalue()


def activity_gifs_from_state(mission_id: str) -> dict[str, bytes]:
    """Return automatically recorded GIFs, including files from an earlier session."""
    stored = st.session_state.get("_automatic_activity_gifs", {})
    gifs = dict(stored.get(mission_id, {})) if isinstance(stored, dict) else {}
    try:
        gif_dir = SUBMISSIONS_DIR / mission_id / "activity_gifs"
        for path in sorted(gif_dir.glob("*.gif")):
            content = path.read_bytes()
            if content.startswith((b"GIF87a", b"GIF89a")):
                gifs[path.name] = content
    except Exception:
        pass
    return gifs


def _persist_gifs_to_folder(mission_id: str, gifs: dict[str, bytes]) -> None:
    """Write activity GIFs straight into the submissions folder."""
    if not gifs:
        return
    try:
        gif_dir = SUBMISSIONS_DIR / mission_id / "activity_gifs"
        gif_dir.mkdir(parents=True, exist_ok=True)
        for name, content in gifs.items():
            (gif_dir / name).write_bytes(content)
    except Exception:
        pass  # never let a filesystem hiccup break the lab UI


def _gif_from_recording_frames(frames: list[str], duration_ms: int) -> bytes:
    """Encode browser-captured canvas frames as an animated GIF."""
    image_module = require("PIL.Image")
    images = []
    for frame in frames[:48]:
        if not isinstance(frame, str) or "," not in frame:
            continue
        encoded = frame.split(",", 1)[1]
        if len(encoded) > 1_500_000:
            continue
        raw = base64.b64decode(encoded, validate=True)
        with image_module.open(io.BytesIO(raw)) as source:
            images.append(source.convert("RGB"))
    if not images:
        return b""
    output = io.BytesIO()
    images[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=images[1:],
        duration=max(60, min(int(duration_ms), 1000)),
        loop=0,
        disposal=2,
        optimize=False,
    )
    return output.getvalue()


def persist_component_recording(
    mission_id: str,
    component_state: dict[str, Any],
    filename: str = "latest_drive.gif",
) -> dict[str, bytes]:
    """Save a component's newest browser recording once, without any upload UI."""
    frames = component_state.get("recording_frames", [])
    if not isinstance(frames, list) or not frames:
        return activity_gifs_from_state(mission_id)
    fingerprint = hashlib.sha256()
    for frame in frames:
        if isinstance(frame, str):
            fingerprint.update(frame.encode("ascii", errors="ignore"))
    digest = fingerprint.hexdigest()
    digest_key = f"_automatic_gif_digest_{mission_id}"
    if st.session_state.get(digest_key) == digest:
        return activity_gifs_from_state(mission_id)
    try:
        gif = _gif_from_recording_frames(
            frames,
            int(component_state.get("recording_frame_duration_ms", 120)),
        )
        if not gif:
            return activity_gifs_from_state(mission_id)
        gifs = {filename: gif}
        _persist_gifs_to_folder(mission_id, gifs)
        all_gifs = st.session_state.get("_automatic_activity_gifs", {})
        all_gifs = dict(all_gifs) if isinstance(all_gifs, dict) else {}
        all_gifs[mission_id] = gifs
        st.session_state["_automatic_activity_gifs"] = all_gifs
        st.session_state[digest_key] = digest
        return gifs
    except Exception:
        return activity_gifs_from_state(mission_id)




def component_state_without_recording(state: Any) -> dict[str, Any]:
    """Keep compact mission results while the GIF lives as its own artifact."""
    if not isinstance(state, dict):
        return {}
    return {
        key: value
        for key, value in state.items()
        if key not in ("recording_frames", "recording_frame_duration_ms")
    }


def persist_latest_mission_run(mission_id: str, data: dict[str, Any]) -> None:
    """Automatically persist compact run parameters and metrics on change."""
    try:
        serialized = json.dumps(data, indent=2, sort_keys=True, default=str)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        digest_key = f"_automatic_run_digest_{mission_id}"
        if st.session_state.get(digest_key) == digest:
            return
        target = SUBMISSIONS_DIR / mission_id
        target.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "mission_id": mission_id,
            **data,
        }
        (target / "latest_run.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        st.session_state[digest_key] = digest
    except Exception:
        pass


def build_mission_zip(
    mission_id: str,
    data: dict[str, Any],
    explanations: dict[str, str],
    identity: dict[str, str],
) -> bytes:
    """Build a ZIP for a single mission submission."""
    payload = {
        "schema_version": 1,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "mission_id": mission_id,
        "student": identity,
        "explanations": explanations,
        **{
            k: v
            for k, v in data.items()
            if k not in ("figures", "activity_gifs")
        },
        "activity_gifs": sorted(data.get("activity_gifs", {}).keys()),
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("submission.json", json.dumps(payload, indent=2, default=str))
        for name, content in data.get("csv_files", {}).items():
            archive.writestr(name, content)
        for name, fig in data.get("figures", {}).items():
            archive.writestr(name, figure_png(fig))
        for name, content in data.get("activity_gifs", {}).items():
            archive.writestr(f"activity_gifs/{name}", content)
        md_lines = [f"# {mission_id} Submission", ""]
        md_lines.append(f"- Name: {identity.get('name') or '(not provided)'}")
        md_lines.append(f"- Section: {identity.get('section') or '(not provided)'}")
        md_lines.append("")
        md_lines.append("## Explanations")
        for k, v in explanations.items():
            md_lines.append(f"\n### {k}\n\n{v or '(no answer)'}")
        archive.writestr("explanation.md", "\n".join(md_lines))
    return buffer.getvalue()


def build_final_submission_zip(
    all_mission_data: dict[str, dict[str, Any]],
    all_explanations: dict[str, dict[str, str]],
    all_checkins: dict[str, str],
    identity: dict[str, str],
) -> bytes:
    """Build a comprehensive ZIP with all missions and check-ins."""
    payload = {
        "schema_version": 1,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "student": identity,
        "missions": {},
        "checkins": all_checkins,
    }
    for mid, data in all_mission_data.items():
        payload["missions"][mid] = {
            k: v
            for k, v in data.items()
            if k not in ("figures", "activity_gifs")
        }
        payload["missions"][mid]["activity_gifs"] = sorted(
            data.get("activity_gifs", {}).keys()
        )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("submission.json", json.dumps(payload, indent=2, default=str))

        # Per-mission files
        for mid, data in all_mission_data.items():
            for name, content in data.get("csv_files", {}).items():
                archive.writestr(f"{mid}/{name}", content)
            for name, fig in data.get("figures", {}).items():
                archive.writestr(f"{mid}/{name}", figure_png(fig))
            for name, content in data.get("activity_gifs", {}).items():
                archive.writestr(f"{mid}/activity_gifs/{name}", content)

        # Explanation document
        md_lines = [
            "# PID and Odometry Lab -- Full Submission",
            "",
            f"- Name: {identity.get('name') or '(not provided)'}",
            f"- Student ID: {identity.get('student_id') or '(not provided)'}",
            f"- Section: {identity.get('section') or '(not provided)'}",
            "",
        ]
        md_lines.append("## Check-ins\n")
        for k, v in all_checkins.items():
            md_lines.append(f"### {k}\n\n{v or '(no answer)'}\n")
        md_lines.append("## Mission Explanations\n")
        for mid, expl in all_explanations.items():
            md_lines.append(f"### {mid}\n")
            for k, v in expl.items():
                md_lines.append(f"**{k}**: {v or '(no answer)'}\n")
        archive.writestr("explanation.md", "\n".join(md_lines))
    return buffer.getvalue()


def save_mission_submission(
    mission_id: str,
    data: dict[str, Any],
    explanations: dict[str, str],
    identity: dict[str, str],
) -> Path:
    """Write a mission's text, data, plots, and GIFs into a Git-ready folder."""
    target = SUBMISSIONS_DIR / mission_id
    target.mkdir(parents=True, exist_ok=True)
    archive_bytes = build_mission_zip(mission_id, data, explanations, identity)
    with zipfile.ZipFile(io.BytesIO(archive_bytes), "r") as archive:
        archive.extractall(target)
    return target


def save_final_submission(
    all_mission_data: dict[str, dict[str, Any]],
    all_explanations: dict[str, dict[str, str]],
    all_checkins: dict[str, str],
    identity: dict[str, str],
) -> Path:
    """Write the complete submission tree so a student can commit it to Git."""
    SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    archive_bytes = build_final_submission_zip(
        all_mission_data,
        all_explanations,
        all_checkins,
        identity,
    )
    with zipfile.ZipFile(io.BytesIO(archive_bytes), "r") as archive:
        archive.extractall(SUBMISSIONS_DIR)
    return SUBMISSIONS_DIR


# ---------------------------------------------------------------------------
# Automatic saving of text responses and GIFs
# ---------------------------------------------------------------------------

AUTOSAVE_DIR = SUBMISSIONS_DIR / "autosave"

# Every check-in key used across the lab, so the autosave captures all of them.
ALL_CHECKIN_KEYS = (
    "background_compare", "background_social",
    "pid_playground_terms", "odom_background_wheels",
    "m1_arm_tuning",
    "m2_drift", "m2_turning", "m3_heading_pid", "m3_integration",
    "ethics_failure_mode", "ethics_margin", "ethics_accountability",
    "final_reflection",
)


def collect_text_responses() -> dict[str, Any]:
    """Gather every check-in answer and mission explanation currently in session."""
    checkins = {}
    for key in ALL_CHECKIN_KEYS:
        resp = checkin_response(key)
        value = resp["note"] or resp["choice"]
        if value:
            checkins[key] = value

    explanations = {}
    for mission_id in MISSION_ORDER:
        answers = {k: v for k, v in mission_explanations_from_state(mission_id).items() if v}
        if answers:
            explanations[mission_id] = answers

    identity = {
        "name": str(st.session_state.get("student_name", "")).strip()
        or str(st.session_state.get("export_student_name", "")).strip(),
        "student_id": str(st.session_state.get("student_id", "")).strip()
        or str(st.session_state.get("export_student_id", "")).strip(),
        "section": str(st.session_state.get("student_section", "")).strip()
        or str(st.session_state.get("export_student_section", "")).strip(),
    }
    return {"identity": identity, "checkins": checkins, "explanations": explanations}


def _text_responses_markdown(responses: dict[str, Any]) -> str:
    identity = responses.get("identity", {})
    lines = [
        "# Autosaved responses",
        "",
        f"- Name: {identity.get('name') or '(not provided)'}",
        f"- Student ID: {identity.get('student_id') or '(not provided)'}",
        f"- Section: {identity.get('section') or '(not provided)'}",
        "",
        "## Check-in answers",
        "",
    ]
    checkins = responses.get("checkins", {})
    if checkins:
        for key, value in checkins.items():
            lines.append(f"### {key}\n\n{value}\n")
    else:
        lines.append("_(none yet)_\n")
    lines.append("## Mission explanations\n")
    explanations = responses.get("explanations", {})
    if explanations:
        for mission_id, answers in explanations.items():
            lines.append(f"### {mission_id}\n")
            for label, value in answers.items():
                lines.append(f"**{label}**: {value}\n")
    else:
        lines.append("_(none yet)_\n")
    return "\n".join(lines)


def autosave_responses_and_gifs() -> None:
    """Persist text responses and automatic GIFs to the submissions folder on every
    rerun, without requiring a button press.  Writes only when content has changed
    (tracked by a hash in session state) and never raises into the UI."""
    try:
        responses = collect_text_responses()

        gifs: dict[str, dict[str, bytes]] = {}
        for mission_id in MISSION_ORDER:
            mission_gifs = activity_gifs_from_state(mission_id)
            if mission_gifs:
                gifs[mission_id] = mission_gifs

        # Fingerprint the current content so we only touch disk on change.
        gif_manifest = {mid: sorted(files.keys()) for mid, files in gifs.items()}
        gif_fingerprints = {
            mid: {
                name: hashlib.sha256(content).hexdigest()
                for name, content in files.items()
            }
            for mid, files in gifs.items()
        }
        signature = json.dumps(
            {"responses": responses, "gifs": gif_fingerprints},
            sort_keys=True, default=str,
        )
        digest = str(hash(signature))
        if st.session_state.get("_autosave_digest") == digest:
            return

        AUTOSAVE_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            **responses,
            "activity_gifs": gif_manifest,
        }
        (AUTOSAVE_DIR / "responses.json").write_text(
            json.dumps(payload, indent=2, default=str), encoding="utf-8"
        )
        (AUTOSAVE_DIR / "responses.md").write_text(
            _text_responses_markdown(responses), encoding="utf-8"
        )
        for mission_id, files in gifs.items():
            gif_dir = AUTOSAVE_DIR / mission_id / "activity_gifs"
            gif_dir.mkdir(parents=True, exist_ok=True)
            for name, content in files.items():
                (gif_dir / name).write_bytes(content)

        st.session_state["_autosave_digest"] = digest
        st.session_state["_autosave_last"] = payload["saved_at"]
    except Exception:
        # Autosave must never interrupt the lab; a manual save remains available.
        pass


# ---------------------------------------------------------------------------
# Page: Hero intro
# ---------------------------------------------------------------------------

HERO_STYLE = """
<style>
.intro-hero {
    background: linear-gradient(135deg, #0f172a 0%, #122345 30%, #1e3a5f 55%, #0d9488 100%);
    min-height: 55vh;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: clamp(2rem, 4vw, 3.5rem);
    color: white;
    position: relative;
    overflow: hidden;
    gap: 2rem;
}
.intro-hero::before {
    content: "";
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle at 25% 75%, rgba(13, 148, 136, 0.25) 0%, transparent 45%),
                radial-gradient(circle at 75% 25%, rgba(37, 99, 235, 0.18) 0%, transparent 45%);
    animation: hero-pulse 8s ease-in-out infinite alternate;
    pointer-events: none;
}
@keyframes hero-pulse {
    0% { transform: translate(0, 0) scale(1); }
    100% { transform: translate(-3%, 3%) scale(1.05); }
}
.intro-copy {
    max-width: 540px;
    position: relative;
    z-index: 1;
    flex-shrink: 0;
}
.intro-copy .intro-tag {
    display: inline-block;
    background: rgba(13, 148, 136, 0.35);
    border: 1px solid rgba(13, 148, 136, 0.5);
    padding: 0.3rem 0.85rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
    color: #5eead4;
}
.intro-copy h1 {
    font-size: clamp(2.4rem, 5.5vw, 4rem);
    line-height: 1.0;
    margin: 0 0 1rem 0;
    letter-spacing: -0.02em;
    font-weight: 900;
}
.intro-copy .intro-sub {
    font-size: clamp(1rem, 1.5vw, 1.2rem);
    line-height: 1.55;
    margin: 0;
    opacity: 0.88;
    color: #cbd5e1;
}
.intro-viz {
    position: relative;
    z-index: 1;
    flex-shrink: 1;
    min-width: 200px;
    max-width: 380px;
    width: 100%;
}
.intro-viz svg {
    width: 100%;
    height: auto;
    filter: drop-shadow(0 4px 24px rgba(0,0,0,0.3));
}
@keyframes arm-base {
    0%   { transform: rotate(0deg); }
    15%  { transform: rotate(-35deg); }
    28%  { transform: rotate(-19deg); }
    38%  { transform: rotate(-27deg); }
    46%  { transform: rotate(-24deg); }
    52%  { transform: rotate(-25deg); }
    75%  { transform: rotate(-25deg); }
    92%  { transform: rotate(0deg); }
    100% { transform: rotate(0deg); }
}
@keyframes arm-elbow {
    0%   { transform: rotate(0deg); }
    15%  { transform: rotate(-28deg); }
    28%  { transform: rotate(-15deg); }
    38%  { transform: rotate(-22deg); }
    46%  { transform: rotate(-19deg); }
    52%  { transform: rotate(-20deg); }
    75%  { transform: rotate(-20deg); }
    92%  { transform: rotate(0deg); }
    100% { transform: rotate(0deg); }
}
@keyframes target-pulse {
    0%, 100% { r: 12; opacity: 0.25; }
    50%      { r: 16; opacity: 0.12; }
}
@keyframes effector-trail {
    0%, 52% { opacity: 0.5; }
    75%     { opacity: 0; }
}
.intro-start-button + div[data-testid="stButton"] > button {
    min-height: 3.8rem;
    font-size: 1.1rem;
    font-weight: 800;
    border-radius: 10px;
}

@media (max-width: 700px) {
    .intro-hero { flex-direction: column; min-height: auto; padding: 2rem 1.4rem; }
    .intro-viz { max-width: 280px; margin: 0 auto; }
}
</style>
"""


def render_intro_page() -> None:
    pid_svg = (
        '<svg viewBox="0 0 300 220" xmlns="http://www.w3.org/2000/svg">'

        '<line x1="20" y1="195" x2="280" y2="195" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>'
        '<rect x="140" y="185" width="40" height="16" rx="4" fill="rgba(255,255,255,0.12)"/>'

        '<circle cx="86" cy="80" r="12" fill="rgba(94,234,212,0.25)" stroke="none"'
        ' style="animation: target-pulse 2s ease-in-out infinite;"/>'
        '<circle cx="86" cy="80" r="5" fill="none" stroke="#5eead4" stroke-width="1.5"/>'
        '<circle cx="86" cy="80" r="1.5" fill="#5eead4"/>'
        '<line x1="80" y1="80" x2="92" y2="80" stroke="#5eead4" stroke-width="0.7" opacity="0.5"/>'
        '<line x1="86" y1="74" x2="86" y2="86" stroke="#5eead4" stroke-width="0.7" opacity="0.5"/>'

        '<g style="transform-origin: 160px 190px; animation: arm-base 5s ease-in-out infinite;">'
        '<line x1="160" y1="190" x2="160" y2="115" stroke="#f97316" stroke-width="5" stroke-linecap="round"/>'
        '<circle cx="160" cy="190" r="7" fill="rgba(249,115,22,0.3)" stroke="#f97316" stroke-width="1.5"/>'
        '<circle cx="160" cy="190" r="2.5" fill="#f97316"/>'

        '<g style="transform-origin: 160px 115px; animation: arm-elbow 5s ease-in-out infinite;">'
        '<line x1="160" y1="115" x2="160" y2="55" stroke="#fb923c" stroke-width="4" stroke-linecap="round"/>'
        '<circle cx="160" cy="115" r="5" fill="rgba(251,146,60,0.3)" stroke="#fb923c" stroke-width="1.5"/>'
        '<circle cx="160" cy="115" r="2" fill="#fb923c"/>'

        '<circle cx="160" cy="55" r="5" fill="white" opacity="0.9"/>'
        '<circle cx="160" cy="55" r="2" fill="#f97316"/>'
        '</g>'
        '</g>'

        '</svg>'
    )

    st.markdown(
        HERO_STYLE
        + '<div class="intro-hero">'
        '<div class="intro-copy">'
        '<span class="intro-tag">Course assignment</span>'
        '<h1>PID Control and<br>Odometry Lab</h1>'
        '<p class="intro-sub">This assignment covers PID feedback control and robot odometry. '
        'Complete the required tutorial sections and three missions, document your tuning decisions, '
        'and submit the automatically saved results.</p>'
        '</div>'
        f'<div class="intro-viz">{pid_svg}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    left, tutorial_col, skip_col, right = st.columns([0.7, 1.2, 1.2, 0.7])
    with tutorial_col:
        st.markdown('<span class="intro-start-button"></span>', unsafe_allow_html=True)
        if st.button("Start tutorial", type="primary", width="stretch"):
            set_stage("pid_concepts")
    with skip_col:
        st.markdown('<span class="intro-start-button"></span>', unsafe_allow_html=True)
        if st.button("Skip to lab", width="stretch"):
            set_stage("lab")


# ---------------------------------------------------------------------------
# Page: PID Concepts (component)
# ---------------------------------------------------------------------------

def render_pid_concepts_page() -> None:
    st.title("PID Concepts")
    st.markdown(
        "Before tuning gains, explore what feedback control means interactively. "
        "The component below lets you experiment with a simple feedback loop."
    )
    pid_concepts_component()

    back_col, next_col = st.columns(2)
    if back_col.button("Back", width="stretch"):
        set_stage("intro")
    if next_col.button("Continue to background", type="primary", width="stretch"):
        set_stage("background")


# ---------------------------------------------------------------------------
# Page: Background
# ---------------------------------------------------------------------------

def render_background_page() -> None:
    st.title("Background: The Feedback Loop")

    # --- Scaffolding: start from the everyday intuition before the formalism ---
    st.markdown(
        """
        Having driven the car to the stop line manually, this section names what was
        happening, step by step, before introducing the equations.
        """
    )

    st.markdown("#### Step 1 — Two ways to control a system")
    open_col, closed_col = st.columns(2)
    with open_col:
        st.markdown("**Open loop — command without feedback**")
        st.write(
            "The action is set in advance: *apply gas for 2 seconds, then release.* "
            "The controller never measures the result. If conditions differ from "
            "what was assumed — an incline, a low battery, a heavier load — the car "
            "stops in the wrong place, and the controller cannot detect it."
        )
    with closed_col:
        st.markdown("**Closed loop — command based on measurement**")
        st.write(
            "The controller measures the remaining gap continuously and adjusts: "
            "reducing the command as it approaches, applying more if it stalls "
            "short. Because it responds to the actual state, it corrects for "
            "conditions it wasn't told about. PID is a closed-loop controller."
        )

    st.markdown("#### Step 2 — Controllers come in several types")
    st.write(
        "A controller is a rule from **error** to **command**. The simplest is "
        "**bang-bang** (on/off) — full command until the target is reached, as in a "
        "thermostat — which is easy to build but tends to overshoot. **Proportional** "
        "control is smoother: the command is proportional to the error. **PID** adds "
        "two further terms on top of proportional so the controller can damp its "
        "approach and remove any steady offset. Those three terms are the subject of "
        "the rest of this page."
    )

    st.markdown("#### Step 3 — The loop, formally")
    st.markdown(
        """
        Every feedback controller follows the same loop. The robot measures its
        state, computes an error, passes it through a controller, and sends a
        command to the plant (the physical system). The plant moves, and the
        cycle repeats.
        """
    )

    columns = st.columns(3)
    with columns[0]:
        st.markdown("**Error**")
        st.write(
            "The difference between where the robot wants to be (setpoint) "
            "and where it actually is (measurement)."
        )
        st.latex(r"e(t) = r(t) - y(t)")
    with columns[1]:
        st.markdown("**Controller**")
        st.write(
            "A rule that converts error into a command. PID uses three terms: "
            "proportional, integral, and derivative."
        )
        st.latex(r"u(t) = K_p\,e + K_i\!\int\!e\,dt + K_d\,\frac{de}{dt}")
    with columns[2]:
        st.markdown("**Plant**")
        st.write(
            "The physical system. The controller's output drives it: a motor, "
            "a heater, a rudder. The plant's response becomes the next measurement."
        )

    render_bridge(
        "The feedback loop in engineering",
        "Many engineering systems follow the same pattern: observe the current "
        "state, decide on a corrective action, apply it, and observe again. In PID "
        "control, <b>you</b> design this loop by choosing gains that shape how the "
        "controller reacts to error, accumulated drift, and rate of change.",
    )

    checkin = render_checkin(
        key="background_compare",
        title="The role of the engineer in PID",
        prompt="What decisions does a human engineer make when designing a PID controller, and why does that make PID a feedback controller?",
        placeholder="The engineer chooses the gains Kp, Ki, and Kd, which determine how the controller reacts to...",
    )

    render_bridge(
        "Tuning has real-world stakes",
        "The gains you pick decide how a real machine behaves around real people. "
        "Too aggressive and a car overshoots the stop line into a crosswalk; too "
        "timid and antilock brakes react too slowly. Antilock brakes, insulin pumps, "
        "elevator stops, drone landings — behind each is someone who chose the "
        "trade-off between speed and safety. Controller tuning is a "
        "<b>sociotechnical</b> decision, not just a math exercise.",
    )

    social_checkin = render_checkin(
        key="background_social",
        title="When tuning meets the real world",
        prompt=(
            "Pick a real system controlled by feedback (car brakes, a drone, a heater, "
            "an insulin pump...). What goes wrong for a person if its controller is tuned "
            "too aggressively, and what goes wrong if it is tuned too cautiously?"
        ),
        placeholder="For antilock brakes, too aggressive means... and too cautious means...",
    )

    both_complete = checkin["complete"] and social_checkin["complete"]

    left, center, right = st.columns([1, 1.2, 1])
    with left:
        if st.button("Back", width="stretch"):
            set_stage("pid_concepts")
    with center:
        if st.button(
            "Continue to PID playground",
            type="primary",
            width="stretch",
            disabled=not both_complete,
        ):
            set_stage("pid_playground")


# ---------------------------------------------------------------------------
# Page: PID Playground (component)
# ---------------------------------------------------------------------------

def render_pid_playground_page() -> None:
    st.title("PID Playground")
    st.markdown(
        """
        Drag the target around and watch the PID controller react in real time.

        - **P (proportional)** reacts to the current error -- how far away from the target.
        - **I (integral)** reacts to accumulated error -- fixes steady-state offset.
        - **D (derivative)** reacts to how fast the error is changing -- damps oscillation.

        Experiment with each slider independently to build intuition.
        """
    )

    pid_playground_component()

    checkin = render_checkin(
        key="pid_playground_terms",
        title="P, I, D in action",
        prompt=(
            "When you dragged the target, which term reacted first? "
            "Which term eliminated the final gap?"
        ),
        placeholder="The P term reacted first because... The I term helped eliminate...",
    )

    back_col, next_col = st.columns(2)
    if back_col.button("Back", width="stretch"):
        set_stage("background")
    if next_col.button(
        "Continue to odometry",
        type="primary",
        width="stretch",
        disabled=not checkin["complete"],
    ):
        set_stage("odom_background")


# ---------------------------------------------------------------------------
# Page: Odometry Background
# ---------------------------------------------------------------------------

_LESSONS_DIR = Path(__file__).parent / "odometry_lessons"


@functools.lru_cache(maxsize=None)
def _load_lesson_html(filename: str) -> str:
    return (_LESSONS_DIR / filename).read_text(encoding="utf-8")


def _embed_lesson(filename: str, *, height: int) -> None:
    components = require("streamlit.components.v1")
    components.html(_load_lesson_html(filename), height=height, scrolling=False)


def render_odom_background_page() -> None:
    st.title("Odometry: tracking position and heading")

    st.markdown(
        """
        Odometry estimates a robot's pose from wheel motion: where it is and which
        direction it is facing. This page builds from a single tracking wheel to a
        full 2D pose update with short interactive examples.

        Here's the thread to hold onto as you go: **we start from raw sensor counts
        and end at an (x, y, heading) estimate the controller can steer by.** Each
        section adds exactly one link in that chain.
        """
    )

    st.markdown(
        """
        > **The chain we're building:**
        > wheel turns → *encoder counts the turn* → *counts become distance* →
        > *two wheels' distances become heading* → **pose (x, y, θ)**
        """
    )

    # ------------------------------------------------------------------
    # Section 1 — Dead wheel
    # ------------------------------------------------------------------
    st.markdown("## 1 · Tracking wheel: measuring real motion")
    st.markdown(
        """
        Drive wheels can over-report motion when they slip, skid, or start too
        abruptly. The motor encoder still counts rotation, but that rotation may
        not match the robot's actual travel across the floor.

        A passive tracking wheel, often called a **dead wheel**, measures ground
        contact directly. Toggle the modes below to compare drive-wheel-only
        estimation with a tracking wheel measurement.
        """
    )
    _embed_lesson("01_dead_wheel.html", height=580)

    st.info(
        "**So we have a wheel that faithfully rolls along the ground.** But the robot "
        "can't see the wheel roll — it only gets electrical pulses from a sensor. "
        "Next: how that sensor turns rotation into numbers the code can read.",
        icon="➡️",
    )

    # ------------------------------------------------------------------
    # Section 2 — Encoder
    # ------------------------------------------------------------------
    st.markdown("## 2 · Encoder ticks and direction")
    st.markdown(
        """
        An **encoder** is the sensor on a wheel axle that reports how much the
        wheel has turned. Most robotics encoders are *optical quadrature*
        encoders: a slotted disk passes two light sensors, and each slot is
        counted as a **tick**. The offset between channels A and B shows whether
        the wheel is moving forward or reverse.

        Use the animation to connect physical slots, tick counts, and waveform
        direction.
        """
    )
    _embed_lesson("02_encoder.html", height=620)

    st.info(
        "**Now we can count how far the wheel turned, in ticks.** But ticks aren't "
        "meters — a big wheel covers more ground per tick than a small one. Next: "
        "converting rotation into actual distance rolled across the floor.",
        icon="➡️",
    )

    # ------------------------------------------------------------------
    # Section 3 — Wheel unroll
    # ------------------------------------------------------------------
    st.markdown("## 3 · From wheel rotation to distance rolled")
    st.markdown(
        """
        If a wheel rolls without slipping, the distance it travels is the length
        of tread that contacts the ground. One full rotation moves the robot by
        one **circumference**: $C = \\pi D$. The animation shows one wheel
        rotation unfolding into one circumference of travel.

        The general form works for any angle:

        $$\\text{distance} = \\theta_{\\text{rad}} \\cdot r = \\frac{\\theta_{\\text{deg}}}{360°} \\cdot \\pi D$$

        This is why *angle rotated × wheel radius = distance traveled*.
        """
    )
    _embed_lesson("05_wheel_unroll.html", height=620)

    st.info(
        "**One wheel gives us distance along a straight line — but robots turn.** "
        "A single wheel can't tell which way the robot is facing. The trick: use "
        "*two* wheels a known distance apart. When they roll different amounts, the "
        "robot must have rotated. Next: turning that difference into a heading.",
        icon="➡️",
    )

    # ------------------------------------------------------------------
    # Section 4 — Heading geometry
    # ------------------------------------------------------------------
    st.markdown("## 4 · Two wheels give position *and* heading")

    st.markdown(
        """
        One wheel tells you how far it rolled, but not which way the robot is
        facing. The key idea of differential-drive odometry is simple:

        **if the two wheels roll different distances, the robot must have turned.**

        Picture the robot pivoting. The outer wheel traces a bigger circle than the
        inner wheel, so it rolls farther. The *difference* between the two wheel
        distances is exactly the extra arc the outer wheel swept — and that extra
        arc, divided by the track width, is the turn angle.
        """
    )

    left_col, right_col = st.columns(2)
    with left_col:
        st.markdown("**Left wheel rolls** $d_L$")
        st.markdown("**Right wheel rolls** $d_R$")
        st.markdown("**Track width** (wheel spacing) $L$")
    with right_col:
        st.markdown("How far the center moved:")
        st.latex(r"\Delta s = \frac{d_L + d_R}{2}")
        st.markdown("How much the heading turned:")
        st.latex(r"\Delta\theta = \frac{d_R - d_L}{L}")

    st.markdown(
        "Then the robot's pose $(x, y, \\theta)$ updates by stepping forward "
        "$\\Delta s$ along the *average* heading during the turn:"
    )
    st.latex(r"x \leftarrow x + \Delta s \cos\!\left(\theta + \tfrac{\Delta\theta}{2}\right)")
    st.latex(r"y \leftarrow y + \Delta s \sin\!\left(\theta + \tfrac{\Delta\theta}{2}\right)")
    st.latex(r"\theta \leftarrow \theta + \Delta\theta")

    st.markdown(
        "Drag the two wheel sliders in the tool below and watch $\\Delta\\theta$ "
        "update: equal distances go straight, a bigger right wheel turns left, a "
        "bigger left wheel turns right."
    )
    _embed_lesson("06_heading_geometry.html", height=560)

    # ------------------------------------------------------------------
    # Wrap-up
    # ------------------------------------------------------------------
    render_bridge(
        "Why accurate observations matter",
        "Feedback control depends on the sensor estimate it receives. "
        "Odometry gives a wheeled robot its running estimate of position and heading. "
        "When that estimate drifts, every controller that depends on it is working from "
        "the wrong map. Tracking wheels, encoders, and the geometry above are the basic "
        "tools for keeping that estimate aligned with reality.",
    )

    checkin = render_checkin(
        key="odom_background_wheels",
        title="Wheel motion to pose",
        prompt=(
            "If the right wheel rolls forward 6 cm and the left wheel doesn't move, "
            "which way does the robot turn, and why? Use the heading formula in your answer."
        ),
        choices=("Turns left", "Turns right", "Drives straight"),
        placeholder="It turns... because dR - dL is... so dθ is...",
    )

    back_col, next_col = st.columns(2)
    if back_col.button("Back", width="stretch"):
        set_stage("pid_playground")
    if next_col.button(
        "Continue to the lab",
        type="primary",
        width="stretch",
        disabled=not checkin["complete"],
    ):
        set_stage("lab")


# ---------------------------------------------------------------------------
# Page: Lab (multi-mission)
# ---------------------------------------------------------------------------

def render_lab_page() -> None:
    context = mission_context()
    render_mission_header(context)

    current = active_mission()
    if current == "mission_1":
        render_mission_1(context)
    elif current == "mission_2":
        render_mission_2(context)
    else:
        render_mission_3(context)


# -- Mission 1: Two-Link Robot Arm -----------------------------------------


def _mission1_openloop_svg(trials: list["OpenLoopTrial"], target: float = 2.0) -> str:
    track_w = 500
    track_h = 120
    max_m = 3.0
    px_per_m = (track_w - 60) / max_m
    track_y = 75
    track_left = 30
    colors = ["#f97316", "#fb923c", "#fdba74"]
    labels = ["Normal", "Low batt", "Hi fric"]
    style = "<style>"
    for i, trial in enumerate(trials):
        end_x = track_left + trial.final_distance * px_per_m
        style += (
            "@keyframes slide-ol-" + str(i) + "{"
            "0%{transform:translateX(0)}"
            "100%{transform:translateX(" + f"{end_x - track_left:.1f}" + "px)}"
            "}"
            ".m1ol-robot-" + str(i) + "{"
            "animation:slide-ol-" + str(i) + " 2s ease-out forwards;"
            "}"
        )
    style += "</style>"
    svg = (
        '<div style="overflow-x:auto">'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + str(track_w) + " " + str(track_h) + '"'
        ' width="' + str(track_w) + '" height="' + str(track_h) + '" style="max-width:100%">'
        + style
    )
    svg += (
        '<rect x="' + str(track_left) + '" y="' + str(track_y) + '"'
        ' width="' + str(track_w - 60) + '" height="4" rx="2" fill="#d1d5db"/>'
    )
    target_x = track_left + target * px_per_m
    svg += (
        '<line x1="' + f"{target_x:.1f}" + '" y1="' + str(track_y - 30) + '"'
        ' x2="' + f"{target_x:.1f}" + '" y2="' + str(track_y + 10) + '"'
        ' stroke="#0d9488" stroke-width="2" stroke-dasharray="5,3"/>'
    )
    svg += (
        '<rect x="' + f"{target_x - 10:.1f}" + '" y="' + str(track_y - 35) + '"'
        ' width="20" height="5" rx="2" fill="#0d9488" opacity="0.6"/>'
    )
    for i in range(len(trials)):
        robot_y = track_y - 22 + i * 10
        svg += (
            '<rect class="m1ol-robot-' + str(i) + '"'
            ' x="' + str(track_left) + '" y="' + str(robot_y) + '"'
            ' width="18" height="8" rx="3"'
            ' fill="' + colors[i] + '" opacity="0.9"/>'
        )
    legend_x = track_left
    for i in range(len(trials)):
        lx = legend_x + i * 80
        svg += (
            '<circle cx="' + str(lx) + '" cy="10" r="4" fill="' + colors[i] + '"/>'
            '<rect x="' + str(lx + 8) + '" y="5" width="55" height="10" fill="none"/>'
        )
        for ci, ch in enumerate(labels[i]):
            svg += (
                '<rect x="' + str(lx + 8 + ci * 6) + '" y="6" width="5" height="8"'
                ' rx="1" fill="' + colors[i] + '" opacity="' + str(0.25 + 0.05 * ci) + '"/>'
            )
    for m_val in [0, 1, 2, 3]:
        tick_x = track_left + m_val * px_per_m
        svg += (
            '<line x1="' + f"{tick_x:.1f}" + '" y1="' + str(track_y + 4) + '"'
            ' x2="' + f"{tick_x:.1f}" + '" y2="' + str(track_y + 12) + '"'
            ' stroke="#9ca3af" stroke-width="1"/>'
        )
    svg += "</svg></div>"
    return svg


def _mission1_pid_svg(result: "PIDResult") -> str:
    W, H = 540, 200
    pad_l, pad_r, pad_t, pad_b = 40, 20, 20, 30
    plot_w = W - pad_l - pad_r
    plot_h = H - pad_t - pad_b

    t_max = result.time[-1] if result.time[-1] > 0 else 1.0
    max_pos = max(max(abs(p) for p in result.position), result.target) * 1.15
    if max_pos <= 0:
        max_pos = 1.0
    max_err = max(abs(e) for e in result.error) if result.error else 1.0
    if max_err <= 0:
        max_err = 1.0

    def tx(t: float) -> float:
        return pad_l + (t / t_max) * plot_w

    def py(p: float) -> float:
        return pad_t + plot_h - (p / max_pos) * plot_h

    def ey(e: float) -> float:
        mid = pad_t + plot_h * 0.5
        return mid - (e / max_err) * (plot_h * 0.4)

    n = len(result.position)
    sample = max(1, n // 80)
    pos_pts = " ".join(f"{tx(result.time[i]):.1f},{py(result.position[i]):.1f}" for i in range(0, n, sample))
    if (n - 1) % sample != 0:
        pos_pts += f" {tx(result.time[-1]):.1f},{py(result.position[-1]):.1f}"

    err_pts = " ".join(f"{tx(result.time[i]):.1f},{ey(result.error[i]):.1f}" for i in range(0, n, sample))
    if (n - 1) % sample != 0:
        err_pts += f" {tx(result.time[-1]):.1f},{ey(result.error[-1]):.1f}"

    pos_len = plot_w * 2.5
    err_len = plot_w * 3.0
    anim_dur = min(t_max, 4.0)

    target_y = py(result.target)

    svg = (
        '<div style="overflow-x:auto">'
        '<svg xmlns="http://www.w3.org/2000/svg"'
        f' viewBox="0 0 {W} {H}" width="{W}" height="{H}" style="max-width:100%">'
    )

    svg += (
        '<style>'
        f'@keyframes m1g-draw-pos{{to{{stroke-dashoffset:0}}}}'
        f'@keyframes m1g-draw-err{{to{{stroke-dashoffset:0}}}}'
        '@keyframes m1g-dot{0%{opacity:0}5%{opacity:1}}'
        f'.m1g-pos{{stroke-dasharray:{pos_len:.0f};stroke-dashoffset:{pos_len:.0f};'
        f'animation:m1g-draw-pos {anim_dur:.1f}s linear forwards}}'
        f'.m1g-err{{stroke-dasharray:{err_len:.0f};stroke-dashoffset:{err_len:.0f};'
        f'animation:m1g-draw-err {anim_dur:.1f}s linear forwards}}'
        f'.m1g-dot{{animation:m1g-dot {anim_dur:.1f}s linear forwards}}'
        '</style>'
    )

    svg += f'<rect x="{pad_l}" y="{pad_t}" width="{plot_w}" height="{plot_h}" rx="4" fill="rgba(0,0,0,0.06)"/>'

    for frac in (0.25, 0.5, 0.75):
        gy = pad_t + plot_h * (1 - frac)
        svg += f'<line x1="{pad_l}" y1="{gy:.0f}" x2="{pad_l + plot_w}" y2="{gy:.0f}" stroke="rgba(150,150,150,0.12)" stroke-width="0.5"/>'

    for frac in (0.25, 0.5, 0.75):
        gx = pad_l + plot_w * frac
        svg += f'<line x1="{gx:.0f}" y1="{pad_t}" x2="{gx:.0f}" y2="{pad_t + plot_h}" stroke="rgba(150,150,150,0.12)" stroke-width="0.5"/>'

    svg += (
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + plot_h}" stroke="rgba(150,150,150,0.3)" stroke-width="1"/>'
        f'<line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{pad_l + plot_w}" y2="{pad_t + plot_h}" stroke="rgba(150,150,150,0.3)" stroke-width="1"/>'
    )

    for sec in range(int(t_max) + 1):
        tick_x = tx(sec)
        if tick_x <= pad_l + plot_w:
            svg += f'<line x1="{tick_x:.0f}" y1="{pad_t + plot_h}" x2="{tick_x:.0f}" y2="{pad_t + plot_h + 4}" stroke="rgba(150,150,150,0.4)" stroke-width="1"/>'

    svg += (
        f'<line x1="{pad_l}" y1="{target_y:.1f}" x2="{pad_l + plot_w}" y2="{target_y:.1f}"'
        ' stroke="#0d9488" stroke-width="1.5" stroke-dasharray="6,4"/>'
    )

    zero_y = ey(0)
    svg += (
        f'<line x1="{pad_l}" y1="{zero_y:.1f}" x2="{pad_l + plot_w}" y2="{zero_y:.1f}"'
        ' stroke="rgba(239,68,68,0.15)" stroke-width="0.5" stroke-dasharray="3,3"/>'
    )

    svg += f'<polyline class="m1g-err" points="{err_pts}" fill="none" stroke="#ef4444" stroke-width="1.5" opacity="0.5" stroke-linejoin="round"/>'

    svg += f'<polyline class="m1g-pos" points="{pos_pts}" fill="none" stroke="#f97316" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>'

    peak_pos = max(result.position)
    if peak_pos > result.target * 1.05:
        peak_idx = result.position.index(peak_pos)
        px_x = tx(result.time[peak_idx])
        px_y = py(peak_pos)
        svg += f'<circle class="m1g-dot" cx="{px_x:.1f}" cy="{px_y:.1f}" r="4" fill="#ef4444" opacity="0.6"/>'
        svg += (
            f'<line x1="{px_x:.1f}" y1="{px_y:.1f}" x2="{px_x:.1f}" y2="{target_y:.1f}"'
            ' stroke="#ef4444" stroke-width="0.7" stroke-dasharray="2,2" opacity="0.4"/>'
        )

    settle_x = tx(result.time[-1])
    settle_y = py(result.position[-1])
    svg += f'<circle class="m1g-dot" cx="{settle_x:.1f}" cy="{settle_y:.1f}" r="3" fill="#22c55e" opacity="0.6"/>'

    legend_x = pad_l + plot_w - 100
    legend_y = pad_t + 8
    svg += (
        f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 18}" y2="{legend_y}" stroke="#0d9488" stroke-width="1.5" stroke-dasharray="4,3"/>'
        f'<circle cx="{legend_x + 24}" cy="{legend_y}" r="2.5" fill="#0d9488"/>'
    )
    svg += (
        f'<line x1="{legend_x + 35}" y1="{legend_y}" x2="{legend_x + 53}" y2="{legend_y}" stroke="#f97316" stroke-width="2.5" stroke-linecap="round"/>'
        f'<circle cx="{legend_x + 59}" cy="{legend_y}" r="2.5" fill="#f97316"/>'
    )
    svg += (
        f'<line x1="{legend_x + 70}" y1="{legend_y}" x2="{legend_x + 88}" y2="{legend_y}" stroke="#ef4444" stroke-width="1.5" opacity="0.5"/>'
        f'<circle cx="{legend_x + 94}" cy="{legend_y}" r="2.5" fill="#ef4444" opacity="0.5"/>'
    )

    svg += '</svg></div>'
    return svg


def render_mission_1(context: dict[str, Any]) -> None:
    st.header("Mission 1: Two-link robot arm")
    st.markdown(
        """
        Use the arm playground as the whole first mission. Tune the shoulder and
        elbow PID controllers for the two-link arm, then test whether the arm can
        settle on the target poses without shaking or overshooting badly.

        Each target now plays in two beats — the arm **moves** to the pose, then
        **holds** so you can clearly see how cleanly it settled.

        Start with the automatic target poses. Once the arm nails three poses in
        a row, enter test mode and click targets in the workspace. Use gravity
        compensation when the shoulder struggles to carry the second link.
        """
    )

    arm_result = arm_playground_component(key="m1_arm_playground") or {}
    if not isinstance(arm_result, dict):
        arm_result = {}
    arm_gifs = persist_component_recording(
        "mission_1", arm_result, filename="latest_arm_tuning.gif"
    )
    if arm_result.get("recording_frames") and arm_gifs:
        st.caption(
            "Latest arm activity GIF automatically saved to "
            "`student_submission/mission_1/activity_gifs/latest_arm_tuning.gif`."
        )
    arm_activity_ready = bool(arm_result.get("activityComplete"))
    if arm_activity_ready:
        persist_latest_mission_run(
            "mission_1", component_state_without_recording(arm_result)
        )

    arm_checkin = render_checkin(
        key="m1_arm_tuning",
        title="Arm tuning notes",
        prompt=(
            "What did you change on the shoulder and elbow controllers to make "
            "the arm settle cleanly? Mention at least one PID term and what it fixed."
        ),
        placeholder="I increased/decreased... because the arm was...",
    )

    st.subheader("Mission check")
    st.write(
        "Use the playground until the arm can hold the rotating target poses and "
        "behaves reasonably in test mode. Then answer the check-in and submit."
    )

    if st.button(
        "Check Mission 1",
        key="check_m1",
        type="primary",
        disabled=not arm_checkin["complete"] or not arm_activity_ready,
    ):
        st.session_state["m1_passed"] = True
        st.session_state["m1_result"] = {
            "component": "two_link_arm",
            "activity": component_state_without_recording(arm_result),
            "checkin": arm_checkin,
        }
        st.session_state["m1_params"] = {
            "activity": "two_link_arm_pid_tuning",
            **arm_result.get("params", {}),
        }
        st.session_state["m1_metrics"] = {
            "completed": True,
            **arm_result.get("metrics", {}),
        }

    if not arm_checkin["complete"]:
        st.caption("Answer the arm tuning check-in before running the mission check.")
    elif not arm_activity_ready:
        st.caption("Hold three target poses so the arm run can be recorded before checking the mission.")

    if st.session_state.get("m1_passed") is True:
        st.success("Mission 1 passed. Export your arm tuning notes, then unlock Mission 2.")

        identity = render_student_identity()
        explanations = render_mission_explanations("mission_1")
        activity_gifs = activity_gifs_from_state("mission_1")
        explanations_complete = all(v.strip() for v in explanations.values())

        zip_data = {
            "params": st.session_state.get("m1_params", {}),
            "metrics": st.session_state.get("m1_metrics", {}),
            "checkin": arm_checkin,
            "csv_files": {},
            "figures": {},
            "activity_gifs": activity_gifs,
        }
        if not explanations_complete:
            st.caption("Answer all explanation prompts before continuing.")

        if st.button(
            "Save to submissions folder and unlock Mission 2",
            key="unlock_m2",
            disabled=not explanations_complete,
        ):
            save_mission_submission("mission_1", zip_data, explanations, identity)
            mark_mission_complete("mission_1")
            request_streamlit_rerun()




# -- Mission 2: Odometry Calibration --------------------------------------


def _mission2_odom_svg(result: OdomResult) -> str:
    """Return an animated SVG showing the true path vs odometry estimate."""
    n_frames = 25
    n_pts = len(result.true_x)
    if n_pts < 2:
        return ""
    indices = [int(i * (n_pts - 1) / (n_frames - 1)) for i in range(n_frames)]
    svg_w, svg_h = 500, 350
    pad = 40
    all_x = result.true_x + result.odom_x
    all_y = result.true_y + result.odom_y
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    range_x = max_x - min_x if max_x != min_x else 1.0
    range_y = max_y - min_y if max_y != min_y else 1.0
    scale = min((svg_w - 2 * pad) / range_x, (svg_h - 2 * pad) / range_y)
    cx = svg_w / 2
    cy = svg_h / 2
    data_cx = (min_x + max_x) / 2
    data_cy = (min_y + max_y) / 2
    def tx(wx: float) -> float:
        return cx + (wx - data_cx) * scale
    def ty(wy: float) -> float:
        return cy - (wy - data_cy) * scale
    true_pts = " ".join(f"{tx(result.true_x[i]):.1f},{ty(result.true_y[i]):.1f}" for i in range(n_pts))
    odom_pts = " ".join(f"{tx(result.odom_x[i]):.1f},{ty(result.odom_y[i]):.1f}" for i in range(n_pts))
    true_kf_lines: list[str] = []
    odom_kf_lines: list[str] = []
    for fi, idx in enumerate(indices):
        pct = fi * 100 // (n_frames - 1)
        sx_t = tx(result.true_x[idx])
        sy_t = ty(result.true_y[idx])
        th_t = -math.degrees(result.true_theta[idx])
        true_kf_lines.append(f"{pct}% {{ transform: translate({sx_t:.1f}px,{sy_t:.1f}px) rotate({th_t:.1f}deg); }}")
        sx_o = tx(result.odom_x[idx])
        sy_o = ty(result.odom_y[idx])
        th_o = -math.degrees(result.odom_theta[idx])
        odom_kf_lines.append(f"{pct}% {{ transform: translate({sx_o:.1f}px,{sy_o:.1f}px) rotate({th_o:.1f}deg); }}")
    true_kf = " ".join(true_kf_lines)
    odom_kf = " ".join(odom_kf_lines)
    anim_dur = "6s"
    start_true_x = tx(result.true_x[0])
    start_true_y = ty(result.true_y[0])
    start_odom_x = tx(result.odom_x[0])
    start_odom_y = ty(result.odom_y[0])
    lg_x = svg_w - pad + 5
    lg_y1 = pad
    lg_y2 = lg_y1 + 18
    svg = (
        '<div style="display:flex;justify-content:center;margin:1rem 0;">'
        f'<svg viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg"'
        f' style="max-width:{svg_w}px;width:100%;height:auto;">'
        '<style>'
        f'@keyframes m2-true {{ {true_kf} }}'
        f' @keyframes m2-odom {{ {odom_kf} }}'
        f' .m2-bot-true {{ animation: m2-true {anim_dur} linear infinite; }}'
        f' .m2-bot-odom {{ animation: m2-odom {anim_dur} linear infinite; }}'
        '</style>'
        f'<rect x="0" y="0" width="{svg_w}" height="{svg_h}" rx="12" fill="#1e1e2e"/>'
        f'<polyline points="{true_pts}" fill="none" stroke="#0d9488" stroke-width="2" stroke-linejoin="round"/>'
        f'<polyline points="{odom_pts}" fill="none" stroke="#f97316" stroke-width="2" stroke-linejoin="round"'
        ' stroke-dasharray="6,4"/>'
        f'<circle cx="{start_true_x:.1f}" cy="{start_true_y:.1f}" r="4" fill="#0d9488"/>'
        f'<circle cx="{start_odom_x:.1f}" cy="{start_odom_y:.1f}" r="4" fill="#f97316" opacity="0.7"/>'
        '<polygon points="-6,5 -6,-5 8,0" fill="#0d9488"'
        ' class="m2-bot-true" style="transform-origin:0 0;"/>'
        '<polygon points="-6,5 -6,-5 8,0" fill="#f97316" opacity="0.55"'
        ' class="m2-bot-odom" style="transform-origin:0 0;"/>'
        f'<line x1="{lg_x}" y1="{lg_y1}" x2="{lg_x + 18}" y2="{lg_y1}"'
        ' stroke="#0d9488" stroke-width="2"/>'
        f'<circle cx="{lg_x + 22}" cy="{lg_y1}" r="3" fill="#0d9488"/>'
        f'<line x1="{lg_x}" y1="{lg_y2}" x2="{lg_x + 18}" y2="{lg_y2}"'
        ' stroke="#f97316" stroke-width="2" stroke-dasharray="4,3"/>'
        f'<circle cx="{lg_x + 22}" cy="{lg_y2}" r="3" fill="#f97316" opacity="0.7"/>'
        '</svg>'
        '</div>'
    )
    return svg


def render_mission_2(context: dict[str, Any]) -> None:
    st.subheader("Mission 2: Holonomic odometry tuning")
    st.markdown(
        """
        This mission is one odometry tuning activity. The robot is holonomic, so
        it can drive forward/back and strafe left/right. Two odometry pods measure
        those two axes: one forward pod for `x`, and one sideways pod for `y`.

        Click the simple movement commands, tune the forward and strafe pod scale
        values live while the robot drives calibration loops, then run the test
        sequence. Pass when the estimated final pose stays under the allowed error.
        """
    )
    _embed_lesson("07_holonomic_pods.html", height=600)

    result = odometry_playground_component(key="m2_odometry_ftc") or {}
    odometry_gifs = persist_component_recording(
        "mission_2",
        result if isinstance(result, dict) else {},
        filename="latest_odometry_test.gif",
    )
    if isinstance(result, dict) and result.get("recording_frames") and odometry_gifs:
        st.caption(
            "Latest odometry test GIF automatically saved to "
            "`student_submission/mission_2/activity_gifs/latest_odometry_test.gif`."
        )
        persist_latest_mission_run(
            "mission_2", component_state_without_recording(result)
        )
    passed = bool(result.get("passed")) if isinstance(result, dict) else False
    max_error = float(result.get("maxError", 999.0)) if isinstance(result, dict) else 999.0
    final_error = float(result.get("finalError", 999.0)) if isinstance(result, dict) else 999.0
    params = result.get("params", {}) if isinstance(result, dict) else {}

    cols = st.columns(3)
    cols[0].metric("Test max error", f"{max_error:.2f} in" if max_error < 999 else "--")
    cols[1].metric("Final error", f"{final_error:.2f} in" if final_error < 999 else "--")
    cols[2].metric("Requirement", "< 3.0 in")

    c1 = render_checkin(
        key="m2_drift",
        title="Pod scale tuning",
        prompt="What did the forward and strafe pod scale values change in the estimate?",
        placeholder="The forward scale changed... The strafe scale changed...",
    )
    c2 = render_checkin(
        key="m2_turning",
        title="Holonomic odometry",
        prompt="Why does a holonomic robot need a sideways odometry pod for strafing?",
        placeholder="A sideways pod is needed because...",
    )

    checks_ready = c1["complete"] and c2["complete"]

    st.subheader("Mission check")
    st.write("**Goal**: run the odometry test sequence with max error under 3.0 inches.")

    if st.button("Check Mission 2", key="check_m2", type="primary", disabled=not checks_ready):
        if passed:
            st.session_state["m2_passed"] = True
            st.session_state["m2_result"] = component_state_without_recording(result)
            st.session_state["m2_params"] = params
            st.session_state["m2_metrics"] = {
                "max_error_in": max_error,
                "final_error_in": final_error,
                "passed": passed,
            }
        else:
            st.session_state["m2_passed"] = False

    if not checks_ready:
        st.caption("Answer both check-ins above before running the mission check.")

    if st.session_state.get("m2_passed") is True:
        st.success(f"Mission 2 passed. Max test error: {max_error:.2f} in.")

        identity = render_student_identity()
        explanations = render_mission_explanations("mission_2")
        activity_gifs = activity_gifs_from_state("mission_2")
        explanations_complete = all(v.strip() for v in explanations.values())

        zip_data = {
            "params": params,
            "metrics": st.session_state.get("m2_metrics", {}),
            "result": component_state_without_recording(result),
            "csv_files": {},
            "figures": {},
            "activity_gifs": activity_gifs,
        }
        if not explanations_complete:
            st.caption("Answer all explanation prompts before continuing.")

        if st.button(
            "Save to submissions folder and unlock Mission 3",
            key="unlock_m3",
            disabled=not explanations_complete,
        ):
            save_mission_submission("mission_2", zip_data, explanations, identity)
            mark_mission_complete("mission_2")
            request_streamlit_rerun()

    elif st.session_state.get("m2_passed") is False:
        st.error("Not yet. Run the test sequence in the activity and tune until max error is under 3.0 inches.")




# -- Mission 3: Path Following with PID -----------------------------------


def _mission3_pathfollow_svg(result: "PathFollowResult") -> str:
    vb_w, vb_h = 500, 400
    pad = 40
    all_x = list(result.path_x) + list(result.true_x)
    all_y = list(result.path_y) + list(result.true_y)
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    range_x = max_x - min_x if max_x > min_x else 1.0
    range_y = max_y - min_y if max_y > min_y else 1.0
    scale = min((vb_w - 2 * pad) / range_x, (vb_h - 2 * pad) / range_y)
    off_x = pad + ((vb_w - 2 * pad) - range_x * scale) / 2.0
    off_y = pad + ((vb_h - 2 * pad) - range_y * scale) / 2.0
    def tx(wx: float) -> float:
        return off_x + (wx - min_x) * scale
    def ty(wy: float) -> float:
        return off_y + (max_y - wy) * scale
    ref_pts = " ".join(f"{tx(result.path_x[i]):.1f},{ty(result.path_y[i]):.1f}" for i in range(len(result.path_x)))
    n_true = len(result.true_x)
    true_pts = " ".join(f"{tx(result.true_x[i]):.1f},{ty(result.true_y[i]):.1f}" for i in range(n_true))
    total_len = 0.0
    for i in range(1, n_true):
        dx = tx(result.true_x[i]) - tx(result.true_x[i - 1])
        dy = ty(result.true_y[i]) - ty(result.true_y[i - 1])
        seg = math.sqrt(dx * dx + dy * dy)
        total_len += seg
    if total_len < 1.0:
        total_len = 1.0
    dash_len = f"{total_len:.1f}"
    n_frames = 30
    step = max(1, n_true // n_frames)
    indices = list(range(0, n_true, step))
    if indices[-1] != n_true - 1:
        indices.append(n_true - 1)
    robot_kf = []
    for idx in indices:
        pct = (idx / max(n_true - 1, 1)) * 100.0
        sx = tx(result.true_x[idx])
        sy = ty(result.true_y[idx])
        angle_deg = -math.degrees(result.true_theta[idx])
        robot_kf.append(f"{pct:.1f}%{{transform:translate({sx:.1f}px,{sy:.1f}px) rotate({angle_deg:.1f}deg)}}")
    draw_kf = []
    for idx in indices:
        pct = (idx / max(n_true - 1, 1)) * 100.0
        frac = idx / max(n_true - 1, 1)
        offset_val = total_len * (1.0 - frac)
        draw_kf.append(f"{pct:.1f}%{{stroke-dashoffset:{offset_val:.1f}}}")
    corners: list[tuple[float, float]] = []
    px_list = list(result.path_x)
    py_list = list(result.path_y)
    if len(px_list) >= 4:
        seen: set[tuple[float, float]] = set()
        for i in range(len(px_list)):
            rounded = (round(px_list[i], 4), round(py_list[i], 4))
            if rounded not in seen:
                seen.add(rounded)
                corners.append((px_list[i], py_list[i]))
    style = "<style>"
    style += (
        "@keyframes m3-draw{"
        + "".join(draw_kf)
        + "}"
    )
    style += (
        "@keyframes m3-move{"
        + "".join(robot_kf)
        + "}"
    )
    style += (
        ".m3-actual{"
        "stroke-dasharray:" + dash_len + ";"
        "stroke-dashoffset:" + dash_len + ";"
        "animation:m3-draw 5s linear infinite;"
        "}"
    )
    style += (
        ".m3-robot{"
        "animation:m3-move 5s linear infinite;"
        "}"
    )
    style += (
        "@keyframes m3-pulse{0%{opacity:0.5}50%{opacity:1}100%{opacity:0.5}}"
        ".m3-wp{animation:m3-pulse 2s ease-in-out infinite;}"
    )
    style += "</style>"
    svg = (
        '<div style="overflow-x:auto">'
        '<svg xmlns="http://www.w3.org/2000/svg"'
        ' viewBox="0 0 ' + str(vb_w) + " " + str(vb_h) + '"'
        ' width="' + str(vb_w) + '" height="' + str(vb_h) + '"'
        ' style="max-width:100%">'
        + style
    )
    svg += (
        '<rect x="0" y="0" width="' + str(vb_w) + '" height="' + str(vb_h) + '"'
        ' rx="12" fill="#1e293b"/>'
    )
    svg += (
        '<polyline points="' + ref_pts + '"'
        ' fill="none" stroke="#0d9488" stroke-width="2"'
        ' stroke-dasharray="8,4" stroke-linejoin="round"/>'
    )
    svg += (
        '<polyline class="m3-actual" points="' + true_pts + '"'
        ' fill="none" stroke="#f97316" stroke-width="2"'
        ' stroke-linejoin="round" stroke-linecap="round"/>'
    )
    for cx_w, cy_w in corners:
        svg += (
            '<circle class="m3-wp" cx="' + f"{tx(cx_w):.1f}" + '" cy="' + f"{ty(cy_w):.1f}" + '"'
            ' r="5" fill="none" stroke="#0d9488" stroke-width="1.5"/>'
        )
        svg += (
            '<circle cx="' + f"{tx(cx_w):.1f}" + '" cy="' + f"{ty(cy_w):.1f}" + '"'
            ' r="2" fill="#0d9488"/>'
        )
    svg += (
        '<g class="m3-robot">'
        '<polygon points="-8,-5 8,0 -8,5" fill="#f97316" opacity="0.9"/>'
        '<circle r="2" fill="#fff" opacity="0.8"/>'
        '</g>'
    )
    svg += (
        '<rect x="' + str(vb_w - 130) + '" y="10" width="120" height="50"'
        ' rx="6" fill="#0f172a" opacity="0.7"/>'
    )
    svg += (
        '<line x1="' + str(vb_w - 120) + '" y1="28" x2="' + str(vb_w - 95) + '" y2="28"'
        ' stroke="#0d9488" stroke-width="2" stroke-dasharray="4,2"/>'
    )
    svg += (
        '<rect x="' + str(vb_w - 90) + '" y="22" width="8" height="8"'
        ' rx="2" fill="#0d9488" opacity="0.5"/>'
    )
    svg += (
        '<line x1="' + str(vb_w - 120) + '" y1="45" x2="' + str(vb_w - 95) + '" y2="45"'
        ' stroke="#f97316" stroke-width="2"/>'
    )
    svg += (
        '<polygon points="' + str(vb_w - 88) + ',42 ' + str(vb_w - 78) + ',45 ' + str(vb_w - 88) + ',48"'
        ' fill="#f97316" opacity="0.8"/>'
    )
    svg += "</svg></div>"
    return svg


def _waypoint_nav_svg(result: "WaypointNavResult") -> str:
    """Animated top-down view: the robot drives its TRUE path (an animated marker)
    past pedestrians while its BELIEVED (odometry) path is drawn dashed. Pedestrians
    show a safety ring that turns red if the true path breaches it."""
    vb_w, vb_h = 520, 440
    pad = 52
    wps = result.waypoints
    peds = result.pedestrians
    all_x = list(result.true_x) + list(result.odom_x) + [w[0] for w in wps] + [p[0] for p in peds] + [0.0]
    all_y = list(result.true_y) + list(result.odom_y) + [w[1] for w in wps] + [p[1] for p in peds] + [0.0]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    range_x = max_x - min_x if max_x > min_x else 1.0
    range_y = max_y - min_y if max_y > min_y else 1.0
    scale = min((vb_w - 2 * pad) / range_x, (vb_h - 2 * pad) / range_y)
    off_x = pad + ((vb_w - 2 * pad) - range_x * scale) / 2.0
    off_y = pad + ((vb_h - 2 * pad) - range_y * scale) / 2.0

    def tx(wx: float) -> float:
        return off_x + (wx - min_x) * scale

    def ty(wy: float) -> float:
        return off_y + (max_y - wy) * scale

    n = len(result.true_x)
    step = max(1, n // 90)
    idxs = list(range(0, n, step))
    if idxs[-1] != n - 1:
        idxs.append(n - 1)
    true_pts = " ".join(f"{tx(result.true_x[i]):.1f},{ty(result.true_y[i]):.1f}" for i in idxs)
    odom_pts = " ".join(f"{tx(result.odom_x[i]):.1f},{ty(result.odom_y[i]):.1f}" for i in idxs)

    # Robot animation keyframes along the TRUE path.
    kf = []
    for k, i in enumerate(idxs):
        pct = k * 100.0 / (len(idxs) - 1)
        kf.append(f"{pct:.1f}%{{transform:translate({tx(result.true_x[i]):.1f}px,{ty(result.true_y[i]):.1f}px)}}")
    dur = 6.0

    svg = (
        '<div style="overflow-x:auto">'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vb_w} {vb_h}"'
        f' width="{vb_w}" height="{vb_h}" style="max-width:100%">'
        '<style>'
        f'@keyframes m3move{{{" ".join(kf)}}}'
        f'.m3robot{{animation:m3move {dur:.1f}s linear infinite}}'
        '@keyframes m3ped{0%,100%{opacity:.55}50%{opacity:.9}}'
        '</style>'
        f'<rect x="0" y="0" width="{vb_w}" height="{vb_h}" rx="12" fill="#1e293b"/>'
    )
    # Start marker
    svg += f'<circle cx="{tx(0.0):.1f}" cy="{ty(0.0):.1f}" r="5" fill="#94a3b8"/>'
    svg += (
        f'<text x="{tx(0.0):.1f}" y="{ty(0.0) + 18:.1f}" fill="#94a3b8"'
        ' font-family="system-ui" font-size="11" text-anchor="middle">start</text>'
    )
    # Waypoints
    for i, (wx, wy) in enumerate(wps):
        cx, cy = tx(wx), ty(wy)
        truly = (not math.isnan(result.true_gap_at_reach[i])
                 and result.true_gap_at_reach[i] <= 0.24)
        ring = "#12b76a" if truly else "#f97316"
        svg += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="10" fill="none" stroke="{ring}" stroke-width="2"/>'
        svg += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3" fill="{ring}"/>'
        svg += (
            f'<text x="{cx:.1f}" y="{cy - 15:.1f}" fill="{ring}" font-family="system-ui"'
            f' font-size="11" font-weight="700" text-anchor="middle">WP{i + 1}</text>'
        )
    # Pedestrians with safety rings
    safe_px = result.safe_radius * scale
    for pi, (px, py) in enumerate(peds):
        cx, cy = tx(px), ty(py)
        # is THIS pedestrian breached by the true path?
        pgap = min(math.hypot(px - result.true_x[i], py - result.true_y[i]) for i in idxs)
        breached = pgap < result.safe_radius
        col = "#f04438" if breached else "#12b76a"
        fillc = "rgba(240,68,56,0.14)" if breached else "rgba(18,183,106,0.10)"
        svg += (
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{safe_px:.1f}" fill="{fillc}"'
            f' stroke="{col}" stroke-width="1.5" stroke-dasharray="4,3"/>'
        )
        # simple pedestrian glyph (head + body)
        svg += f'<circle class="m3ped" cx="{cx:.1f}" cy="{cy - 6:.1f}" r="4" fill="{col}"/>'
        svg += (
            f'<line class="m3ped" x1="{cx:.1f}" y1="{cy - 2:.1f}" x2="{cx:.1f}" y2="{cy + 7:.1f}"'
            f' stroke="{col}" stroke-width="3" stroke-linecap="round"/>'
        )
    # Believed (odometry) path
    svg += (
        f'<polyline points="{odom_pts}" fill="none" stroke="#f97316" stroke-width="2"'
        ' stroke-dasharray="7,4" stroke-linejoin="round" opacity="0.85"/>'
    )
    # True path
    svg += (
        f'<polyline points="{true_pts}" fill="none" stroke="#38bdf8" stroke-width="2.5"'
        ' stroke-linejoin="round" stroke-linecap="round"/>'
    )
    # Animated robot on the true path
    svg += (
        '<g class="m3robot">'
        '<circle r="6" fill="#38bdf8" stroke="#e0f2fe" stroke-width="1.5"/>'
        '</g>'
    )
    # Legend
    lx, ly = 14, 14
    svg += f'<rect x="{lx}" y="{ly}" width="210" height="62" rx="7" fill="#0f172a" opacity="0.82"/>'
    svg += f'<line x1="{lx + 10}" y1="{ly + 15}" x2="{lx + 34}" y2="{ly + 15}" stroke="#38bdf8" stroke-width="2.5"/>'
    svg += (f'<text x="{lx + 42}" y="{ly + 19}" fill="#cbd5e1" font-family="system-ui"'
            ' font-size="11">true path (reality)</text>')
    svg += (f'<line x1="{lx + 10}" y1="{ly + 32}" x2="{lx + 34}" y2="{ly + 32}" stroke="#f97316"'
            ' stroke-width="2.5" stroke-dasharray="6,3"/>')
    svg += (f'<text x="{lx + 42}" y="{ly + 36}" fill="#cbd5e1" font-family="system-ui"'
            ' font-size="11">what the robot believes</text>')
    svg += f'<circle cx="{lx + 22}" cy="{ly + 49}" r="4" fill="#12b76a"/>'
    svg += (f'<text x="{lx + 42}" y="{ly + 53}" fill="#cbd5e1" font-family="system-ui"'
            ' font-size="11">pedestrian + safe zone</text>')
    svg += "</svg></div>"
    return svg


def csv_for_waypoint_nav(result: "WaypointNavResult") -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["time", "true_x", "true_y", "true_theta", "odom_x", "odom_y", "odom_theta", "heading_error", "command"])
    for row in zip(result.time, result.true_x, result.true_y, result.true_theta,
                   result.odom_x, result.odom_y, result.odom_theta,
                   result.heading_error, result.command):
        writer.writerow(row)
    return buffer.getvalue()


def csv_for_drawn_route(state: dict[str, Any]) -> str:
    """Serialize the student-authored Mission 3 route."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["route_point", "x", "y"])
    writer.writerow([0, 0.0, 0.0])
    for index, point in enumerate(state.get("route", []), start=1):
        if isinstance(point, (list, tuple)) and len(point) >= 2:
            writer.writerow([index, point[0], point[1]])
    return buffer.getvalue()


def csv_for_drawn_waypoint_trace(state: dict[str, Any]) -> str:
    """Serialize the true and estimated pose trace returned by the CCv2 simulator."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "time", "true_x", "true_y", "true_theta",
        "odom_x", "odom_y", "odom_theta",
    ])
    for row in state.get("trace", []):
        if isinstance(row, (list, tuple)) and len(row) >= 7:
            writer.writerow(row[:7])
    return buffer.getvalue()


def render_mission_3(context: dict[str, Any]) -> None:
    st.subheader("Mission 3: Draw, tune, and drive a safe sidewalk route")
    st.markdown(
        """
        Plan the motion before tuning it. Press and drag from **START** to draw a
        smooth route that visits **WP1 → WP2 → WP3 → WP4 in order** and bends around
        both pedestrians. The route ends at WP4; it does not need to form a loop.
        Then tune heading PID, speed, and the wheel-radius estimate until the robot's
        **true path** follows your curve precisely enough to complete the trip safely.
        """
    )

    with st.expander("How planning, PID, and odometry work together", expanded=False):
        st.markdown(
            """
            1. **Plan:** your cyan polyline is the reference route. Extra route points
               can make turns smoother and leave more clearance around a person.
            2. **Estimate:** wheel odometry supplies the pose *(x, y, heading)* that the
               controller believes. The orange marker shows that belief.
            3. **Control:** the robot aims at the next route point. Heading error is
               `desired heading − estimated heading`; PID turns that error into wheel
               speed differences.
            4. **Verify reality:** the green trace is the true path. A wrong wheel
               radius makes it separate from the estimate. Poor gains or excessive
               speed make it cut corners or oscillate.

            Passing requires every named waypoint, at least **0.28 m** from each
            pedestrian, mean path error at most **0.05 m**, and maximum path error
            at most **0.10 m**.
            """
        )

    initial_component_state = st.session_state.get("m3_component_state", {})
    if not isinstance(initial_component_state, dict):
        initial_component_state = {}
    component_result = waypoint_draw_component(initial_component_state)
    latest_component_state = getattr(component_result, "state", None)
    if isinstance(latest_component_state, dict):
        st.session_state["m3_component_state"] = latest_component_state
    else:
        latest_component_state = initial_component_state

    activity_gifs = persist_component_recording("mission_3", latest_component_state)
    if latest_component_state.get("drove") and activity_gifs:
        st.caption(
            "Latest drive GIF automatically saved to "
            "`student_submission/mission_3/activity_gifs/latest_drive.gif`."
        )
        persist_latest_mission_run(
            "mission_3", component_state_without_recording(latest_component_state)
        )

    signature_state = {
        key: value
        for key, value in latest_component_state.items()
        if key not in ("recording_frames", "recording_frame_duration_ms")
    }
    state_signature = json.dumps(signature_state, sort_keys=True, default=str)
    checked_signature = st.session_state.get("m3_checked_signature")
    if checked_signature and checked_signature != state_signature:
        st.session_state["m3_passed"] = None

    drove = bool(latest_component_state.get("drove"))
    run_passed = bool(latest_component_state.get("passed"))
    current_metrics = latest_component_state.get("metrics", {})
    if not isinstance(current_metrics, dict):
        current_metrics = {}

    render_bridge(
        "Tuning is a safety decision, not just a number",
        "The route, gains, speed, and calibration jointly decide how a real machine "
        "behaves around people. A margin on this screen represents physical space "
        "between a robot and someone using the sidewalk.",
    )

    c1 = render_checkin(
        key="m3_heading_pid",
        title="How the heading PID steers",
        prompt="Walk through one tracking step: how does the robot turn the next route point into a steering command?",
        placeholder="The robot uses its estimated pose to compute a desired heading, then the PID...",
    )
    c2 = render_checkin(
        key="m3_integration",
        title="State-estimation precision",
        prompt="Explain why a well-tuned PID can still follow the wrong physical path when the wheel-radius estimate is inaccurate.",
        placeholder="The PID only sees the odometry estimate, so if the estimate is wrong...",
    )
    c3 = render_checkin(
        key="ethics_failure_mode",
        title="The specific failure",
        prompt="Controllers fail in specific ways. Describe the most dangerous failure this delivery robot can have on a busy sidewalk, and tie it to what you saw here.",
        placeholder="The most dangerous failure is... which is what happened when...",
    )
    c4 = render_checkin(
        key="ethics_margin",
        title="The trade-off you would set",
        prompt="Tuning for speed increases overshoot and drift; tuning for safety costs time. What safety margin would you require around a pedestrian, and what performance would you give up for it?",
        placeholder="I would require a margin of... accepting the robot is slower because...",
    )
    c5 = render_checkin(
        key="ethics_accountability",
        title="Accountability",
        prompt="When this robot injures someone because of a tuning or calibration choice, who is responsible — the engineer, the company, the operator? Justify your answer.",
        placeholder="Responsibility lies primarily with... because...",
    )

    checks_ready = all(c["complete"] for c in (c1, c2, c3, c4, c5))

    st.divider()
    st.subheader("Mission check")
    st.write(
        "**Goal:** follow the route you drew, reach WP1–WP4 in order, stay at least "
        "0.28 m from pedestrians, and meet both tracking-error limits."
    )

    if st.button(
        "Check Mission 3",
        key="check_m3",
        type="primary",
        disabled=not checks_ready or not drove,
    ):
        st.session_state["m3_checked_signature"] = state_signature
        st.session_state["m3_passed"] = run_passed
        if run_passed:
            st.session_state["m3_result"] = latest_component_state
            st.session_state["m3_params"] = latest_component_state.get("params", {})
            st.session_state["m3_metrics"] = current_metrics

    if not checks_ready:
        st.caption("Answer all five reflections above before running the mission check.")
    elif not drove:
        st.caption("Draw a complete route and drive it before running the mission check.")

    if st.session_state.get("m3_passed") is True:
        saved_metrics = st.session_state.get("m3_metrics", current_metrics)
        st.success(
            "Mission 3 passed: all four waypoints, with "
            f"{float(saved_metrics.get('min_pedestrian_gap', 0.0)):.2f} m minimum "
            "pedestrian clearance."
        )

        identity = render_student_identity()
        explanations = render_mission_explanations("mission_3")
        activity_gifs = activity_gifs_from_state("mission_3")
        explanations_complete = all(v.strip() for v in explanations.values())

        zip_data = {
            "params": st.session_state.get("m3_params", {}),
            "metrics": st.session_state.get("m3_metrics", {}),
            "csv_files": {
                "drawn_route.csv": csv_for_drawn_route(st.session_state.get("m3_result", {})),
                "waypoint_nav_run.csv": csv_for_drawn_waypoint_trace(st.session_state.get("m3_result", {})),
            },
            "figures": {},
            "activity_gifs": activity_gifs,
        }
        if not explanations_complete:
            st.caption("Answer all explanation prompts before continuing.")

        if st.button(
            "Save Mission 3 and continue to final submission",
            key="finish_mission_3",
            disabled=not explanations_complete,
        ):
            save_mission_submission("mission_3", zip_data, explanations, identity)
            mark_mission_complete("mission_3")
            st.session_state.pop("mission_override", None)
            set_stage("export")

    elif st.session_state.get("m3_passed") is False:
        st.error(
            "Not yet. Use the component verdict and metrics to isolate the problem: "
            "revise the route for clearance, calibrate odometry if orange and green "
            "separate, or retune PID and speed if tracking error is too high."
        )




# ---------------------------------------------------------------------------
# Page: Final Export
# ---------------------------------------------------------------------------

def render_export_page() -> None:
    st.title("Final Submission")
    st.markdown(
        "Saving writes controller settings, odometry calibration, waypoint-navigation "
        "results, check-in answers, and CSV logs from all completed missions into your "
        "submissions folder. Commit that folder to Git and submit the commit link."
    )

    # Check mission completion
    progress = set(st.session_state.get("mission_progress", [])) & set(MISSION_ORDER)
    completed = len(progress)
    st.write(f"**Missions completed**: {completed}/3")
    if completed < 3:
        st.warning(
            "You have not completed all three missions yet. Go back and finish them "
            "for a complete submission."
        )
        if st.button("Back to lab", key="export_back_incomplete"):
            set_stage("lab")

    # Final reflection
    reflection = render_checkin(
        key="final_reflection",
        title="Put the two skills together",
        prompt="How do PID and odometry depend on each other on a real robot?",
        placeholder="Odometry estimates the robot's pose, and PID uses that estimate to...",
    )

    # Gather all check-in answers
    checkin_keys = [
        "background_compare", "background_social",
        "pid_playground_terms", "odom_background_wheels",
        "m1_arm_tuning",
        "m2_drift", "m2_turning", "m3_heading_pid", "m3_integration",
        "ethics_failure_mode", "ethics_margin", "ethics_accountability",
        "final_reflection",
    ]
    all_checkins = {}
    for k in checkin_keys:
        resp = checkin_response(k)
        all_checkins[k] = resp["note"] or resp["choice"]

    # Gather all mission data
    all_mission_data: dict[str, dict[str, Any]] = {}
    all_explanations = {
        mission_id: mission_explanations_from_state(mission_id)
        for mission_id in MISSION_ORDER
    }

    if st.session_state.get("m1_result"):
        all_mission_data["mission_1"] = {
            "params": st.session_state.get("m1_params", {}),
            "metrics": st.session_state.get("m1_metrics", {}),
            "result": st.session_state.get("m1_result", {}),
            "csv_files": {},
            "figures": {},
            "activity_gifs": activity_gifs_from_state("mission_1"),
        }

    if st.session_state.get("m2_result"):
        result = st.session_state["m2_result"]
        all_mission_data["mission_2"] = {
            "params": st.session_state.get("m2_params", {}),
            "metrics": st.session_state.get("m2_metrics", {}),
            "csv_files": {"odometry_run.csv": csv_for_odom(result)},
            "figures": {"odometry_plot.png": plot_odometry(result)},
            "activity_gifs": activity_gifs_from_state("mission_2"),
        }

    if st.session_state.get("m3_result"):
        result = st.session_state["m3_result"]
        all_mission_data["mission_3"] = {
            "params": st.session_state.get("m3_params", {}),
            "metrics": st.session_state.get("m3_metrics", {}),
            "csv_files": {
                "drawn_route.csv": csv_for_drawn_route(result),
                "waypoint_nav_run.csv": csv_for_drawn_waypoint_trace(result),
            },
            "figures": {},
            "activity_gifs": activity_gifs_from_state("mission_3"),
        }

    # Student info
    st.subheader("Student info")
    name = st.text_input("Name", key="export_student_name")
    student_id = st.text_input("Student ID or email", key="export_student_id")
    section = st.text_input("Section", key="export_student_section")
    identity = {
        "name": name.strip(),
        "student_id": student_id.strip(),
        "section": section.strip(),
    }

    all_answers_ready = reflection["complete"]

    if st.button(
        "Save complete submission folder",
        type="primary",
        disabled=not all_answers_ready,
    ):
        path = save_final_submission(
            all_mission_data,
            all_explanations,
            all_checkins,
            identity,
        )
        st.success(f"Saved to {path}. Commit this folder and submit the GitHub commit link.")
    if not all_answers_ready:
        st.caption("Answer the final reflection before saving.")

    if st.button("Back to lab", key="export_back_bottom"):
        set_stage("lab")


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def run_smoke_test() -> None:
    """Run simulations without Streamlit to verify correctness."""
    global np, plt
    np = require("numpy")
    plt = require("matplotlib.pyplot")

    print("Running PID smoke test...")
    pid_result = simulate_pid(kp=3.0, ki=0.5, kd=1.0, target=2.0)
    p_metrics = pid_metrics(pid_result)
    print(f"  Final error: {p_metrics['final_error']:.4f} m")
    print(f"  Overshoot:   {p_metrics['overshoot']:.4f} m")
    print(f"  Settling:    {p_metrics['settling_time']:.2f} s")

    print("Running open-loop smoke test...")
    trials = simulate_open_loop_trials(0.62, 2.0)
    mean_error = float(np.mean([abs(t.error) for t in trials]))
    print(f"  Mean absolute error: {mean_error:.3f} m")

    print("Running odometry smoke test...")
    odom_result = simulate_odometry(0.050, 0.34)
    o_metrics = odom_metrics(odom_result)
    print(f"  Position error: {o_metrics['final_position_error']:.4f} m")
    print(f"  Heading error:  {o_metrics['final_heading_error_deg']:.1f} deg")

    print("Running path following smoke test...")
    path_result = simulate_path_following(2.5, 0.1, 0.5)
    print(f"  Mean tracking error: {path_result.mean_tracking_error:.4f} m")
    print(f"  Max tracking error:  {path_result.max_tracking_error:.4f} m")

    print("\nSmoke test passed.")


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------

def run_streamlit_app() -> None:
    global st, np, plt
    st = require("streamlit")
    np = require("numpy")
    plt = require("matplotlib.pyplot")

    stage = str(st.session_state.get("stage", "intro"))
    lab_stage = stage == "lab"

    st.set_page_config(
        page_title="Week 4: PID and Odometry",
        page_icon="PID",
        layout="wide",
        initial_sidebar_state="expanded" if lab_stage else "collapsed",
    )
    set_sidebar_default_for_stage(expanded=lab_stage)
    scroll_to_top_if_requested()

    st.sidebar.caption("Local-only lab. Do not use Streamlit Cloud as submission storage.")
    render_instructor_controls()

    if stage == "intro":
        render_intro_page()
    elif stage == "pid_concepts":
        render_pid_concepts_page()
    elif stage == "background":
        render_background_page()
    elif stage == "pid_playground":
        render_pid_playground_page()
    elif stage == "odom_background":
        render_odom_background_page()
    elif stage == "lab":
        render_lab_page()
    elif stage == "export":
        render_export_page()
    else:
        set_stage("intro")

    # Auto-save text responses and recorded GIFs after the page has rendered, so
    # the latest widget values are captured without requiring a button press.
    autosave_responses_and_gifs()
    last_saved = st.session_state.get("_autosave_last")
    if last_saved:
        st.sidebar.caption(f"Responses & GIFs auto-saved to submissions folder ({last_saved}).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Week 4 PID and odometry teaching lab.")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run simulations without Streamlit to verify correctness.",
    )
    args = parser.parse_args()

    if args.smoke_test:
        run_smoke_test()
    else:
        run_streamlit_app()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
