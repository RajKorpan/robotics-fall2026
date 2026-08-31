from lab.models import RunResult
from simulation.common import identity


def run_policy(settings):
    scenarios=[
      ("person_nearby",settings["max_speed_near_people"]<=.20,"speed limit near a person"),
      ("personal_space",settings["personal_space_m"]>=.80,"minimum personal-space distance"),
      ("low_confidence",settings["confidence_threshold"]>=.75 and settings["fallback"]=="stop and request help","uncertain perception stops safely"),
      ("emergency_stop",settings["emergency_stop"],"independent emergency stop"),
      ("consequential_action",settings["confirm_consequential"],"human confirmation before consequence"),
      ("hearing_access",settings["visual_feedback"] and settings["text_controls"],"essential state/control does not depend on sound"),
      ("vision_access",settings["audio_feedback"] and settings["physical_stop"],"essential state/control does not depend on vision"),
      ("network_loss",settings["local_fallback"] and settings["fallback"]=="stop and request help","network loss has local safe fallback"),
    ]; metrics={"scenarios_passed":sum(x[1] for x in scenarios),"scenarios_total":len(scenarios),"accessible_modalities":sum(bool(settings[k]) for k in ("visual_feedback","audio_feedback","text_controls","physical_stop")),"unsafe_scenarios":sum(not x[1] for x in scenarios)}; traces={"scenario":[x[0] for x in scenarios],"passed":[x[1] for x in scenarios],"criterion":[x[2] for x in scenarios]}; run_id,timestamp=identity("mission_3",settings); return RunResult(run_id,"mission_3",timestamp,settings,metrics,traces)
