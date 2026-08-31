from __future__ import annotations
import io
def sample_figure(samples,true_value):
    import matplotlib.pyplot as plt
    valid=[value for value in samples if value is not None]; figure,(ax1,ax2)=plt.subplots(1,2,figsize=(9,3.4)); ax1.plot([float("nan") if v is None else v for v in samples],linewidth=1); ax1.axhline(true_value,color="black",linestyle="--",label="truth"); ax1.set(xlabel="Sample",ylabel="Distance (m)",title="Measurement sequence"); ax1.legend(); ax2.hist(valid,bins=24,color="#4f8bc9",edgecolor="white"); ax2.axvline(true_value,color="black",linestyle="--"); ax2.set(xlabel="Distance (m)",ylabel="Count",title="Distribution"); figure.tight_layout(); return figure
def pipeline_figure(dataset,result):
    import matplotlib.pyplot as plt
    figure,axis=plt.subplots(figsize=(9,3.8)); axis.plot(dataset["time"],dataset["truth"],label="Ground truth",color="black",linewidth=2); axis.plot(dataset["time"],result["estimate"],label="Filtered/fused estimate",color="#d95f02",linewidth=1.5); axis.scatter(dataset["time"],dataset["sensor_a"],label="Sensor A",s=5,alpha=.22); axis.set(xlabel="Time (s)",ylabel="Distance (m)"); axis.grid(alpha=.2); axis.legend(ncol=3); figure.tight_layout(); return figure
def png_bytes(figure):
    stream=io.BytesIO(); figure.savefig(stream,format="png",dpi=150,bbox_inches="tight"); return stream.getvalue()

