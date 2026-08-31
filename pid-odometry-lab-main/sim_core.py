"""Simulation helpers for a PID and odometry teaching lab.

The module intentionally stays small and dependency-light.  Every public helper
accepts plain Python numbers and sequences, while returning dataclasses or lists
that are easy to inspect in Streamlit tables and charts.  NumPy is used when it
is installed, but the functions fall back to standard-library lists.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Callable, Iterable, Sequence

try:  # NumPy is optional for this lab.
    import numpy as _np
except Exception:  # pragma: no cover - depends on the teaching environment.
    _np = None


Number = int | float
Point = tuple[float, float]
Pose = tuple[float, float, float]
Profile = Number | Callable[[float], Number] | Sequence[tuple[float, Number]]

TAU = 2.0 * math.pi


def clamp(value: Number, low: Number | None = None, high: Number | None = None) -> float:
    """Clamp ``value`` to optional lower and upper bounds."""
    result = float(value)
    if low is not None:
        result = max(float(low), result)
    if high is not None:
        result = min(float(high), result)
    return result


def wrap_angle(theta: Number) -> float:
    """Wrap an angle in radians to the interval [-pi, pi)."""
    return ((float(theta) + math.pi) % TAU) - math.pi


def angle_error(target: Number, current: Number) -> float:
    """Return the shortest signed angular error from ``current`` to ``target``."""
    return wrap_angle(float(target) - float(current))


def _limits_pair(limits: tuple[Number | None, Number | None] | None) -> tuple[float | None, float | None]:
    if limits is None:
        return None, None
    low, high = limits
    low_f = None if low is None else float(low)
    high_f = None if high is None else float(high)
    if low_f is not None and high_f is not None and low_f > high_f:
        raise ValueError("lower limit must be <= upper limit")
    return low_f, high_f


def _profile_value(profile: Profile, t: float) -> float:
    """Evaluate a constant, callable, or piecewise-constant time profile."""
    if callable(profile):
        return float(profile(t))
    if isinstance(profile, (int, float)):
        return float(profile)
    if not profile:
        raise ValueError("profile sequence cannot be empty")

    current = float(profile[0][1])
    for start_t, value in profile:
        if t < float(start_t):
            break
        current = float(value)
    return current


@dataclass
class PIDStep:
    """One PID update sample."""

    t: float
    setpoint: float
    measurement: float
    error: float
    output: float
    p: float
    i: float
    d: float


@dataclass
class PIDController:
    """Minimal PID controller with output limits and integral clamping.

    ``update`` expects a positive ``dt`` in seconds.  Set
    ``derivative_on_measurement=True`` to avoid derivative kick when setpoints
    change abruptly.
    """

    kp: float = 1.0
    ki: float = 0.0
    kd: float = 0.0
    setpoint: float = 0.0
    output_limits: tuple[Number | None, Number | None] | None = None
    integral_limits: tuple[Number | None, Number | None] | None = None
    derivative_on_measurement: bool = False
    integral: float = 0.0
    previous_error: float | None = None
    previous_measurement: float | None = None
    last_output: float = 0.0
    last_terms: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def reset(self, integral: Number = 0.0) -> None:
        """Clear controller history while keeping gains and limits."""
        self.integral = float(integral)
        self.previous_error = None
        self.previous_measurement = None
        self.last_output = 0.0
        self.last_terms = (0.0, 0.0, 0.0)

    def update(
        self,
        measurement: Number,
        dt: Number,
        setpoint: Number | None = None,
        feedforward: Number = 0.0,
        wrap_error: bool = False,
    ) -> float:
        """Advance the controller by one step and return the command output."""
        dt_f = float(dt)
        if dt_f <= 0.0:
            raise ValueError("dt must be positive")

        if setpoint is not None:
            self.setpoint = float(setpoint)

        measurement_f = float(measurement)
        error = (
            angle_error(self.setpoint, measurement_f)
            if wrap_error
            else self.setpoint - measurement_f
        )

        p_term = self.kp * error
        self.integral += error * dt_f
        i_low, i_high = _limits_pair(self.integral_limits)
        self.integral = clamp(self.integral, i_low, i_high)
        i_term = self.ki * self.integral

        if self.derivative_on_measurement:
            if self.previous_measurement is None:
                derivative = 0.0
            else:
                derivative = -(measurement_f - self.previous_measurement) / dt_f
        else:
            if self.previous_error is None:
                derivative = 0.0
            else:
                derivative = (error - self.previous_error) / dt_f
        d_term = self.kd * derivative

        raw_output = p_term + i_term + d_term + float(feedforward)
        o_low, o_high = _limits_pair(self.output_limits)
        output = clamp(raw_output, o_low, o_high)

        self.previous_error = error
        self.previous_measurement = measurement_f
        self.last_output = output
        self.last_terms = (p_term, i_term, d_term)
        return output

    def snapshot(self, t: Number, measurement: Number) -> PIDStep:
        """Return the latest controller terms as a row-like dataclass."""
        p_term, i_term, d_term = self.last_terms
        error = (
            self.previous_error
            if self.previous_error is not None
            else self.setpoint - float(measurement)
        )
        return PIDStep(
            t=float(t),
            setpoint=float(self.setpoint),
            measurement=float(measurement),
            error=float(error),
            output=float(self.last_output),
            p=float(p_term),
            i=float(i_term),
            d=float(d_term),
        )


@dataclass
class FirstOrderPlant:
    """First-order plant: dy/dt = (gain * u + bias + disturbance - y) / tau."""

    y: float = 0.0
    tau: float = 1.0
    gain: float = 1.0
    bias: float = 0.0
    disturbance: float = 0.0
    output_limits: tuple[Number | None, Number | None] | None = None

    def step(self, command: Number, dt: Number) -> float:
        dt_f = float(dt)
        if dt_f <= 0.0:
            raise ValueError("dt must be positive")
        tau_f = max(1e-9, float(self.tau))
        target = self.gain * float(command) + self.bias + self.disturbance
        self.y += (target - self.y) * dt_f / tau_f
        low, high = _limits_pair(self.output_limits)
        self.y = clamp(self.y, low, high)
        return self.y


@dataclass
class HeadingPlant:
    """Simple heading plant with first-order angular-velocity response."""

    theta: float = 0.0
    omega: float = 0.0
    tau: float = 0.35
    command_gain: float = 1.0
    max_omega: float | None = None

    def step(self, command: Number, dt: Number) -> tuple[float, float]:
        dt_f = float(dt)
        if dt_f <= 0.0:
            raise ValueError("dt must be positive")
        tau_f = max(1e-9, float(self.tau))
        target_omega = self.command_gain * float(command)
        if self.max_omega is not None:
            target_omega = clamp(target_omega, -abs(self.max_omega), abs(self.max_omega))
        self.omega += (target_omega - self.omega) * dt_f / tau_f
        self.theta = wrap_angle(self.theta + self.omega * dt_f)
        return self.theta, self.omega


@dataclass
class DifferentialDriveState:
    """Robot pose plus cumulative wheel travel in meters."""

    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0
    left_distance: float = 0.0
    right_distance: float = 0.0

    @property
    def pose(self) -> Pose:
        return self.x, self.y, self.theta


def integrate_diff_drive(
    state: DifferentialDriveState | Pose,
    left_delta: Number,
    right_delta: Number,
    wheel_base: Number,
) -> DifferentialDriveState:
    """Integrate differential-drive odometry from wheel distance increments."""
    if float(wheel_base) <= 0.0:
        raise ValueError("wheel_base must be positive")

    if isinstance(state, DifferentialDriveState):
        x, y, theta = state.x, state.y, state.theta
        left_total = state.left_distance + float(left_delta)
        right_total = state.right_distance + float(right_delta)
    else:
        x, y, theta = (float(state[0]), float(state[1]), float(state[2]))
        left_total = float(left_delta)
        right_total = float(right_delta)

    dl = float(left_delta)
    dr = float(right_delta)
    ds = 0.5 * (dl + dr)
    dtheta = (dr - dl) / float(wheel_base)

    if abs(dtheta) < 1e-9:
        x += ds * math.cos(theta)
        y += ds * math.sin(theta)
    else:
        radius = ds / dtheta
        new_theta = theta + dtheta
        x += radius * (math.sin(new_theta) - math.sin(theta))
        y += -radius * (math.cos(new_theta) - math.cos(theta))

    return DifferentialDriveState(
        x=x,
        y=y,
        theta=wrap_angle(theta + dtheta),
        left_distance=left_total,
        right_distance=right_total,
    )


def integrate_odometry_sequence(
    left_deltas: Sequence[Number],
    right_deltas: Sequence[Number],
    wheel_base: Number,
    initial: DifferentialDriveState | Pose | None = None,
) -> list[DifferentialDriveState]:
    """Return the odometry state after each pair of wheel distance increments."""
    if len(left_deltas) != len(right_deltas):
        raise ValueError("left_deltas and right_deltas must have the same length")
    state = (
        DifferentialDriveState()
        if initial is None
        else initial
        if isinstance(initial, DifferentialDriveState)
        else DifferentialDriveState(*initial)
    )
    states = [state]
    for dl, dr in zip(left_deltas, right_deltas):
        state = integrate_diff_drive(state, dl, dr, wheel_base)
        states.append(state)
    return states


def encoder_ticks_to_distance(
    ticks: Number,
    ticks_per_rev: Number,
    wheel_radius: Number,
    gear_ratio: Number = 1.0,
) -> float:
    """Convert encoder ticks to linear wheel travel in meters."""
    if float(ticks_per_rev) <= 0.0:
        raise ValueError("ticks_per_rev must be positive")
    if float(gear_ratio) <= 0.0:
        raise ValueError("gear_ratio must be positive")
    revolutions = float(ticks) / (float(ticks_per_rev) * float(gear_ratio))
    return revolutions * TAU * float(wheel_radius)


def unicycle_to_wheel_speeds(linear: Number, angular: Number, wheel_base: Number) -> tuple[float, float]:
    """Convert chassis linear/angular speed to left/right wheel linear speeds."""
    half = 0.5 * float(wheel_base)
    return float(linear) - half * float(angular), float(linear) + half * float(angular)


def wheel_speeds_to_unicycle(left: Number, right: Number, wheel_base: Number) -> tuple[float, float]:
    """Convert left/right wheel linear speeds to chassis linear/angular speed."""
    if float(wheel_base) <= 0.0:
        raise ValueError("wheel_base must be positive")
    linear = 0.5 * (float(left) + float(right))
    angular = (float(right) - float(left)) / float(wheel_base)
    return linear, angular


def simulate_pid_first_order(
    controller: PIDController,
    plant: FirstOrderPlant,
    duration: Number,
    dt: Number,
    setpoint: Profile,
) -> list[dict[str, float]]:
    """Simulate PID control of a first-order plant and return chart rows."""
    steps = _step_count(duration, dt)
    rows: list[dict[str, float]] = []
    for k in range(steps + 1):
        t = k * float(dt)
        target = _profile_value(setpoint, t)
        command = controller.update(plant.y, dt, target)
        measurement = plant.step(command, dt)
        sample = controller.snapshot(t, measurement)
        rows.append({**asdict(sample), "command": command})
    return rows


def simulate_heading_pid(
    controller: PIDController,
    plant: HeadingPlant,
    duration: Number,
    dt: Number,
    heading_setpoint: Profile,
) -> list[dict[str, float]]:
    """Simulate a heading PID loop using wrapped angular error."""
    steps = _step_count(duration, dt)
    rows: list[dict[str, float]] = []
    for k in range(steps + 1):
        t = k * float(dt)
        target = _profile_value(heading_setpoint, t)
        command = controller.update(plant.theta, dt, target, wrap_error=True)
        theta, omega = plant.step(command, dt)
        sample = controller.snapshot(t, theta)
        rows.append({**asdict(sample), "theta": theta, "omega": omega, "command": command})
    return rows


def _step_count(duration: Number, dt: Number) -> int:
    duration_f = float(duration)
    dt_f = float(dt)
    if duration_f < 0.0:
        raise ValueError("duration must be non-negative")
    if dt_f <= 0.0:
        raise ValueError("dt must be positive")
    return int(math.floor(duration_f / dt_f))


def point_distance(a: Point, b: Point) -> float:
    return math.hypot(float(b[0]) - float(a[0]), float(b[1]) - float(a[1]))


def heading_to(a: Point, b: Point) -> float:
    return math.atan2(float(b[1]) - float(a[1]), float(b[0]) - float(a[0]))


def path_length(points: Sequence[Point]) -> float:
    return sum(point_distance(a, b) for a, b in zip(points, points[1:]))


def cumulative_path_distances(points: Sequence[Point]) -> list[float]:
    totals = [0.0]
    for a, b in zip(points, points[1:]):
        totals.append(totals[-1] + point_distance(a, b))
    return totals


def nearest_waypoint(point: Point, waypoints: Sequence[Point]) -> tuple[int, float]:
    """Return ``(index, distance)`` for the waypoint nearest to ``point``."""
    if not waypoints:
        raise ValueError("waypoints cannot be empty")
    distances = [point_distance(point, wp) for wp in waypoints]
    index = min(range(len(distances)), key=distances.__getitem__)
    return index, distances[index]


def interpolate_path(points: Sequence[Point], spacing: Number) -> list[Point]:
    """Resample a polyline at approximately uniform point spacing."""
    if not points:
        return []
    spacing_f = float(spacing)
    if spacing_f <= 0.0:
        raise ValueError("spacing must be positive")
    if len(points) == 1:
        return [(float(points[0][0]), float(points[0][1]))]

    samples: list[Point] = [(float(points[0][0]), float(points[0][1]))]
    carry = spacing_f
    for start, end in zip(points, points[1:]):
        ax, ay = float(start[0]), float(start[1])
        bx, by = float(end[0]), float(end[1])
        seg_len = math.hypot(bx - ax, by - ay)
        if seg_len <= 1e-12:
            continue
        while carry <= seg_len:
            ratio = carry / seg_len
            samples.append((ax + ratio * (bx - ax), ay + ratio * (by - ay)))
            carry += spacing_f
        carry -= seg_len
    if point_distance(samples[-1], points[-1]) > 1e-9:
        samples.append((float(points[-1][0]), float(points[-1][1])))
    return samples


def lookahead_point(
    pose: Pose,
    path: Sequence[Point],
    lookahead: Number,
) -> tuple[int, Point]:
    """Pick the first path point at least ``lookahead`` meters from ``pose``."""
    if not path:
        raise ValueError("path cannot be empty")
    nearest_idx, _ = nearest_waypoint((pose[0], pose[1]), path)
    lookahead_f = max(0.0, float(lookahead))
    for i in range(nearest_idx, len(path)):
        if point_distance((pose[0], pose[1]), path[i]) >= lookahead_f:
            return i, (float(path[i][0]), float(path[i][1]))
    return len(path) - 1, (float(path[-1][0]), float(path[-1][1]))


def pure_pursuit_command(
    pose: Pose,
    path: Sequence[Point],
    lookahead: Number,
    speed: Number,
    wheel_base: Number | None = None,
) -> dict[str, float]:
    """Return a simple pure-pursuit command toward a lookahead point.

    The dictionary always includes ``linear`` and ``angular``.  When
    ``wheel_base`` is provided it also includes ``left_speed`` and
    ``right_speed``.
    """
    _, target = lookahead_point(pose, path, lookahead)
    dx = target[0] - float(pose[0])
    dy = target[1] - float(pose[1])
    heading = float(pose[2])
    local_x = math.cos(heading) * dx + math.sin(heading) * dy
    local_y = -math.sin(heading) * dx + math.cos(heading) * dy
    distance_sq = max(1e-9, local_x * local_x + local_y * local_y)
    curvature = 2.0 * local_y / distance_sq
    linear = float(speed)
    angular = linear * curvature
    command = {"linear": linear, "angular": angular, "curvature": curvature}
    if wheel_base is not None:
        left, right = unicycle_to_wheel_speeds(linear, angular, wheel_base)
        command.update({"left_speed": left, "right_speed": right})
    return command


def mean_absolute_error(values: Sequence[Number], targets: Sequence[Number] | Number = 0.0) -> float:
    errors = _pairwise_errors(values, targets)
    return sum(abs(e) for e in errors) / len(errors) if errors else 0.0


def root_mean_square_error(values: Sequence[Number], targets: Sequence[Number] | Number = 0.0) -> float:
    errors = _pairwise_errors(values, targets)
    return math.sqrt(sum(e * e for e in errors) / len(errors)) if errors else 0.0


def max_abs_error(values: Sequence[Number], targets: Sequence[Number] | Number = 0.0) -> float:
    errors = _pairwise_errors(values, targets)
    return max((abs(e) for e in errors), default=0.0)


def settling_time(
    times: Sequence[Number],
    values: Sequence[Number],
    target: Number,
    tolerance: Number,
) -> float | None:
    """Return the first time after which all values stay within tolerance."""
    if len(times) != len(values):
        raise ValueError("times and values must have the same length")
    tol = abs(float(tolerance))
    target_f = float(target)
    for i, t in enumerate(times):
        if all(abs(float(v) - target_f) <= tol for v in values[i:]):
            return float(t)
    return None


def path_tracking_error(poses: Sequence[Pose], path: Sequence[Point]) -> dict[str, float]:
    """Compute nearest-path distance metrics for a sequence of poses."""
    if not poses:
        return {"mean": 0.0, "rmse": 0.0, "max": 0.0}
    if not path:
        raise ValueError("path cannot be empty")
    distances = [
        nearest_waypoint((float(pose[0]), float(pose[1])), path)[1]
        for pose in poses
    ]
    return {
        "mean": mean_absolute_error(distances),
        "rmse": root_mean_square_error(distances),
        "max": max_abs_error(distances),
    }


def rows_to_columns(rows: Sequence[dict[str, float]]) -> dict[str, list[float]]:
    """Convert list-of-dicts simulation rows into column lists for plotting."""
    columns: dict[str, list[float]] = {}
    for row in rows:
        for key, value in row.items():
            columns.setdefault(key, []).append(float(value))
    return columns


def maybe_numpy_array(rows: Sequence[dict[str, float]], columns: Sequence[str] | None = None):
    """Return a NumPy array when NumPy is installed, otherwise list rows.

    This keeps Streamlit demos convenient without making NumPy mandatory.
    """
    if columns is None:
        columns = list(rows[0].keys()) if rows else []
    matrix = [[float(row[name]) for name in columns] for row in rows]
    if _np is None:
        return matrix
    return _np.array(matrix, dtype=float)


def _pairwise_errors(values: Sequence[Number], targets: Sequence[Number] | Number) -> list[float]:
    if isinstance(targets, (int, float)):
        target_list = [float(targets)] * len(values)
    else:
        if len(values) != len(targets):
            raise ValueError("values and targets must have the same length")
        target_list = [float(target) for target in targets]
    return [float(value) - target for value, target in zip(values, target_list)]


__all__ = [
    "DifferentialDriveState",
    "FirstOrderPlant",
    "HeadingPlant",
    "PIDController",
    "PIDStep",
    "angle_error",
    "clamp",
    "cumulative_path_distances",
    "encoder_ticks_to_distance",
    "heading_to",
    "integrate_diff_drive",
    "integrate_odometry_sequence",
    "interpolate_path",
    "lookahead_point",
    "max_abs_error",
    "maybe_numpy_array",
    "mean_absolute_error",
    "nearest_waypoint",
    "path_length",
    "path_tracking_error",
    "point_distance",
    "pure_pursuit_command",
    "root_mean_square_error",
    "rows_to_columns",
    "settling_time",
    "simulate_heading_pid",
    "simulate_pid_first_order",
    "unicycle_to_wheel_speeds",
    "wheel_speeds_to_unicycle",
    "wrap_angle",
]
