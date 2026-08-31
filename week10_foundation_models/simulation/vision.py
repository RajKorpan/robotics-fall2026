from html import escape
from lab.models import RunResult
from simulation.common import run_identity
from simulation.scenarios import load_bank


def scene_svg(case):
    colors = {"clear":"#e8f5ff", "low light":"#4a5260", "occlusion":"#eee7dc", "partial view":"#edf0f4", "unusual object":"#fff4d6", "misleading context":"#e8f7e8", "ambiguity":"#f4e8ff", "severe occlusion":"#c8c8c8"}
    bg = colors[case["condition"]]; label = escape(case["id"].replace("_", " ").title()); note = escape(case["note"])
    mug = '<path d="M205 90 L305 90 L295 185 L215 185 Z" fill="#3b82f6" stroke="#172554" stroke-width="5"/><path d="M302 110 C365 100 365 165 300 158" fill="none" stroke="#172554" stroke-width="14"/>'
    if case["id"] in ("clear_mug", "dim_mug"): subject = mug
    elif case["id"] == "occluded_mug": subject = mug + '<rect x="265" y="72" width="118" height="125" fill="#795548"/><text x="287" y="140" fill="white">box</text>'
    elif case["id"] == "empty_chair": subject = '<rect x="205" y="82" width="110" height="85" rx="8" fill="#966f4a"/><path d="M220 160 L205 205 M300 160 L315 205" stroke="#4b3425" stroke-width="12"/><path d="M218 70 Q260 42 304 76 L290 145 L230 140 Z" fill="#374151"/>'
    elif case["id"] == "unusual_tool": subject = '<path d="M180 170 L300 72 M220 188 L315 80" stroke="#64748b" stroke-width="16"/><circle cx="205" cy="181" r="28" fill="none" stroke="#334155" stroke-width="10"/><path d="M300 72 l42 -18 M315 80 l42 8" stroke="#334155" stroke-width="12"/>'
    elif case["id"] == "clear_exit": subject = '<rect x="200" y="60" width="125" height="145" fill="#8b5e3c" stroke="#3f2d20" stroke-width="6"/><circle cx="300" cy="138" r="7" fill="#f5d76e"/><rect x="338" y="50" width="130" height="54" fill="#15803d"/><text x="365" y="84" fill="white" font-size="21">EXIT →</text>'
    elif case["id"] == "two_bottles": subject = '<rect x="190" y="105" width="55" height="90" rx="12" fill="#f8fafc" stroke="#64748b" stroke-width="5"/><rect x="205" y="78" width="25" height="30" fill="#94a3b8"/><rect x="285" y="105" width="55" height="90" rx="12" fill="#f8fafc" stroke="#64748b" stroke-width="5"/><rect x="300" y="78" width="25" height="30" fill="#94a3b8"/>'
    else: subject = '<path d="M155 70 L375 70 L345 195 L175 195 Z" fill="#6b7280"/><text x="210" y="140" fill="white" font-size="20">covered</text>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="520" height="260" viewBox="0 0 520 260"><rect width="520" height="260" fill="{bg}"/><rect x="35" y="205" width="450" height="12" fill="#78828c"/>{subject}<text x="24" y="32" font-family="sans-serif" font-size="20" fill="#111">{label}</text><text x="24" y="242" font-family="sans-serif" font-size="14" fill="#111">{note}</text></svg>'''.encode()


def run_vision_suite(settings):
    threshold = float(settings["confidence_threshold"]); rows = []
    for case in load_bank("vision_scenes.json"):
        accepted = case["confidence"] >= threshold and case["model_label"] != "none"; correct = case["model_label"] == case["ground_truth"] or (case["ground_truth"] == "unknown_object" and not accepted)
        unsafe_accepted = accepted and not case["safe"]
        rows.append({**case, "accepted": accepted, "correct": correct, "unsafe_accepted": unsafe_accepted})
    run_id, timestamp = run_identity("mission_2", settings)
    errors = [r for r in rows if not r["correct"]]; accepted = [r for r in rows if r["accepted"]]
    metrics = {"scenes_tested": len(rows), "accepted_detections": len(accepted), "errors_observed": len(errors), "unsafe_recommendations_accepted": sum(r["unsafe_accepted"] for r in rows), "mean_confidence_correct": round(sum(r["confidence"] for r in rows if r["correct"]) / max(1, sum(r["correct"] for r in rows)), 3), "mean_confidence_incorrect": round(sum(r["confidence"] for r in errors) / max(1, len(errors)), 3)}
    traces = {k: [r[k] for r in rows] for k in ("id", "condition", "ground_truth", "model_label", "confidence", "recommendation", "accepted", "correct", "unsafe_accepted")}
    artifacts = {f"{r['id']}.svg": scene_svg(r) for r in rows}
    return RunResult(run_id, "mission_2", timestamp, settings, metrics, traces, artifacts=artifacts)
