from lab.models import RunResult
from simulation.common import identity


def run_privacy(settings):
    checks=[
        ("purpose_minimization","Collect event features rather than identifiable raw video",settings["data_collected"]=="event features only"),
        ("local_processing","Raw sensor processing stays on robot",settings["processing"]=="local"),
        ("raw_storage","Raw video is not stored",not settings["store_raw_video"]),
        ("retention","Event retention is no more than 24 hours",settings["retention_hours"]<=24),
        ("consent","Assistance mode uses just-in-time opt-in",settings["consent"]=="just-in-time opt-in"),
        ("deletion","User-accessible deletion is enabled",settings["deletion_enabled"]),
        ("anonymization","Identifiers are removed from event logs",settings["anonymize_logs"]),
        ("access","Logs use role-based access",settings["role_based_access"]),
    ]
    utility={"continuous video":.94,"cropped person images":.90,"event features only":.84,"no sensing":.20}[settings["data_collected"]]
    risk=10; risk-=2*(settings["processing"]=="local"); risk-=2*(not settings["store_raw_video"]); risk-=1*(settings["retention_hours"]<=24); risk-=1*(settings["consent"]=="just-in-time opt-in"); risk-=1*settings["deletion_enabled"]; risk-=1*settings["anonymize_logs"]; risk-=1*settings["role_based_access"]; risk=max(0,risk)
    metrics={"requirements_passed":sum(row[2] for row in checks),"requirements_total":len(checks),"task_utility":utility,"privacy_risk_score":risk,"raw_video_stored":settings["store_raw_video"],"retention_hours":settings["retention_hours"]}
    traces={"requirement_id":[r[0] for r in checks],"requirement":[r[1] for r in checks],"passed":[r[2] for r in checks]}; run_id,timestamp=identity("mission_1",settings); return RunResult(run_id,"mission_1",timestamp,settings,metrics,traces)

