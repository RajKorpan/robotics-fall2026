from __future__ import annotations


def feedback_figure(trace: dict[str, list[float]]):
    import matplotlib.pyplot as plt

    figure, axis = plt.subplots(figsize=(8, 3.6))
    axis.plot(trace["time"], trace["position"], label="Position", linewidth=2)
    axis.plot(trace["time"], trace["target"], "--", label="Target")
    axis.set(xlabel="Time (s)", ylabel="Position", title="System response")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    return figure

