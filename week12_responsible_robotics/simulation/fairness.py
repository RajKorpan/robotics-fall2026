from collections import defaultdict
from lab.models import RunResult
from simulation.common import identity

BASE={
 "well_lit":{"positive":[.90,.80,.70,.60],"negative":[.40,.30,.20,.10]},
 "low_light":{"positive":[.68,.58,.48,.38],"negative":[.52,.42,.32,.22]},
 "darker_scene":{"positive":[.65,.55,.45,.35],"negative":[.55,.45,.35,.25]},
 "mobility_aid_present":{"positive":[.72,.62,.52,.42],"negative":[.48,.38,.28,.18]},
}


def run_fairness(settings):
    threshold=float(settings["threshold"]); margin=float(settings["abstain_margin"]); intervention=settings["intervention"]; rows=[]
    for group,labels in BASE.items():
        disadvantaged=group!="well_lit"
        for truth_name,scores in labels.items():
            truth=truth_name=="positive"
            for index,base in enumerate(scores):
                score=base
                if intervention=="alternate sensor" and disadvantaged: score+=.15 if truth else -.05
                elif intervention=="additional calibration data" and disadvantaged: score+=.08 if truth else -.03
                score=max(0,min(1,score)); abstained=abs(score-threshold)<=margin; reviewed=abstained and settings["human_review"]; decision=truth if reviewed else score>=threshold
                rows.append({"group":group,"sample":f"{group}_{truth_name}_{index}","truth":truth,"score":round(score,2),"abstained":abstained,"reviewed":reviewed,"decision":decision,"correct":decision==truth})
    group_metrics={}
    for group in BASE:
        values=[r for r in rows if r["group"]==group]; pos=[r for r in values if r["truth"]]; neg=[r for r in values if not r["truth"]]; auto=[r for r in values if not r["abstained"]]
        group_metrics[group]={"tpr":sum(r["decision"] for r in pos)/len(pos),"fpr":sum(r["decision"] for r in neg)/len(neg),"accuracy":sum(r["correct"] for r in values)/len(values),"automated_coverage":len(auto)/len(values)}
    baseline_groups={}
    for group,labels in BASE.items():
        positives=labels["positive"]; negatives=labels["negative"]; baseline_groups[group]={"tpr":sum(s>=threshold for s in positives)/len(positives),"fpr":sum(s>=threshold for s in negatives)/len(negatives)}
    baseline_tprs=[m["tpr"] for m in baseline_groups.values()]; tprs=[m["tpr"] for m in group_metrics.values()]; metrics={"samples":len(rows),"tpr_gap":round(max(tprs)-min(tprs),3),"worst_group_tpr":round(min(tprs),3),"worst_group_fpr":round(max(m["fpr"] for m in group_metrics.values()),3),"minimum_automated_coverage":round(min(m["automated_coverage"] for m in group_metrics.values()),3),"review_rate":round(sum(r["reviewed"] for r in rows)/len(rows),3),"overall_accuracy":round(sum(r["correct"] for r in rows)/len(rows),3),"groups":group_metrics,"baseline_without_intervention":{"tpr_gap":round(max(baseline_tprs)-min(baseline_tprs),3),"worst_group_tpr":round(min(baseline_tprs),3),"worst_group_fpr":round(max(m["fpr"] for m in baseline_groups.values()),3),"groups":baseline_groups}}
    traces={key:[r[key] for r in rows] for key in ("group","sample","truth","score","abstained","reviewed","decision","correct")}; run_id,timestamp=identity("mission_2",settings); return RunResult(run_id,"mission_2",timestamp,settings,metrics,traces)
