from pathlib import Path
import importlib.util
import tempfile

from lab.evidence import ROOT, root
from lab.navigation import bottom_nav, unlocked
from lab.local_jobs import installed, setup_status, start_job, job_status, cancel_job
from lab.local_config import MODEL_CONFIG, scene_path


def check_environment():
    rows = []
    for name in ("streamlit", "pandas"):
        rows.append({"Check": name, "Ready": importlib.util.find_spec(name) is not None, "Detail": "Required Python package"})
    for name in ("cup_reattempt.mp4",):
        path = ROOT / "assets" / "policy_recordings" / name
        rows.append({"Check": name, "Ready": path.is_file() and path.stat().st_size > 1000, "Detail": "Bundled recorded OpenVLA demonstration"})
    rows.append({"Check": "Guided speech example", "Ready": (ROOT / "assets" / "guided" / "stop_robot.wav").is_file(), "Detail": "Bundled audio input example"})
    rows.append({"Check": "Local model files", "Ready": installed(), "Detail": "Two pinned model checkpoints and isolated CPU runtime"})
    rows.append({"Check": "Workbench photograph", "Ready": scene_path().is_file(), "Detail": "Bundled multi-object workbench image"})
    from simulation.robot_room import route, START, GOAL
    rows.append({"Check": "Maze simulator", "Ready": len(route(START, GOAL)) > 20, "Detail": "Two-wall detour from start to goal"})
    try:
        root().mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=root()) as stream:
            stream.write(b"save check")
        writable = True
        detail = str(root())
    except OSError as error:
        writable, detail = False, str(error)
    rows.append({"Check": "Evidence saving", "Ready": writable, "Detail": detail})
    return rows


def render(st):
    st.title("Preflight: check the experiment environment")
    st.write("This lab generates answers and robot proposals using two small models on your computer. Prepare the models once, then run preflight to check that both can generate an answer and your work can be saved.")
    st.write("**First use:** select Prepare local models. Keep this page open while the CPU software and model files download. This step needs internet access. Later experiments use the downloaded files locally. Model setup may need to be repeated if the course container is replaced.")
    setup = setup_status()
    if st.button("Prepare local models", disabled=setup["running"]):
        setup_status(start=True)
        st.rerun()
    if setup["running"]:
        @st.fragment(run_every=2)
        def setup_progress():
            progress = setup_status()
            st.info("Preparing local models. Download and installation progress appears below.")
            st.code(progress["log"][-4500:], language="text")
            if not progress["running"]:
                st.rerun()
        setup_progress()
    elif setup["exit_code"] not in (None, 0):
        st.error("Model setup failed. Check the last lines below, then retry. Your work is retained.")
        st.code(setup["log"], language="text")
    elif installed():
        st.success("Both local model checkpoints are available.")
    st.write("Select Run preflight. The first generation can take longer while weights load. If a bundled file is missing, update your course checkout. If saving fails, use a folder you can write to.")
    if st.button("Run preflight", type="primary"):
        st.session_state["preflight"] = check_environment()
        if installed():
            st.session_state["model_probes"] = {kind: start_job(kind, "clear" if kind == "language" else "identify", "Say ready." if kind == "language" else "Name one visible object.", "preflight") for kind in MODEL_CONFIG}
            st.session_state["preflight"].extend({"Check": kind + " model generates locally", "Ready": False, "Detail": "Generating a test answer"} for kind in MODEL_CONFIG)
        st.rerun()
    probes = st.session_state.get("model_probes", {})
    if probes:
        @st.fragment(run_every=1)
        def probe_progress():
            pending = False
            changed = False
            for kind, job_id in probes.items():
                result = job_status(kind, job_id)
                passed = result.get("status") == "complete" and bool(result.get("record", {}).get("output"))
                pending = pending or result.get("status") in ("queued", "loading", "generating")
                detail = "Generated: " + result["record"]["output"][:130] if passed else result.get("error", result.get("status", "Waiting") + f" ({result.get('elapsed', 0):.0f} s elapsed, {result.get('tokens', 0)} tokens)")
                for row in st.session_state["preflight"]:
                    if row["Check"] == kind + " model generates locally":
                        changed = changed or row["Ready"] != passed
                        row.update({"Ready": passed, "Detail": detail})
                st.write(kind.title() + ": " + detail)
            if pending:
                if st.button("Stop preflight generation"):
                    for kind, job_id in probes.items():
                        cancel_job(kind, job_id)
                    st.rerun()
            elif not st.session_state.get("model_probes_displayed") or changed:
                st.session_state["model_probes_displayed"] = True
                st.rerun()
        probe_progress()
    rows = st.session_state.get("preflight", [])
    if rows:
        st.dataframe(rows, hide_index=True)
    resume = st.session_state.get("resume_after_preflight")
    destination = resume if resume and unlocked(st.session_state, resume) else "guided"
    if resume:
        st.info("Your saved answers and evidence are retained. Run this fresh environment check before resuming. If saved work was edited, return to the earliest mission needing Check and save.")
    bottom_nav(st, "intro", destination, next_disabled=not rows or not all(r["Ready"] for r in rows))
