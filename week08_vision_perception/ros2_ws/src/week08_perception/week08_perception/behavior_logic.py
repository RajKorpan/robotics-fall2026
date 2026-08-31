from dataclasses import dataclass
@dataclass(frozen=True)
class Config: min_confidence:float=.6; center_deadband:float=.1; stop_area:float=.22; stale_after:float=.6; search_angular:float=.25; approach_linear:float=.1; center_gain:float=.7
def decide(obs,age,cfg):
    if obs is None or age>cfg.stale_after:return "STOP",0.,0.
    if not obs["detected"] or obs["confidence"]<cfg.min_confidence:return "SEARCH",0.,cfg.search_angular
    if obs["area_fraction"]>=cfg.stop_area:return "STOP",0.,0.
    if abs(obs["center_offset"])>cfg.center_deadband:return "CENTER",0.,max(-.6,min(.6,-cfg.center_gain*obs["center_offset"]))
    return "APPROACH",cfg.approach_linear,0.
