"""One-cell directional simulation. No planner chooses moves for the model."""
import copy
import hashlib
import json
from collections import deque

WIDTH, HEIGHT = 13, 9
START, GOAL = [1, 7], [11, 1]
OBJECTS = {"red crate": [2, 1], "yellow toolbox": [6, 4], "blue target crate": GOAL}
WALLS = ({(x, y) for x in range(WIDTH) for y in range(HEIGHT) if x in (0, WIDTH-1) or y in (0, HEIGHT-1)}
         | {(4, y) for y in range(2, 8)} | {(8, y) for y in range(1, 7)})
COMMAND_OPTIONS = ("UP", "DOWN", "LEFT", "RIGHT", "STOP")
COMMANDS = ", ".join(COMMAND_OPTIONS)
MAX_STEPS = 36
SCENARIOS = {
    "goal": {"label": "1. Goal only", "request": "Reach the blue target crate at column 11, row 1."},
    "map": {"label": "2. Direct toward the goal", "request": "Reach the blue target crate at (11,1). Reply with exactly the word RIGHT until column 3. Then reply UP until row 1. Then go RIGHT toward column 7, DOWN toward row 7, RIGHT toward column 11, and UP toward row 1."},
    "route": {"label": "3. Describe the detour", "request": "Reach the blue target crate at (11,1). From the start at (1,7), move UP to row 1, RIGHT to column 7, DOWN to row 7, RIGHT to column 11, then UP to row 1. Follow this detour around the two walls. Use current coordinates to decide which part of the route remains. Stop only at (11,1)."},
}
ROBOT_SYSTEM = "Follow the user's robot instruction using the supplied map and current state. Reply with one direction or STOP, without explanation."



def initial_state():
    return {"position": START[:], "step": 0, "history": [], "finished": False}


def state_key(state):
    return hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()


def contract():
    return state_key({"system": ROBOT_SYSTEM, "scenarios": SCENARIOS, "objects": OBJECTS, "walls": sorted(WALLS),
                      "size": [WIDTH, HEIGHT], "start": START, "goal": GOAL, "limit": MAX_STEPS, "version": 3})


def ascii_map(state):
    return "\n".join("".join("R" if [x,y] == state["position"] else "G" if [x,y] == GOAL else "#" if (x,y) in WALLS else "." for x in range(WIDTH)) for y in range(HEIGHT))


def model_message(request, state):
    neighbors = {}
    for name, (dx,dy) in {"UP":(0,-1), "DOWN":(0,1), "LEFT":(-1,0), "RIGHT":(1,0)}.items():
        p = [state["position"][0]+dx, state["position"][1]+dy]
        neighbors[name] = "wall" if tuple(p) in WALLS or not (0 <= p[0] < WIDTH and 0 <= p[1] < HEIGHT) else "free"
    return ("UP decreases row, DOWN increases row, LEFT decreases column, RIGHT increases column. STOP ends the run. Each move is one cell. Objects mark free cells.\nMap rows 0 to 8, columns 0 to 12. # = wall, . = free, R = robot, G = goal.\n" + ascii_map(state)
            + "\nObjects (column,row): " + json.dumps(OBJECTS) + "\nCurrent position (column,row): " + str(state["position"])
            + "\nGoal: [11, 1]. Neighbor cells: " + json.dumps(neighbors)
            + "\nPrevious actions: " + ", ".join(state["history"][-12:])
            + "\nInstruction: " + request + "\nNext action:")


def parse_command(text):
    value = text.strip().upper()
    return value if value in COMMAND_OPTIONS else None


def evaluate(record, state):
    before, after = copy.deepcopy(state), copy.deepcopy(state)
    action = parse_command(record["output"])
    decision, reason = "MOVE", "Moved one free cell."
    if record.get("robot_state") != state:
        decision, reason = "BLOCKED", "The proposal was generated for a different state."
    elif action is None:
        decision, reason = "BLOCKED", "The reply is not one allowed direction or STOP."
    elif state["finished"]:
        decision, reason = "BLOCKED", "This run already ended."
    elif action == "STOP":
        decision, reason = "STOP", "The model chose to stop."
    else:
        dx, dy = {"UP":(0,-1), "DOWN":(0,1), "LEFT":(-1,0), "RIGHT":(1,0)}[action]
        candidate = [before["position"][0]+dx, before["position"][1]+dy]
        if tuple(candidate) in WALLS or not (0 <= candidate[0] < WIDTH and 0 <= candidate[1] < HEIGHT):
            decision, reason = "BLOCKED", "The move meets a wall or map boundary. No movement occurred."
        else:
            after["position"] = candidate
    after["step"] += 1
    after["history"].append(action or "INVALID")
    reached = after["position"] == GOAL
    after["finished"] = decision != "MOVE" or reached or after["step"] >= MAX_STEPS
    if reached:
        reason = "Goal reached. The simulator ends the run here."
    elif after["step"] >= MAX_STEPS and decision == "MOVE":
        reason = "The 36-action limit ended the run."
    return {"before": before, "after": after, "action": action, "decision": decision, "reason": reason, "goal_reached": reached}


def summarize(record):
    state = initial_state()
    path = [START[:]]
    for step in record.get("steps", []):
        expected = evaluate(step["model"], state)
        if step["simulation"] != expected or state["finished"]:
            raise ValueError("The recorded steps do not replay from the starting map.")
        state = expected["after"]
        path.append(state["position"][:])
    if not record.get("steps") or not state["finished"]:
        raise ValueError("The robot run is incomplete.")
    return {"model_job_id": record["job_id"], "record_sha256": state_key(record), "simulator_contract": contract(),
            "after": state, "path": path, "actions": state["step"], "moves": sum(a != b for a,b in zip(path,path[1:])),
            "goal_reached": state["position"] == GOAL, "reason": record["steps"][-1]["simulation"]["reason"]}


def route(start, goal):
    """Feasibility check for preflight/tests only. Never used to control a run."""
    start, goal = tuple(start), tuple(goal)
    frontier, parent = deque([start]), {start: None}
    while frontier:
        cell = frontier.popleft()
        if cell == goal:
            path = []
            while cell is not None:
                path.append(list(cell))
                cell = parent[cell]
            return path[::-1]
        for dx,dy in ((0,-1),(0,1),(-1,0),(1,0)):
            p = cell[0]+dx, cell[1]+dy
            if 0 <= p[0] < WIDTH and 0 <= p[1] < HEIGHT and p not in WALLS and p not in parent:
                parent[p] = cell
                frontier.append(p)
    return []
