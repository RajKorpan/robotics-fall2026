from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lab.autosave import submission_root
from lab_config import LAB


ROOT = Path(__file__).resolve().parents[1]


def save_mission(mission_id: str, evidence: dict[str, Any], responses: dict[str, Any]) -> Path:
    target = submission_root() / mission_id
    target.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "lab_id": LAB.id,
        "mission_id": mission_id,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "evidence": evidence,
    }
    (target / "submission.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (target / "latest_run.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    prefix = f"{mission_id}."
    answers = {key[len(prefix):]: value for key, value in responses.items() if key.startswith(prefix)}
    lines = [f"# {mission_id.replace('_', ' ').title()}", ""]
    for key, value in answers.items():
        lines.extend([f"## {key.replace('_', ' ').title()}", "", str(value), ""])
    (target / "explanation.md").write_text("\n".join(lines), encoding="utf-8")
    if mission_id == "mission_1":
        _write_ros_system_diagram(target, responses, evidence.get("graph", {}))
    return target


def _write_ros_system_diagram(
    target: Path,
    responses: dict[str, Any],
    graph: dict[str, Any] | None = None,
) -> Path:
    target.mkdir(parents=True, exist_ok=True)
    graph = graph or {}
    guided_checks = responses.get("mission_1.guided_checks", {})
    trace_topics = {"/scan", "/odom", "/student_cmd_vel", "/cmd_vel", "/tf"}
    topics = [
        item for item in graph.get("topics", [])
        if isinstance(item, dict) and item.get("name") in trace_topics
    ]
    node_names = {
        "/course_cmd_vel_guard",
        "/course_evidence_collector",
        "/ros_gz_bridge",
        "/rviz2",
    }
    for topic in topics:
        node_names.update(str(value) for value in topic.get("publishers", []))
        node_names.update(str(value) for value in topic.get("subscribers", []))
    node_ids = {name: f"n{index}" for index, name in enumerate(sorted(node_names))}
    lines = [
        "# Observed ROS 2 system diagram",
        "",
        "```mermaid",
        "flowchart LR",
    ]
    for name, node_id in node_ids.items():
        lines.append(f'  {node_id}["{name}"]')
    for index, topic in enumerate(topics):
        topic_id = f"t{index}"
        topic_name = str(topic.get("name", ""))
        topic_type = ", ".join(str(value).split("/")[-1] for value in topic.get("types", []))
        lines.append(f'  {topic_id}(["{topic_name}<br/>{topic_type}"])')
        for publisher in topic.get("publishers", []):
            if str(publisher) in node_ids:
                lines.append(f"  {node_ids[str(publisher)]} -->|publishes| {topic_id}")
        for subscriber in topic.get("subscribers", []):
            if str(subscriber) in node_ids:
                lines.append(f"  {topic_id} -->|subscribes| {node_ids[str(subscriber)]}")
    lines.extend([
        "```",
        "",
        "This diagram is generated from the captured publisher and subscriber endpoints. A missing arrow records a missing live endpoint, not an assumed connection.",
        "",
        "## Guided terminal observations",
        "",
        "| Observation | Completed |",
        "|---|---|",
    ])
    labels = {
        "node_list": "Listed the running nodes",
        "guard_info": "Inspected the command guard",
        "bridge_info": "Inspected the simulator bridge",
        "scan_info": "Inspected the scan connections",
        "scan_message": "Viewed one scan message",
        "command_topics": "Compared proposed and approved command topics",
    }
    for key, label in labels.items():
        lines.append(f"| {label} | {'Yes' if guided_checks.get(key) else 'No'} |")
    lines.append("")
    path = target / "ros_system_diagram.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_foundations_summary(st) -> Path:
    responses = dict(st.session_state.get("responses", {}))
    lines = [
        "# Week 1 guided tutorial activity record",
        "",
        "Parts 1–3 were ungraded, teaching-first demonstrations completed before the live ROS missions.",
        "",
    ]
    activities = {
        "part_1.activity": "Part 1 — Why robotics software is difficult",
        "part_2.activity": "Part 2 — Robot software architectures",
        "part_3.activity": "Part 3 — What ROS 2 provides",
    }
    for key, heading in activities.items():
        lines.extend([f"## {heading}", ""])
        value = responses.get(key, {})
        lines.extend(["```json", json.dumps(value, indent=2, sort_keys=True), "```", ""])
    path = submission_root() / "foundations.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def snapshot_student_source() -> Path:
    source = ROOT / "ros2_ws" / "src" / "week01_behavior"
    target = submission_root() / "mission_3" / "source"
    target.mkdir(parents=True, exist_ok=True)
    for relative in (
        "package.xml",
        "setup.py",
        "setup.cfg",
        "week01_behavior/decision.py",
        "week01_behavior/obstacle_guard.py",
        "test/test_decision.py",
        "test/test_student_decision.py",
    ):
        source_file = source / relative
        if source_file.exists():
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, destination)
    return target


def write_manifest(st) -> Path:
    root = submission_root()
    root.mkdir(parents=True, exist_ok=True)
    files = sorted(
        str(path.relative_to(root)).replace("\\", "/")
        for path in root.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    )
    payload = {
        "schema_version": 1,
        "lab_id": LAB.id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "student": {
            key: str(dict(st.session_state.get("student", {})).get(key, ""))
            for key in ("name", "email")
        },
        "completed_missions": list(st.session_state.get("completed_missions", [])),
        "checked_evidence_ids": dict(st.session_state.get("checked_evidence_ids", {})),
        "files": files,
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
