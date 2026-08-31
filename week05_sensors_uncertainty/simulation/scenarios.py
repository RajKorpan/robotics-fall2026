from __future__ import annotations
import random
from simulation.filters import apply_filter,fuse,error_metrics
from simulation.sensors import SensorConfig,measure

DT=0.05
def dynamic_truth(count=400):
    values=[]
    for i in range(count):
        t=i*DT
        if t<6: value=2.8
        elif t<10: value=1.15
        elif t<15: value=1.15+0.22*(t-10)
        else: value=2.25+0.08*(t-15)
        values.append(value)
    return values
def fusion_dataset(seed:int):
    truth=dynamic_truth(); rng_a=random.Random(seed); rng_b=random.Random(seed+991)
    a_cfg=SensorConfig(noise_std=0.18,resolution=0.01,dropout_rate=0.025,outlier_rate=0.07,outlier_scale=1.2)
    b_cfg=SensorConfig(noise_std=0.07,bias=0.06,resolution=0.02,dropout_rate=0.03,outlier_rate=0.01,update_stride=4)
    a=[measure(value,a_cfg,rng_a,i) for i,value in enumerate(truth)]; b=[measure(value,b_cfg,rng_b,i) for i,value in enumerate(truth)]
    return {"time":[i*DT for i in range(len(truth))],"truth":truth,"sensor_a":a,"sensor_b":b}
def run_pipeline(dataset,method,window,alpha,weight_a):
    a=apply_filter(dataset["sensor_a"],method,window,alpha); b=apply_filter(dataset["sensor_b"],"Exponential",5,0.35); estimate=fuse(a,b,weight_a); metrics=error_metrics(dataset["truth"],estimate,DT,120)
    return {"estimate":estimate,"filtered_a":a,"filtered_b":b,"metrics":metrics,"settings":{"method":method,"window":window,"alpha":alpha,"weight_a":weight_a}}

DECISION_SCENARIOS={
    "clearly_safe":[2.5]*80,
    "stationary_danger":[0.55]*80,
    "near_threshold":[0.92+0.05*((i%10)-5)/5 for i in range(80)],
    "fast_approach":[max(0.35,2.8-0.04*i) for i in range(80)],
    "receding":[0.55+0.025*i for i in range(80)],
    "conflicting_sensors":[1.0]*80,
    "dropout_burst":[1.4 if i<35 else 0.65 for i in range(80)],
}

def _decision_measurements(name,truth,seed):
    rng_a=random.Random(seed); rng_b=random.Random(seed+7)
    a_cfg=SensorConfig(noise_std=0.12,resolution=0.01,dropout_rate=0.03,outlier_rate=0.05,outlier_scale=0.9)
    b_cfg=SensorConfig(noise_std=0.06,bias=0.04,resolution=0.02,dropout_rate=0.04,update_stride=3)
    a=[]; b=[]
    for i,value in enumerate(truth):
        av=measure(value,a_cfg,rng_a,i); bv=measure(value,b_cfg,rng_b,i)
        if name=="conflicting_sensors": av=(value-0.32 if i>15 else av); bv=(value+0.28 if i>15 and i%3==0 else bv)
        if name=="dropout_burst" and 30<=i<=50: av=None; bv=None
        a.append(av); b.append(bv)
    return a,b

def evaluate_rule(settings:dict,context:str,seed:int):
    threshold=float(settings["threshold"]); margin=float(settings["margin"]); weight=float(settings["weight_a"]); confirmations=int(settings["confirmations"]); method=str(settings["filter_method"]); window=int(settings["window"]); missing=str(settings["missing_policy"])
    total_unsafe=false_safe=unnecessary_stop=clear_count=collisions=0; delays=[]; scenario_rows=[]
    for offset,(name,truth) in enumerate(DECISION_SCENARIOS.items()):
        a,b=_decision_measurements(name,truth,seed+offset*101); af=apply_filter(a,method,window,0.35); bf=apply_filter(b,"Exponential",5,0.35); estimate=fuse(af,bf,weight)
        unsafe_streak=0; decisions=[]; first_unsafe=next((i for i,v in enumerate(truth) if v<=threshold),None); first_stop=None
        for i,(actual,est,av,bv) in enumerate(zip(truth,estimate,a,b)):
            both_missing=av is None and bv is None
            if both_missing:
                decision="STOP" if missing=="Stop" else "INSUFFICIENT" if missing=="Insufficient evidence" else "MOVE"
            elif est is None: decision="STOP"
            elif est<=threshold+margin:
                unsafe_streak+=1; decision="STOP" if unsafe_streak>=confirmations else "SLOW"
            elif est<=threshold+margin+0.35: unsafe_streak=0; decision="SLOW"
            else: unsafe_streak=0; decision="MOVE"
            decisions.append(decision)
            if actual<=threshold:
                total_unsafe+=1
                if decision=="MOVE": false_safe+=1
            if actual>=threshold+0.65:
                clear_count+=1
                if decision=="STOP": unnecessary_stop+=1
            if actual<=0.45 and decision=="MOVE": collisions+=1
            if first_unsafe is not None and i>=first_unsafe and decision=="STOP" and first_stop is None: first_stop=i
        if first_unsafe is not None: delays.append(((first_stop-first_unsafe)*DT) if first_stop is not None else float("inf"))
        scenario_rows.append({"scenario":name,"false_safe":sum(t<=threshold and d=="MOVE" for t,d in zip(truth,decisions)),"unnecessary_stop":sum(t>=threshold+0.65 and d=="STOP" for t,d in zip(truth,decisions)),"collision_events":sum(t<=0.45 and d=="MOVE" for t,d in zip(truth,decisions)),"final_decision":decisions[-1]})
    false_rate=false_safe/max(1,total_unsafe); stop_rate=unnecessary_stop/max(1,clear_count); finite=[x for x in delays if x!=float("inf")]; delay=max(finite) if finite and len(finite)==len(delays) else float("inf")
    criteria={"false_safe_limit":0.05 if context=="Warehouse" else 0.01,"unnecessary_stop_limit":0.35 if context=="Warehouse" else 0.45,"delay_limit":0.55 if context=="Warehouse" else 0.35}
    passed=false_rate<=criteria["false_safe_limit"] and stop_rate<=criteria["unnecessary_stop_limit"] and delay<=criteria["delay_limit"] and collisions==0 and missing in ("Stop","Insufficient evidence")
    return {"context":context,"settings":settings,"metrics":{"false_safe_rate":false_rate,"unnecessary_stop_rate":stop_rate,"maximum_detection_delay":delay,"collision_events":collisions},"criteria":criteria,"scenarios":scenario_rows,"passed":passed}

