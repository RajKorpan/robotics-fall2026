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
MAX_STEPS = 50
SCENARIOS = {
    "goal": {"label": "1. Goal only", "request": "Reach the blue target crate at column 11, row 1."},
    "map": {"label": "2. Direct toward the goal", "request": "Reach the blue target crate at (11,1). Reply with exactly the word RIGHT until column 3. Then reply UP until row 1. Then go RIGHT toward column 7, DOWN toward row 7, RIGHT toward column 11, and UP toward row 1."},
    "route": {"label": "3. Describe the detour", "request": "Reach the blue target crate at (11,1). From the start at (1,7), move UP to row 1, RIGHT to column 7, DOWN to row 7, RIGHT to column 11, then UP to row 1. Follow this detour around the two walls. Use current coordinates to decide which part of the route remains. Stop only at (11,1)."},
}
ROBOT_SYSTEM = "Follow the user's robot instruction using the supplied map and current state. Reply with one direction or STOP, without explanation. A blocked move leaves you in place. Use the feedback to choose a different free direction next. STOP pauses for one step only. Every run lasts 50 steps. At the goal, choose STOP to stay there for the remaining steps."



def initial_state():
    return {"position": START[:], "step": 0, "history": [], "finished": False,
            "goal_reached": False, "first_goal_step": None, "last_feedback": "No previous action.", "last_decision": None}


def state_key(state):
    return hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()


def contract():
    return state_key({"system": ROBOT_SYSTEM, "scenarios": SCENARIOS, "objects": OBJECTS, "walls": sorted(WALLS),
                      "size": [WIDTH, HEIGHT], "start": START, "goal": GOAL, "limit": MAX_STEPS,
                      "blocked_recovery": "free neighboring direction or STOP", "version": 4})


def ascii_map(state):
    return "\n".join("".join("R" if [x,y] == state["position"] else "G" if [x,y] == GOAL else "#" if (x,y) in WALLS else "." for x in range(WIDTH)) for y in range(HEIGHT))


def allowed_commands(state):
    """After a collision, restrict the next choice to free local moves or a pause."""
    if state["last_decision"] != "BLOCKED":
        return COMMAND_OPTIONS
    free = []
    for action,(dx,dy) in {"UP":(0,-1),"DOWN":(0,1),"LEFT":(-1,0),"RIGHT":(1,0)}.items():
        x,y = state["position"][0]+dx,state["position"][1]+dy
        if 0 <= x < WIDTH and 0 <= y < HEIGHT and (x,y) not in WALLS:
            free.append(action)
    return (*free,"STOP")


def model_message(request, state):
    neighbors = {}
    for name, (dx,dy) in {"UP":(0,-1), "DOWN":(0,1), "LEFT":(-1,0), "RIGHT":(1,0)}.items():
        p = [state["position"][0]+dx, state["position"][1]+dy]
        neighbors[name] = "wall" if tuple(p) in WALLS or not (0 <= p[0] < WIDTH and 0 <= p[1] < HEIGHT) else "free"
    return ("UP decreases row, DOWN increases row, LEFT decreases column, RIGHT increases column. STOP pauses for this step only. Each move is one cell. Objects mark free cells.\nMap rows 0 to 8, columns 0 to 12. # = wall, . = free, R = robot, G = goal.\n" + ascii_map(state)
            + "\nObjects (column,row): " + json.dumps(OBJECTS) + "\nCurrent position (column,row): " + str(state["position"])
            + "\nGoal: [11, 1]. Neighbor cells: " + json.dumps(neighbors)
            + "\nPrevious actions: " + ", ".join(state["history"][-12:])
            + "\nPrevious action feedback: " + state["last_feedback"]
            + "\nAllowed actions for this step: " + ", ".join(allowed_commands(state))
            + f"\nSteps completed: {state['step']} of {MAX_STEPS}. Goal visited: {state['goal_reached']}."
            + "\nInstruction: " + request + "\nNext action:")


def parse_command(text):
    value = text.strip().upper()
    return value if value in COMMAND_OPTIONS else None


def evaluate(record, state):
    before, after = copy.deepcopy(state), copy.deepcopy(state)
    action = parse_command(record["output"])
    decision, reason = "MOVE", "Moved one free cell."
    if state["finished"]:
        return {"before": before, "after": after, "action": action, "decision": "BLOCKED",
                "reason": "This run already completed 50 steps.", "goal_reached": state["goal_reached"]}
    if record.get("robot_state") != state:
        decision, reason = "BLOCKED", "The proposal was generated for a different state."
    elif action is None:
        decision, reason = "BLOCKED", "The reply is not one allowed direction or STOP."
    elif action == "STOP":
        decision, reason = "STOP", "STOP held the robot in place for this step. Choose again next step."
    else:
        dx, dy = {"UP":(0,-1), "DOWN":(0,1), "LEFT":(-1,0), "RIGHT":(1,0)}[action]
        candidate = [before["position"][0]+dx, before["position"][1]+dy]
        if tuple(candidate) in WALLS or not (0 <= candidate[0] < WIDTH and 0 <= candidate[1] < HEIGHT):
            decision, reason = "BLOCKED", "The move meets a wall or map boundary. No movement occurred. Choose a different free direction next step."
        else:
            after["position"] = candidate
    after["step"] += 1
    after["history"].append(action or "INVALID")
    reached = after["position"] == GOAL
    after["goal_reached"] = before["goal_reached"] or reached
    if reached and after["first_goal_step"] is None:
        after["first_goal_step"] = after["step"]
    after["finished"] = after["step"] >= MAX_STEPS
    if reached:
        reason += " The robot is at the goal."
    if after["finished"]:
        reason += " The 50-step limit ended the run."
    after["last_feedback"] = reason
    after["last_decision"] = decision
    return {"before": before, "after": after, "action": action, "decision": decision, "reason": reason, "goal_reached": after["goal_reached"]}


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
            "goal_reached": state["goal_reached"], "first_goal_step": state["first_goal_step"],
            "blocked_actions": sum(s["simulation"]["decision"] == "BLOCKED" for s in record["steps"]),
            "stop_actions": sum(s["simulation"]["decision"] == "STOP" for s in record["steps"]),
            "reason": record["steps"][-1]["simulation"]["reason"]}


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
