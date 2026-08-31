from __future__ import annotations
from dataclasses import asdict,dataclass
import math, random

@dataclass(frozen=True)
class SensorConfig:
    noise_std: float=0.05
    bias: float=0.0
    resolution: float=0.001
    dropout_rate: float=0.0
    outlier_rate: float=0.0
    outlier_scale: float=1.0
    false_detection_rate: float=0.0
    minimum_range: float=0.1
    maximum_range: float=6.0
    update_stride: int=1

PROFILES={
    "biased":SensorConfig(noise_std=0.04,bias=0.22,resolution=0.01,dropout_rate=0.02,outlier_rate=0.01),
    "noisy":SensorConfig(noise_std=0.20,bias=0.01,resolution=0.01,dropout_rate=0.02,outlier_rate=0.02),
    "quantized":SensorConfig(noise_std=0.025,bias=-0.02,resolution=0.10,dropout_rate=0.01,outlier_rate=0.01),
    "outlier_prone":SensorConfig(noise_std=0.055,bias=0.0,resolution=0.01,dropout_rate=0.03,outlier_rate=0.12,outlier_scale=1.4),
}

def measure(true_value:float,config:SensorConfig,rng:random.Random,index:int=0)->float|None:
    if index%max(1,config.update_stride)!=0: return None
    if rng.random()<config.dropout_rate: return None
    if rng.random()<config.false_detection_rate: value=rng.uniform(config.minimum_range,min(true_value,config.maximum_range))
    else:
        value=true_value+config.bias+rng.gauss(0.0,config.noise_std)
        if rng.random()<config.outlier_rate: value+=rng.choice((-1.0,1.0))*rng.uniform(0.5,config.outlier_scale)
    if value<config.minimum_range or value>config.maximum_range: return None
    return round(value/config.resolution)*config.resolution

def static_samples(true_value:float,count:int,config:SensorConfig,seed:int)->list[float|None]:
    rng=random.Random(seed); return [measure(true_value,config,rng,index) for index in range(count)]

def sample_metrics(samples:list[float|None],true_value:float)->dict[str,float|int]:
    valid=[float(value) for value in samples if value is not None]; n=len(valid)
    mean=sum(valid)/n if n else math.nan; ordered=sorted(valid); median=(ordered[(n-1)//2]+ordered[n//2])/2 if n else math.nan
    variance=sum((value-mean)**2 for value in valid)/(n-1) if n>1 else 0.0
    robust_scale=max(0.02,1.4826*((sorted(abs(value-median) for value in valid)[n//2]) if n else 0.0)); outliers=sum(abs(value-median)>max(0.30,3*robust_scale) for value in valid)
    return {"count":len(samples),"valid_count":n,"dropout_count":len(samples)-n,"mean":mean,"median":median,"variance":variance,"standard_deviation":math.sqrt(variance),"bias":mean-true_value,"outlier_count":outliers}

def profile_for_seed(seed:int)->tuple[str,SensorConfig]:
    names=tuple(PROFILES); name=names[seed%len(names)]; return name,PROFILES[name]

def config_dict(config:SensorConfig): return asdict(config)

