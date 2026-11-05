"""Compact map with coordinate axes, object labels and recorded model movement."""
from html import escape
from pages.guided_visuals import svg
from simulation.robot_room import WIDTH, HEIGHT, START, GOAL, OBJECTS, WALLS


def room_svg(state, result=None, step=None):
    size, ox, oy = 34, 38, 42
    body = '<text x="18" y="20">Blue: robot | green: goal | gray: wall</text>'
    for y in range(HEIGHT):
        body += f'<text x="18" y="{oy+(y+.65)*size}" font-size="12">{y}</text>'
        for x in range(WIDTH):
            color = "#64748b" if (x,y) in WALLS else "#dcfce7" if [x,y] == GOAL else "#ffffff"
            body += f'<rect x="{ox+x*size}" y="{oy+y*size}" width="{size}" height="{size}" fill="{color}" stroke="#cbd5e1"/>'
    for x in range(WIDTH):
        body += f'<text x="{ox+(x+.35)*size}" y="37" font-size="12">{x}</text>'
    def point(cell):
        return ox+(cell[0]+.5)*size, oy+(cell[1]+.5)*size
    if result:
        path = result["path"] if step is None else result["path"][:step+1]
        points = " ".join(f"{point(p)[0]},{point(p)[1]}" for p in path)
        body += f'<polyline points="{points}" fill="none" stroke="#16a34a" stroke-width="4" opacity=".7"/>'
    for name, cell in OBJECTS.items():
        px,py = point(cell)
        color = "#ef4444" if name.startswith("red") else "#eab308" if name.startswith("yellow") else "#3b82f6"
        body += f'<rect x="{px-7}" y="{py-7}" width="14" height="14" fill="{color}"/>'
    px,py = point(START)
    body += f'<text x="{px-14}" y="{py-9}" font-size="11" font-weight="bold">S</text>'
    cell = result["path"][step] if result and step is not None else state["position"]
    px,py = point(cell)
    body += f'<circle cx="{px}" cy="{py}" r="10" fill="#2563eb" stroke="#172554" stroke-width="2"/>'
    body += '<text x="18" y="373" font-size="13">S: start (1,7) | target: (11,1) | coordinates: (column,row)</text>'
    body += '<text x="18" y="395" font-size="13">Red crate (2,1) | yellow toolbox (6,4) | blue target (11,1)</text>'
    return svg(body, 505, 415)
