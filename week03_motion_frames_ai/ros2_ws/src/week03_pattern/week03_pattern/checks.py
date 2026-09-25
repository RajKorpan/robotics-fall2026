"""Course-provided checks and timing logic. No ROS installation needed."""
import hashlib
import math
from pathlib import Path

SPECIFICATIONS = {
    "l_path": "Three segments: forward 0.40 m, rotate left 90°, forward 0.40 m. Finish at (0.40, 0.40) m, heading 90°.",
    "rounded_rectangle": "Eight segments: alternate forward legs of 0.40, 0.25, 0.40, 0.25 m with four left 90° arcs of radius 0.15 m. Finish near the starting pose.",
    "alternating_arcs": "Four forward arcs: turn +45°, -45°, +45°, -45°, each of radius 0.30 m. Finish facing the initial direction.",
}


def validate(segments):
    if not isinstance(segments,list) or not 1 <= len(segments) <= 12:
        raise ValueError("Return a nonempty list of at most 12 segments")
    for s in segments:
        v,w,d=float(s.linear_x),float(s.angular_z),float(s.duration)
        if not all(math.isfinite(n) for n in (v,w,d)) or abs(v)>.22 or abs(w)>.8 or not 0<d<=30:
            raise ValueError("Use finite speeds within 0.22 m/s and 0.8 rad/s, and durations in (0, 30] seconds")
    if sum(s.duration for s in segments)>60:
        raise ValueError("The full pattern must take at most 60 seconds")


def command_at(segments, elapsed):
    """Return (v, omega). Empty patterns and times after completion request a stop."""
    if not math.isfinite(elapsed) or elapsed<0:
        return 0.,0.
    # sum() and repeated += can differ by a few ulps for fractional durations.
    # Check the total first so the end time is always a stop, never a final arc.
    if elapsed>=sum(s.duration for s in segments):
        return 0.,0.
    boundary=0.
    for s in segments:
        boundary+=s.duration
        if elapsed<boundary:
            return float(s.linear_x),float(s.angular_z)
    return 0.,0.


def endpoint(segments):
    x=y=a=0.
    for s in segments:
        v,w,d=s.linear_x,s.angular_z,s.duration
        if abs(w)<1e-9:
            x+=v*d*math.cos(a); y+=v*d*math.sin(a)
        else:
            b=a+w*d
            x+=v/w*(math.sin(b)-math.sin(a)); y-=v/w*(math.cos(b)-math.cos(a)); a=b
    return {"x":x,"y":y,"theta":math.atan2(math.sin(a),math.cos(a))}


def shape_ok(name, segments):
    """Check each specified primitive, not merely the final endpoint."""
    validate(segments)
    if name=="l_path":
        expected=[(.4,0,None),(0,math.pi/2,0),(.4,0,None)]
    elif name=="rounded_rectangle":
        expected=[]
        for length in (.4,.25,.4,.25):
            expected.extend([(length,0,None),(None,math.pi/2,.15)])
    elif name=="alternating_arcs":
        expected=[(None,angle,.30) for angle in (math.pi/4,-math.pi/4,math.pi/4,-math.pi/4)]
    else:
        return False
    if len(segments)!=len(expected):
        return False
    for s,(distance,angle,radius) in zip(segments,expected):
        if distance is not None and abs(s.linear_x*s.duration-distance)>.02:
            return False
        if abs(s.angular_z*s.duration-angle)>.04:
            return False
        if radius is not None:
            if abs(s.angular_z)<1e-9 or abs(abs(s.linear_x/s.angular_z)-radius)>.02:
                return False
        if distance is None and s.linear_x<=0:
            return False
    return True


def source_hash(root):
    root=Path(root)
    digest=hashlib.sha256()
    for path in sorted([*(root/'week03_pattern').rglob('*.py'),*(root/'test').rglob('*.py')]):
        digest.update(path.relative_to(root).as_posix().encode()); digest.update(path.read_bytes())
    return digest.hexdigest()
