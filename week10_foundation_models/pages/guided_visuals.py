"""Compact visuals specific to the teaching experiment, with explicit units and labels."""
from html import escape
import math
import textwrap


def svg(body, width=600, height=260):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="#f1f5f9"/><g font-family="sans-serif" font-size="17" fill="#172b43">{body}</g></svg>'


def mission_one_setup():
    """Schematic of the exact places, objects and robot in the capability card."""
    body = '<text x="20" y="30" font-weight="bold">Mission 1: starting setup</text>'
    body += '<rect x="18" y="54" width="178" height="164" rx="10" fill="#dbeafe" stroke="#64748b"/>'
    body += '<text x="32" y="80" font-size="14" font-weight="bold">Base: robot starts here</text>'
    body += '<circle cx="105" cy="133" r="29" fill="#60a5fa" stroke="#1d4ed8" stroke-width="3"/>'
    body += '<rect x="68" y="121" width="12" height="31" rx="3" fill="#334155"/><rect x="130" y="121" width="12" height="31" rx="3" fill="#334155"/>'
    body += '<rect x="97" y="116" width="19" height="13" fill="#172b43"/><circle cx="111" cy="122" r="4" fill="white"/>'
    body += '<text x="39" y="185" font-size="15">Wheels and camera</text><text x="39" y="205" font-size="15">No arm or gripper</text>'
    body += '<rect x="216" y="54" width="178" height="164" rx="10" fill="#fef3c7" stroke="#64748b"/>'
    body += '<text x="237" y="80" font-weight="bold">Shelf</text><path d="M235 158 H375" stroke="#8b5e3c" stroke-width="10"/>'
    body += '<path d="M279 112 H324 L319 151 H284 Z" fill="#2563eb"/><path d="M324 121 C350 116 350 143 321 139" fill="none" stroke="#2563eb" stroke-width="6"/>'
    body += '<text x="272" y="193">Known cup</text>'
    body += '<rect x="414" y="54" width="178" height="164" rx="10" fill="#dcfce7" stroke="#64748b"/>'
    body += '<text x="435" y="80" font-weight="bold">Desk</text><path d="M433 155 H575 M445 155 V174 M562 155 V174" fill="none" stroke="#8b5e3c" stroke-width="7"/>'
    body += '<rect x="479" y="116" width="55" height="33" rx="3" fill="#b91c1c"/><path d="M485 140 H528" stroke="white" stroke-width="3"/>'
    body += '<text x="466" y="193">Known book</text>'
    return svg(body, 610, 235)


def cup_regions(selected=()):
    body = '<path d="M40 205 H560" stroke="#735337" stroke-width="10"/>'
    for name, x, color in (("A", 90, "#2563eb"), ("B", 330, "#d94646")):
        active = name in selected
        body += f'<rect x="{x-12}" y="52" width="165" height="140" rx="8" fill="{color}" fill-opacity="{.2 if active else .04}" stroke="{color}" stroke-width="{5 if active else 2}" stroke-dasharray="{0 if active else 6}"/>'
        body += f'<path d="M{x+15} 100 H{x+92} L{x+83} 177 H{x+24} Z" fill="{color}"/><path d="M{x+92} 115 C{x+145} 107 {x+145} 161 {x+90} 153" fill="none" stroke="{color}" stroke-width="9"/>'
        body += f'<text x="{x}" y="35">Region {name}: {"blue" if name=="A" else "red"} cup</text>'
    body += '<rect x="12" y="210" width="576" height="37" rx="5" fill="#e2e8f0" stroke="#64748b" stroke-dasharray="4"/><text x="22" y="235">Region C: shelf / background, not a cup</text>'
    return svg(body)


def robot_timeline(step):
    before = min(step * .2, .6)
    after = min((step + 1) * .2, .6)
    body = '<path d="M50 165 H540" stroke="#64748b" stroke-width="3"/><rect x="535" y="70" width="25" height="95" fill="#b18b65"/><text x="505" y="52">shelf</text>'
    for index in range(4):
        x = 60 + index * 155
        body += f'<path d="M{x} 160 V172" stroke="#64748b"/><text x="{x-10}" y="198">{index*.2:.1f} m</text>'
    bx, ax = 60 + before / .6 * 465, 60 + after / .6 * 465
    body += f'<circle cx="{bx}" cy="130" r="22" fill="#60a5fa" stroke="#1d4ed8" stroke-width="3"/><text x="20" y="30">Blue: observed robot position</text>'
    body += f'<circle cx="{ax}" cy="130" r="28" fill="none" stroke="#16a34a" stroke-width="3"/><text x="20" y="230">Green outline: resulting position after this command</text>'
    if ax != bx:
        body += f'<path d="M{bx+25} 130 H{ax-30}" stroke="#16a34a" stroke-width="4"/><path d="M{ax-35} 123 L{ax-25} 130 L{ax-35} 137" fill="#16a34a"/>'
    return svg(body)


def robot_pair():
    return svg('<circle cx="130" cy="150" r="45" fill="#60a5fa"/><rect x="70" y="135" width="15" height="55" fill="#334155"/><rect x="175" y="135" width="15" height="55" fill="#334155"/><path d="M130 150 L160 150" stroke="#172b43" stroke-width="4"/><text x="65" y="50">Mobile base</text><text x="35" y="235">drive and turn, no gripper</text><path d="M390 190 L435 110 L510 135" stroke="#94a3b8" stroke-width="22" fill="none"/><circle cx="435" cy="110" r="16" fill="#334155"/><path d="M510 115 V155 M535 115 V155 M510 115 H535" stroke="#334155" stroke-width="8"/><text x="390" y="50">Robot arm</text><text x="360" y="235">tool motion and gripper</text>')


def weights_diagram(choice, examples, instruction="Move it"):
    training = choice in ("LoRA", "Full fine-tuning", "Training from scratch")
    body = f'<text x="20" y="28">{escape(choice)}</text>'
    body += '<text x="20" y="65">Input / data</text>'
    count = examples if choice in ("Few-shot prompting", "Additional demonstrations", "LoRA", "Full fine-tuning", "Training from scratch") else 0
    body += '<rect x="20" y="78" width="155" height="40" fill="#dbeafe" stroke="#2563eb"/>'
    for index, line in enumerate(textwrap.wrap(instruction, 18)[:2]):
        body += f'<text x="28" y="{95 + index*16}" font-size="13">{escape(line)}</text>'
    for index in range(count):
        y = 125 + index * 15
        body += f'<rect x="20" y="{y}" width="155" height="12" fill="{["#60a5fa", "#f59e0b", "#a78bfa"][index%3]}"/>'
    label = "examples in context" if choice == "Few-shot prompting" else "robot demonstrations" if count else "instruction only"
    body += f'<text x="20" y="242" font-size="14">{label}</text>'
    if choice == "Additional demonstrations":
        body += '<text x="190" y="130" font-size="12">stored</text><text x="185" y="148" font-size="12">not trained</text>'
    else:
        body += '<path d="M188 130 H242" stroke="#475569" stroke-width="3"/>'
    body += '<text x="258" y="65">Model parameters</text>'
    for index in range(12):
        x, y = 260 + index % 4 * 40, 80 + index // 4 * 40
        color = "#f59e0b" if choice == "Full fine-tuning" else "#a78bfa" if choice == "Training from scratch" else "#cbd5e1"
        body += f'<rect x="{x}" y="{y}" width="32" height="32" rx="3" fill="{color}" stroke="#64748b"/>'
    if choice == "LoRA":
        body += '<rect x="445" y="90" width="30" height="45" fill="#f59e0b"/><rect x="485" y="140" width="30" height="45" fill="#f59e0b"/><text x="435" y="215" font-size="14">small trainable adapters</text>'
    else:
        label = "fixed pretrained weights" if not training else "all weights updated" if choice == "Full fine-tuning" else "new random start"
        body += f'<text x="258" y="215" font-size="14">{label}</text>'
    return svg(body)


def execution_result_svg(proposal, result):
    """Draw the actual skill effect, including non-motion outcomes and withheld requests."""
    from simulation.guided_validation import STATE

    before, after = result["before"], result["after"]
    tool, args = proposal["tool"], proposal["args"]
    attempted = result["decision"] == "EXECUTE"
    completed = result["completed"]
    color = "#15803d" if completed else "#b45309" if not attempted else "#b91c1c"
    label = "Completed" if completed else "Withheld: " + result["decision"] if not attempted else "Attempt failed"
    body = '<defs><marker id="move-tip" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6" fill="#15803d"/></marker></defs>'
    target = args.get("location", args.get("object", ""))
    request = tool + (": " + str(target) if target else "")
    body += f'<text x="18" y="28" font-weight="bold">Request: {escape(request)}</text>'
    body += f'<text x="18" y="51" font-size="14">Source: {escape(proposal["source"])} | age: {proposal["observation_age_s"]:.1f} s | score: {proposal["confidence"]:.1f}</text>'
    if proposal.get("ambiguous"):
        body += '<text x="18" y="73" font-size="14" fill="#b45309">Target needs clarification: which cup?</text>'

    def point(name):
        x, y = STATE["locations"][name]
        return 70 + x * 108, 245 - y * 65

    for name in STATE["locations"]:
        x, y = point(name)
        fill = "#fecaca" if name in STATE["forbidden"] else "#dbeafe"
        body += f'<rect x="{x-26}" y="{y-24}" width="66" height="45" fill="{fill}" stroke="#64748b"/><text x="{x-25}" y="{y+43}" font-size="14">{escape(name.replace("_", " "))}</text>'
    bx, by = point(before["position"])
    ax, ay = point(after["position"])
    if tool == "navigate_to" and target in STATE["locations"]:
        tx, ty = point(target)
        if completed:
            body += f'<circle cx="{bx}" cy="{by}" r="12" fill="none" stroke="#64748b" stroke-dasharray="4"/><path d="M{bx+12} {by} L{tx-14} {ty}" stroke="#15803d" stroke-width="4" marker-end="url(#move-tip)"/>'
        else:
            body += f'<path d="M{bx+12} {by} L{tx} {ty}" stroke="{color}" stroke-width="3" stroke-dasharray="6"/><circle cx="{tx}" cy="{ty}" r="29" fill="none" stroke="{color}" stroke-width="3"/>'
            body += f'<text x="305" y="78" font-size="14" fill="{color}">Requested route did not execute</text>' if not attempted else f'<text x="305" y="78" font-size="14" fill="{color}">Skill could not reach room</text>'
    if tool == "inspect":
        # Symbolic inspect records an object observation, not a base movement or camera ray.
        body += '<path d="M310 180 H334 L330 207 H314 Z M334 185 C350 182 350 199 333 199" fill="#2563eb" stroke="#2563eb" stroke-width="3"/>'
        body += f'<circle cx="322" cy="193" r="29" fill="none" stroke="{color}" stroke-width="4" stroke-dasharray="{0 if completed else 6}"/>'
        body += '<text x="300" y="242" font-size="14">known cup</text>'
        note = "Fresh inspection recorded" if completed else "No new inspection"
        body += f'<text x="300" y="78" font-size="14" fill="{color}">{note}</text>'
    body += f'<circle cx="{ax}" cy="{ay}" r="12" fill="#16a34a" stroke="#14532d" stroke-width="2"/>'
    body += f'<rect x="12" y="303" width="576" height="46" rx="6" fill="{color}"/><text x="24" y="332" fill="white" font-weight="bold">{escape(label)}</text>'
    return svg(body, 600, 360)
