from __future__ import annotations
import json, os, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def succeeds(*command):
    try: return subprocess.run(command, capture_output=True, text=True, timeout=20).returncode == 0
    except (OSError, subprocess.TimeoutExpired): return False
def main():
    output = ROOT / "runtime" / "evidence"; output.mkdir(parents=True, exist_ok=True)
    checks = [{"check": "ROS distribution", "passed": os.environ.get("ROS_DISTRO") == "jazzy", "detail": os.environ.get("ROS_DISTRO", "not sourced")}, {"check": "ros2 command", "passed": shutil.which("ros2") is not None, "detail": shutil.which("ros2") or "missing"}, {"check": "ROS_DOMAIN_ID", "passed": os.environ.get("ROS_DOMAIN_ID", "").isdigit(), "detail": os.environ.get("ROS_DOMAIN_ID", "not set")}]
    for package in ("cv_bridge", "image_view", "image_publisher", "week08_interfaces", "week08_perception", "course_cmd_vel_guard"):
        checks.append({"check": f"Package: {package}", "passed": succeeds("ros2", "pkg", "prefix", package), "detail": package})
    model = ROOT / "assets" / "models" / "detector.onnx"; labels = ROOT / "assets" / "models" / "labels.txt"; checks.append({"check": "Frozen learned model", "passed": model.exists(), "detail": str(model) if model.exists() else "instructor must install detector.onnx"}); checks.append({"check": "Frozen class labels", "passed": labels.exists(), "detail": str(labels) if labels.exists() else "labels.txt missing"})
    payload = {"schema_version": 1, "captured_at": datetime.now(timezone.utc).isoformat(), "checks": checks, "ready": all(item["passed"] for item in checks)}; (output / "preflight.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for item in checks: print(f"{item['check']:<34} {'PASS' if item['passed'] else 'FAIL':<5} {item['detail']}")
    raise SystemExit(0 if payload["ready"] else 1)
if __name__ == "__main__": main()
