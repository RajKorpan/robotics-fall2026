from __future__ import annotations

import math


def simulate_feedback(
    *,
    gain: float,
    target: float,
    disturbance: float = 0.0,
    sensor_noise: float = 0.0,
    duration: float = 8.0,
    dt: float = 0.05,
) -> dict[str, list[float]]:
    """Small deterministic plant used only to demonstrate the template contract."""
    position = 0.0
    velocity = 0.0
    trace = {"time": [], "position": [], "target": [], "command": [], "error": []}
    for step in range(round(duration / dt) + 1):
        time = step * dt
        noise = sensor_noise * math.sin(step * 1.73)
        measured_position = position + noise
        error = target - measured_position
        command = max(-4.0, min(4.0, gain * error))
        acceleration = command + disturbance - 0.9 * velocity
        velocity += acceleration * dt
        position += velocity * dt
        trace["time"].append(round(time, 4))
        trace["position"].append(position)
        trace["target"].append(target)
        trace["command"].append(command)
        trace["error"].append(target - position)
    return trace

