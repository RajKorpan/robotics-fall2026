from dataclasses import asdict,dataclass,field
from typing import Any,Callable


@dataclass
class RequirementResult: id:str; label:str; passed:bool; actual:Any; expected:str
@dataclass
class MissionCheck: passed:bool; summary:str; requirements:list[RequirementResult]
@dataclass
class RunResult:
    run_id:str; mission_id:str; timestamp:str; settings:dict[str,Any]; metrics:dict[str,Any]; traces:dict[str,list[Any]]; simulation_version:str="1.0"; artifacts:dict[str,bytes]=field(default_factory=dict,repr=False)
    def serializable(self): data=asdict(self); data.pop("artifacts",None); return data
@dataclass(frozen=True)
class ReflectionPrompt: id:str; label:str; help:str=""
@dataclass(frozen=True)
class MissionDefinition: id:str; title:str; objective:str; render_controls:Callable; run:Callable; evaluate:Callable; reflection_prompts:tuple[ReflectionPrompt,...]

