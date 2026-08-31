from __future__ import annotations
import math

def hold_last(values):
    output=[]; last=None
    for value in values:
        if value is not None: last=float(value)
        output.append(last)
    return output
def moving_average(values,window):
    output=[]; recent=[]
    for value in values:
        if value is not None: recent.append(float(value))
        if len(recent)>window: recent=recent[-window:]
        output.append(sum(recent)/len(recent) if recent else None)
    return output
def median_filter(values,window):
    output=[]; recent=[]
    for value in values:
        if value is not None: recent.append(float(value))
        if len(recent)>window: recent=recent[-window:]
        ordered=sorted(recent); n=len(ordered); output.append(((ordered[(n-1)//2]+ordered[n//2])/2) if n else None)
    return output
def exponential(values,alpha):
    output=[]; state=None
    for value in values:
        if value is not None: state=float(value) if state is None else alpha*float(value)+(1-alpha)*state
        output.append(state)
    return output
def apply_filter(values,method,window=5,alpha=0.3):
    if method=="Raw/hold last": return hold_last(values)
    if method=="Moving average": return moving_average(values,window)
    if method=="Median": return median_filter(values,window)
    if method=="Exponential": return exponential(values,alpha)
    raise ValueError(f"Unknown filter: {method}")
def fuse(a,b,weight_a):
    output=[]
    for av,bv in zip(a,b):
        if av is None: output.append(bv)
        elif bv is None: output.append(av)
        else: output.append(weight_a*av+(1-weight_a)*bv)
    return output
def error_metrics(truth,estimate,dt=0.05,step_index=120):
    pairs=[(t,e) for t,e in zip(truth,estimate) if e is not None]; errors=[abs(t-e) for t,e in pairs]
    rmse=math.sqrt(sum((t-e)**2 for t,e in pairs)/len(pairs)); mae=sum(errors)/len(errors); maximum=max(errors)
    target=truth[min(step_index+1,len(truth)-1)]; delay=None
    for index in range(step_index,len(estimate)):
        if estimate[index] is not None and abs(estimate[index]-target)<=0.15:
            delay=(index-step_index)*dt; break
    return {"rmse":rmse,"mae":mae,"max_error":maximum,"response_delay":delay if delay is not None else float("inf"),"availability":len(pairs)/len(truth)}

