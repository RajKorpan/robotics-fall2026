from dataclasses import dataclass
from typing import Any
from evaluation.metrics import matched_comparison, summarize


@dataclass(frozen=True)
class Requirement:
    label: str; passed: bool; actual: Any; expected: str


def prototype_requirements(evidence):
    states = set(evidence.get("observed_states", [])); required = {"IDLE", "ANNOUNCE", "APPROACH", "LISTENING", "CONFIRMING", "ACTING", "COMPLETE", "ERROR"}
    return (
        Requirement("Complete interaction state coverage", required <= states, sorted(states), str(sorted(required))),
        Requirement("Motion disabled for peer test", evidence.get("motion_enabled") is False, evidence.get("motion_enabled"), "false"),
        Requirement("Emergency stop tested", evidence.get("stop_tested") is True, evidence.get("stop_tested"), "true"),
        Requirement("At least two dry runs", int(evidence.get("dry_runs", 0)) >= 2, evidence.get("dry_runs", 0), ">= 2"),
    )


def baseline_requirements(evidence):
    m = summarize(evidence)
    return (
        Requirement("Voluntary consent recorded", evidence.get("consent_confirmed") is True, evidence.get("consent_confirmed"), "true"),
        Requirement("No audio/video/photo recording", evidence.get("recording_used") is False, evidence.get("recording_used"), "false"),
        Requirement("Random non-identifying code", str(evidence.get("participant_code", "")).startswith("P-") and len(str(evidence.get("participant_code", ""))) >= 6, evidence.get("participant_code"), "P- plus random characters"),
        Requirement("All five scenarios", m["scenario_coverage"] == 5 and m["valid_trials"] == 5, (m["scenario_coverage"], m["valid_trials"]), "5 covered and valid"),
        Requirement("No safety-stop event", m["safety_stops"] == 0, m["safety_stops"], "0"),
    )


def redesign_requirements(evidence):
    baseline, redesign = evidence.get("baseline", {}), evidence.get("redesign", {}); comparison = matched_comparison(baseline, redesign); b, r = comparison["baseline"], comparison["redesign"]
    return (
        Requirement("Matched participant and scenarios", comparison["participant_match"] and comparison["matched_scenarios"] == 5, (comparison["participant_match"], comparison["matched_scenarios"]), "same code and 5 matched scenarios"),
        Requirement("At least two implemented changes", len(evidence.get("design_changes", [])) >= 2, len(evidence.get("design_changes", [])), ">= 2"),
        Requirement("No regression in success", r["task_success_rate"] >= b["task_success_rate"], (b["task_success_rate"], r["task_success_rate"]), "redesign >= baseline"),
        Requirement("At least two target metrics improve", len(comparison["improved_metrics"]) >= 2, comparison["improved_metrics"], ">= 2"),
        Requirement("No access barriers in retest", r["access_barriers"] == 0, r["access_barriers"], "0"),
        Requirement("No safety-stop event", r["safety_stops"] == 0, r["safety_stops"], "0"),
    )
