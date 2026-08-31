export default function mountWaypointMission(component) {
  const { data, parentElement, setStateValue } = component;
  const find = (selector) => parentElement.querySelector(selector);
  const canvas = find("#route-canvas");
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;

  const SCALE = 150;
  const ORIGIN_X = 70;
  const ORIGIN_Y = height - 70;
  const START = { x: 0, y: 0 };
  const PEDESTRIANS = [{ x: 0.75, y: 0.60 }, { x: 1.55, y: 1.40 }];
  const WAYPOINTS = [
    { x: 1.15, y: 0.35 },
    { x: 1.15, y: 1.05 },
    { x: 1.95, y: 1.05 },
    { x: 1.55, y: 2.05 },
  ];
  const SAFE_RADIUS = 0.28;
  const PLAN_WAYPOINT_RADIUS = 0.22;
  const TRUE_WAYPOINT_RADIUS = 0.24;
  const ROUTE_ARRIVAL_RADIUS = 0.14;
  const MEAN_TRACK_LIMIT = 0.05;
  const MAX_TRACK_LIMIT = 0.10;
  const TRUE_WHEEL_RADIUS = 0.050;
  const TRACK_WIDTH = 0.34;
  const DT = 0.02;
  const DRAW_SAMPLE_SPACING = 0.035;
  const MAX_ROUTE_POINTS = 1200;

  const rawIncoming = data?.state && typeof data.state === "object" ? data.state : {};
  const defaultsNeedMigration = Number(rawIncoming.version ?? 0) < 6;
  const incoming = defaultsNeedMigration
    ? { ...rawIncoming, params: {}, drove: false, passed: false, metrics: {}, trace: [] }
    : rawIncoming;
  let route = Array.isArray(incoming.route)
    ? incoming.route.map((point) => ({ x: Number(point[0]), y: Number(point[1]) })).filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y))
    : [];
  let strokeBreaks = Array.isArray(incoming.stroke_breaks)
    ? incoming.stroke_breaks.map(Number).filter((value) => Number.isInteger(value) && value > 0 && value <= route.length)
    : (route.length ? [route.length] : []);
  let gains = {
    kp: Number(incoming.params?.heading_kp ?? 0.3),
    ki: Number(incoming.params?.heading_ki ?? 1.00),
    kd: Number(incoming.params?.heading_kd ?? 0.00),
  };
  let forwardSpeed = Number(incoming.params?.forward_speed ?? 0.48);
  let wheelRadiusEstimate = Number(incoming.params?.wheel_radius_estimate_m ?? 0.054);
  let driving = false;
  let animationId = null;
  let displayTrace = Array.isArray(incoming.trace) ? incoming.trace : [];
  let currentState = incoming;
  let drawingStroke = false;
  let activePointerId = null;
  let strokeStartLength = route.length;
  let runGeneration = 0;
  const listenerCleanups = [];
  const tuningControls = [
    "#heading-kp", "#heading-ki", "#heading-kd", "#forward-speed", "#wheel-radius",
  ].map(find);

  function listen(target, eventName, handler, options) {
    target.addEventListener(eventName, handler, options);
    listenerCleanups.push(() => target.removeEventListener(eventName, handler, options));
  }

  const worldToScreen = (x, y) => ({ x: ORIGIN_X + x * SCALE, y: ORIGIN_Y - y * SCALE });
  const screenToWorld = (x, y) => ({ x: (x - ORIGIN_X) / SCALE, y: (ORIGIN_Y - y) / SCALE });
  const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
  const wrap = (angle) => {
    while (angle > Math.PI) angle -= 2 * Math.PI;
    while (angle < -Math.PI) angle += 2 * Math.PI;
    return angle;
  };

  function integrate(pose, leftDistance, rightDistance) {
    const travel = (leftDistance + rightDistance) / 2;
    const turn = (rightDistance - leftDistance) / TRACK_WIDTH;
    let { x, y, theta } = pose;
    if (Math.abs(turn) < 1e-9) {
      x += travel * Math.cos(theta);
      y += travel * Math.sin(theta);
    } else {
      const radius = travel / turn;
      const nextTheta = theta + turn;
      x += radius * (Math.sin(nextTheta) - Math.sin(theta));
      y += -radius * (Math.cos(nextTheta) - Math.cos(theta));
      theta = nextTheta;
    }
    return { x, y, theta: wrap(theta) };
  }

  function distanceToSegment(point, a, b) {
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const lengthSquared = dx * dx + dy * dy;
    const amount = lengthSquared > 0
      ? clamp(((point.x - a.x) * dx + (point.y - a.y) * dy) / lengthSquared, 0, 1)
      : 0;
    return Math.hypot(point.x - (a.x + amount * dx), point.y - (a.y + amount * dy));
  }

  function distanceToRoute(point) {
    const points = [START, ...route];
    let best = Infinity;
    for (let index = 0; index < points.length - 1; index += 1) {
      best = Math.min(best, distanceToSegment(point, points[index], points[index + 1]));
    }
    return best;
  }

  function samplePolyline(points, spacing = 0.025) {
    const samples = [];
    for (let index = 0; index < points.length - 1; index += 1) {
      const a = points[index];
      const b = points[index + 1];
      const count = Math.max(1, Math.ceil(distance(a, b) / spacing));
      for (let step = 0; step <= count; step += 1) {
        const amount = step / count;
        samples.push({ x: a.x + amount * (b.x - a.x), y: a.y + amount * (b.y - a.y) });
      }
    }
    return samples;
  }

  function orderedProgress(points, waypointRadius) {
    let nextWaypoint = 0;
    for (const point of points) {
      if (nextWaypoint < WAYPOINTS.length && distance(point, WAYPOINTS[nextWaypoint]) <= waypointRadius) {
        nextWaypoint += 1;
      }
    }
    return { waypointsReached: nextWaypoint };
  }

  function trimRouteAtFinalWaypoint() {
    let nextWaypoint = 0;
    let finalIndex = -1;
    for (let index = 0; index < route.length; index += 1) {
      if (distance(route[index], WAYPOINTS[nextWaypoint]) <= PLAN_WAYPOINT_RADIUS) {
        nextWaypoint += 1;
        if (nextWaypoint === WAYPOINTS.length) {
          finalIndex = index;
          break;
        }
      }
    }
    if (finalIndex < 0) return;
    route = route.slice(0, finalIndex + 1);
    route[route.length - 1] = { ...WAYPOINTS.at(-1) };
    strokeBreaks = strokeBreaks.filter((value) => value < route.length);
    if (strokeBreaks.at(-1) !== route.length) strokeBreaks.push(route.length);
  }

  // Normalize old saved routes that continued beyond WP4.
  trimRouteAtFinalWaypoint();

  function planStatus() {
    if (!route.length) {
      return { waypointsReached: 0, minPedestrianGap: 999, safe: false, complete: false };
    }
    const samples = samplePolyline([START, ...route]);
    const progress = orderedProgress(samples, PLAN_WAYPOINT_RADIUS);
    let minPedestrianGap = Infinity;
    for (const pedestrian of PEDESTRIANS) minPedestrianGap = Math.min(minPedestrianGap, distanceToRoute(pedestrian));
    const safe = minPedestrianGap >= SAFE_RADIUS;
    return {
      ...progress,
      minPedestrianGap,
      safe,
      complete: progress.waypointsReached === WAYPOINTS.length && safe,
    };
  }

  function baseState(overrides = {}) {
    const plan = planStatus();
    return {
      version: 7,
      route: route.map((point) => [Number(point.x.toFixed(4)), Number(point.y.toFixed(4))]),
      stroke_breaks: strokeBreaks,
      params: {
        heading_kp: gains.kp,
        heading_ki: gains.ki,
        heading_kd: gains.kd,
        forward_speed: forwardSpeed,
        wheel_radius_estimate_m: wheelRadiusEstimate,
        true_wheel_radius_m: TRUE_WHEEL_RADIUS,
      },
      planner: {
        waypoints_reached: plan.waypointsReached,
        waypoint_total: WAYPOINTS.length,
        planned_min_pedestrian_gap: Number.isFinite(plan.minPedestrianGap) ? plan.minPedestrianGap : 999,
        safe: plan.safe,
        complete: plan.complete,
      },
      drove: false,
      passed: false,
      metrics: {},
      trace: [],
      recording_frames: [],
      recording_frame_duration_ms: 120,
      ...overrides,
    };
  }

  function publish(overrides = {}) {
    currentState = baseState(overrides);
    setStateValue("state", currentState);
  }

  function setPlanMessage() {
    const plan = planStatus();
    const status = find("#plan-status");
    if (!route.length) {
      status.className = "plan-status idle";
      status.textContent = "Add a point to begin.";
    } else if (plan.waypointsReached < WAYPOINTS.length) {
      status.className = "plan-status bad";
      status.textContent = `Next target: WP${plan.waypointsReached + 1}.`;
    } else if (!plan.safe) {
      status.className = "plan-status bad";
      status.textContent = "The planned route enters a pedestrian safety zone.";
    } else {
      status.className = "plan-status ok";
      status.textContent = "Route ready: WP1–WP4 in order with safe clearance.";
    }
    find("#drive-route").disabled = driving || drawingStroke || !plan.complete;
  }

  function resetRun({ emit = true } = {}) {
    runGeneration += 1;
    if (animationId !== null) cancelAnimationFrame(animationId);
    animationId = null;
    driving = false;
    for (const control of tuningControls) control.disabled = false;
    find("#undo-route").disabled = false;
    find("#clear-route").disabled = false;
    displayTrace = [];
    currentState = baseState();
    find("#mean-track").textContent = "-- m";
    find("#max-track").textContent = "-- m";
    find("#ped-gap").textContent = "-- m";
    find("#waypoints-reached").textContent = `0 / ${WAYPOINTS.length}`;
    const verdict = find("#verdict");
    verdict.className = "verdict idle";
    verdict.textContent = planStatus().complete ? "Route ready. Tune, then drive." : "Plan a complete route before driving.";
    setPlanMessage();
    draw();
    if (emit) setStateValue("state", currentState);
  }

  function bindSlider(id, valueId, format, setter) {
    const slider = find(`#${id}`);
    const value = find(`#${valueId}`);
    const handleInput = () => {
      const parsed = Number(slider.value);
      setter(parsed);
      value.textContent = format(parsed);
      displayTrace = [];
      const verdict = find("#verdict");
      verdict.className = "verdict idle";
      verdict.textContent = "Settings changed. Drive again to test them.";
    };
    const handleChange = () => publish();
    listen(slider, "input", handleInput);
    listen(slider, "change", handleChange);
  }

  find("#heading-kp").value = String(gains.kp);
  find("#heading-ki").value = String(gains.ki);
  find("#heading-kd").value = String(gains.kd);
  find("#forward-speed").value = String(forwardSpeed);
  find("#wheel-radius").value = String(wheelRadiusEstimate * 1000);
  find("#heading-kp-value").textContent = gains.kp.toFixed(1);
  find("#heading-ki-value").textContent = gains.ki.toFixed(2);
  find("#heading-kd-value").textContent = gains.kd.toFixed(2);
  find("#forward-speed-value").textContent = `${forwardSpeed.toFixed(2)} m/s`;
  find("#wheel-radius-value").textContent = `${(wheelRadiusEstimate * 1000).toFixed(1)} mm`;

  bindSlider("heading-kp", "heading-kp-value", (value) => value.toFixed(1), (value) => { gains.kp = value; });
  bindSlider("heading-ki", "heading-ki-value", (value) => value.toFixed(2), (value) => { gains.ki = value; });
  bindSlider("heading-kd", "heading-kd-value", (value) => value.toFixed(2), (value) => { gains.kd = value; });
  bindSlider("forward-speed", "forward-speed-value", (value) => `${value.toFixed(2)} m/s`, (value) => { forwardSpeed = value; });
  bindSlider("wheel-radius", "wheel-radius-value", (value) => `${value.toFixed(1)} mm`, (value) => { wheelRadiusEstimate = value / 1000; });

  function pointFromPointer(event) {
    const bounds = canvas.getBoundingClientRect();
    const point = screenToWorld(
      (event.clientX - bounds.left) * (width / bounds.width),
      (event.clientY - bounds.top) * (height / bounds.height),
    );
    if (point.x < -0.1 || point.y < -0.1 || point.x > 3.4 || point.y > 2.4) return null;
    return point;
  }

  function appendDrawPoint(point, { force = false } = {}) {
    if (!point || route.length >= MAX_ROUTE_POINTS) return false;
    const previous = route.at(-1);
    if (!force && previous && distance(previous, point) < DRAW_SAMPLE_SPACING) return false;
    if (previous && distance(previous, point) < 0.004) return false;
    route.push(point);
    return true;
  }

  function beginStroke(event) {
    if (driving || planStatus().complete || event.button !== 0) return;
    const point = pointFromPointer(event);
    if (!point) return;
    event.preventDefault();
    drawingStroke = true;
    activePointerId = event.pointerId;
    strokeStartLength = route.length;
    canvas.classList.add("drawing");
    try { canvas.setPointerCapture(event.pointerId); } catch (_) { /* best effort */ }
    displayTrace = [];
    if (!route.length) appendDrawPoint({ ...START }, { force: true });
    appendDrawPoint(point, { force: true });
    resetRun({ emit: false });
  }

  function extendStroke(event) {
    if (!drawingStroke || event.pointerId !== activePointerId) return;
    event.preventDefault();
    const coalesced = typeof event.getCoalescedEvents === "function" ? event.getCoalescedEvents() : [];
    const samples = coalesced.length ? coalesced : [event];
    let changed = false;
    for (const sample of samples) changed = appendDrawPoint(pointFromPointer(sample)) || changed;
    if (changed) {
      setPlanMessage();
      draw();
    }
  }

  function finishStroke(event) {
    if (!drawingStroke || event.pointerId !== activePointerId) return;
    event.preventDefault();
    appendDrawPoint(pointFromPointer(event), { force: true });
    drawingStroke = false;
    canvas.classList.remove("drawing");
    try { canvas.releasePointerCapture(event.pointerId); } catch (_) { /* already released */ }
    activePointerId = null;
    trimRouteAtFinalWaypoint();
    if (route.length > strokeStartLength && strokeBreaks.at(-1) !== route.length) strokeBreaks.push(route.length);
    resetRun();
  }

  listen(canvas, "pointerdown", beginStroke);
  listen(canvas, "pointermove", extendStroke);
  listen(canvas, "pointerup", finishStroke);
  listen(canvas, "pointercancel", finishStroke);

  function undoRoute() {
    if (driving) return;
    if (strokeBreaks.length) {
      strokeBreaks.pop();
      route = route.slice(0, strokeBreaks.at(-1) ?? 0);
    } else {
      route = [];
    }
    resetRun();
  }

  function clearRoute() {
    if (driving) return;
    route = [];
    strokeBreaks = [];
    resetRun();
  }

  listen(find("#undo-route"), "click", undoRoute);
  listen(find("#clear-route"), "click", clearRoute);

  function drive() {
    const plan = planStatus();
    if (driving || !plan.complete) return;
    driving = true;
    runGeneration += 1;
    const thisRun = runGeneration;
    find("#drive-route").disabled = true;
    find("#undo-route").disabled = true;
    find("#clear-route").disabled = true;
    for (const control of tuningControls) control.disabled = true;

    const firstDirectionPoint = route.find((point) => distance(point, START) > 0.01) ?? route[0];
    const initialHeading = firstDirectionPoint
      ? Math.atan2(firstDirectionPoint.y - START.y, firstDirectionPoint.x - START.x)
      : 0;
    let truePose = { x: START.x, y: START.y, theta: initialHeading };
    let estimatedPose = { x: START.x, y: START.y, theta: initialHeading };
    let routeIndex = 0;
    while (routeIndex < route.length && distance(START, route[routeIndex]) <= ROUTE_ARRIVAL_RADIUS) {
      routeIndex += 1;
    }
    let integral = 0;
    let previousError = 0;
    let minPedestrianGap = Infinity;
    let trackErrorSum = 0;
    let trackErrorCount = 0;
    let maxTrackError = 0;
    let simulationStep = 0;
    const truePath = [{ ...truePose }];
    const trace = [[0, truePose.x, truePose.y, truePose.theta, estimatedPose.x, estimatedPose.y, estimatedPose.theta]];
    const calibrationRatio = wheelRadiusEstimate / TRUE_WHEEL_RADIUS;
    const maxSteps = 9000;
    const recordingCanvas = document.createElement("canvas");
    recordingCanvas.width = 320;
    recordingCanvas.height = Math.round(height * recordingCanvas.width / width);
    const recordingContext = recordingCanvas.getContext("2d");
    let recordingFrames = [];
    let renderedFrameCount = 0;
    let captureEvery = 5;
    const maxRecordingFrames = 36;

    function captureRecordingFrame() {
      if (!recordingContext) return;
      if (recordingFrames.length >= maxRecordingFrames) {
        recordingFrames = recordingFrames.filter((_, index) => index % 2 === 0);
        captureEvery *= 2;
      }
      recordingContext.drawImage(canvas, 0, 0, recordingCanvas.width, recordingCanvas.height);
      recordingFrames.push(recordingCanvas.toDataURL("image/jpeg", 0.58));
    }

    function physicsStep() {
      if (routeIndex >= route.length) return true;
      const goal = route[routeIndex];
      const desiredHeading = Math.atan2(goal.y - estimatedPose.y, goal.x - estimatedPose.x);
      const error = wrap(desiredHeading - estimatedPose.theta);
      integral = clamp(integral + error * DT, -2, 2);
      const derivative = (error - previousError) / DT;
      previousError = error;
      const angularCommand = clamp(gains.kp * error + gains.ki * integral + gains.kd * derivative, -3, 3);
      const speed = forwardSpeed * clamp(1 - Math.abs(error) / (Math.PI / 2), 0.25, 1);
      const leftDistance = (speed - angularCommand * TRACK_WIDTH / 2) * DT;
      const rightDistance = (speed + angularCommand * TRACK_WIDTH / 2) * DT;

      truePose = integrate(truePose, leftDistance, rightDistance);
      estimatedPose = integrate(estimatedPose, leftDistance * calibrationRatio, rightDistance * calibrationRatio);
      for (const pedestrian of PEDESTRIANS) minPedestrianGap = Math.min(minPedestrianGap, distance(truePose, pedestrian));
      const trackingError = distanceToRoute(truePose);
      trackErrorSum += trackingError;
      trackErrorCount += 1;
      maxTrackError = Math.max(maxTrackError, trackingError);
      while (routeIndex < route.length && distance(estimatedPose, route[routeIndex]) <= ROUTE_ARRIVAL_RADIUS) {
        routeIndex += 1;
        integral = 0;
        previousError = 0;
      }
      truePath.push({ ...truePose });
      simulationStep += 1;
      if (simulationStep % 5 === 0) {
        trace.push([
          simulationStep * DT,
          truePose.x, truePose.y, truePose.theta,
          estimatedPose.x, estimatedPose.y, estimatedPose.theta,
        ]);
      }
      return false;
    }

    let done = false;
    function frame() {
      if (thisRun !== runGeneration) return;
      for (let count = 0; count < 6 && !done; count += 1) {
        done = physicsStep() || simulationStep >= maxSteps;
      }
      if (![truePose.x, truePose.y, truePose.theta, estimatedPose.x, estimatedPose.y, estimatedPose.theta].every(Number.isFinite)) {
        done = true;
      }
      draw(truePath, truePose, estimatedPose);
      if (renderedFrameCount % captureEvery === 0) captureRecordingFrame();
      renderedFrameCount += 1;
      if (!done) {
        animationId = requestAnimationFrame(frame);
        return;
      }

      if (trace.at(-1)?.[0] !== simulationStep * DT) {
        trace.push([
          simulationStep * DT,
          truePose.x, truePose.y, truePose.theta,
          estimatedPose.x, estimatedPose.y, estimatedPose.theta,
        ]);
      }
      const actualProgress = orderedProgress(truePath, TRUE_WAYPOINT_RADIUS);
      const meanTrackError = trackErrorCount ? trackErrorSum / trackErrorCount : Infinity;
      const hitPedestrian = minPedestrianGap < SAFE_RADIUS;
      const precise = meanTrackError <= MEAN_TRACK_LIMIT && maxTrackError <= MAX_TRACK_LIMIT;
      const followedRoute = routeIndex >= route.length;
      const passed = followedRoute
        && actualProgress.waypointsReached === WAYPOINTS.length
        && !hitPedestrian
        && precise;
      const metrics = {
        route_points_reached: routeIndex,
        route_points_total: route.length,
        mission_waypoints_reached: actualProgress.waypointsReached,
        mission_waypoint_total: WAYPOINTS.length,
        min_pedestrian_gap: minPedestrianGap,
        mean_tracking_error: meanTrackError,
        max_tracking_error: maxTrackError,
        safe_radius: SAFE_RADIUS,
        mean_tracking_limit: MEAN_TRACK_LIMIT,
        max_tracking_limit: MAX_TRACK_LIMIT,
      };
      displayTrace = trace;
      captureRecordingFrame();
      currentState = baseState({
        drove: true,
        passed,
        metrics,
        trace,
        recording_frames: recordingFrames,
        recording_frame_duration_ms: Math.round((1000 / 60) * captureEvery),
      });

      find("#mean-track").textContent = `${meanTrackError.toFixed(2)} m`;
      find("#max-track").textContent = `${maxTrackError.toFixed(2)} m`;
      find("#ped-gap").textContent = `${minPedestrianGap.toFixed(2)} m`;
      find("#waypoints-reached").textContent = `${actualProgress.waypointsReached} / ${WAYPOINTS.length}`;
      const verdict = find("#verdict");
      verdict.className = `verdict ${passed ? "ok" : "bad"}`;
      if (passed) verdict.textContent = "Pass: all waypoints, safe clearance, and precise tracking.";
      else if (hitPedestrian) verdict.textContent = "Too close to a pedestrian. Add route clearance or improve calibration.";
      else if (!followedRoute || actualProgress.waypointsReached < WAYPOINTS.length) verdict.textContent = "The real robot missed a waypoint or did not finish the route.";
      else verdict.textContent = "Tracking is not precise enough yet. Tune gains, speed, and odometry.";

      driving = false;
      animationId = null;
      find("#undo-route").disabled = false;
      find("#clear-route").disabled = false;
      for (const control of tuningControls) control.disabled = false;
      setPlanMessage();
      setStateValue("state", currentState);
    }
    frame();
  }

  listen(find("#drive-route"), "click", drive);

  function draw(truePath = null, truePose = null, estimatedPose = null) {
    ctx.fillStyle = "#0f172a";
    ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = "rgba(255,255,255,0.05)";
    ctx.lineWidth = 1;
    for (let x = 0; x <= 3.4; x += 0.5) {
      const top = worldToScreen(x, 2.4);
      const bottom = worldToScreen(x, 0);
      ctx.beginPath(); ctx.moveTo(top.x, top.y); ctx.lineTo(bottom.x, bottom.y); ctx.stroke();
    }
    for (let y = 0; y <= 2.4; y += 0.5) {
      const left = worldToScreen(0, y);
      const right = worldToScreen(3.4, y);
      ctx.beginPath(); ctx.moveTo(left.x, left.y); ctx.lineTo(right.x, right.y); ctx.stroke();
    }

    for (const pedestrian of PEDESTRIANS) {
      const center = worldToScreen(pedestrian.x, pedestrian.y);
      ctx.setLineDash([4, 3]);
      ctx.fillStyle = "rgba(236,72,153,0.12)";
      ctx.strokeStyle = "#ec4899";
      ctx.lineWidth = 1.4;
      ctx.beginPath(); ctx.arc(center.x, center.y, SAFE_RADIUS * SCALE, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = "#ec4899";
      ctx.beginPath(); ctx.arc(center.x, center.y - 7, 5, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = "#ec4899";
      ctx.lineWidth = 3;
      ctx.beginPath(); ctx.moveTo(center.x, center.y - 2); ctx.lineTo(center.x, center.y + 9); ctx.stroke();
    }

    const sampledRoute = route.length ? samplePolyline([START, ...route]) : [];
    const routeProgress = orderedProgress(sampledRoute, PLAN_WAYPOINT_RADIUS);
    WAYPOINTS.forEach((waypoint, index) => {
      const center = worldToScreen(waypoint.x, waypoint.y);
      const reached = index < routeProgress.waypointsReached;
      ctx.save(); ctx.translate(center.x, center.y); ctx.rotate(Math.PI / 4);
      ctx.fillStyle = reached ? "rgba(34,197,94,0.18)" : "rgba(234,179,8,0.12)";
      ctx.strokeStyle = reached ? "#22c55e" : "#eab308";
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.rect(-8, -8, 16, 16); ctx.fill(); ctx.stroke(); ctx.restore();
      ctx.fillStyle = reached ? "#22c55e" : "#eab308";
      ctx.font = "bold 10px system-ui";
      ctx.textAlign = "center";
      ctx.fillText(`WP${index + 1}`, center.x, center.y - 14);
    });

    const start = worldToScreen(START.x, START.y);
    ctx.fillStyle = "#94a3b8";
    ctx.beginPath(); ctx.arc(start.x, start.y, 7, 0, Math.PI * 2); ctx.fill();
    ctx.font = "bold 10px system-ui";
    ctx.textAlign = "center";
    ctx.fillText("START", start.x, start.y + 19);

    if (route.length) {
      ctx.strokeStyle = "#38bdf8";
      ctx.lineWidth = 2.5;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.beginPath(); ctx.moveTo(start.x, start.y);
      route.forEach((point) => { const next = worldToScreen(point.x, point.y); ctx.lineTo(next.x, next.y); });
      ctx.stroke();
      const end = worldToScreen(route.at(-1).x, route.at(-1).y);
      ctx.fillStyle = "#38bdf8";
      ctx.beginPath(); ctx.arc(end.x, end.y, 5, 0, Math.PI * 2); ctx.fill();
      ctx.lineCap = "butt";
      ctx.lineJoin = "miter";
    } else {
      ctx.fillStyle = "#94a3b8";
      ctx.font = "bold 13px system-ui";
      ctx.textAlign = "center";
      ctx.fillText("Press and drag from START to draw", width / 2, height - 24);
    }

    let renderedTruePath = truePath;
    if (!renderedTruePath && displayTrace.length) renderedTruePath = displayTrace.map((row) => ({ x: row[1], y: row[2] }));
    if (renderedTruePath?.length > 1) {
      ctx.strokeStyle = "#22c55e";
      ctx.lineWidth = 2.6;
      ctx.beginPath();
      renderedTruePath.forEach((point, index) => {
        const center = worldToScreen(point.x, point.y);
        if (index === 0) ctx.moveTo(center.x, center.y); else ctx.lineTo(center.x, center.y);
      });
      ctx.stroke();
    }

    if (!estimatedPose && displayTrace.length) {
      const last = displayTrace.at(-1);
      estimatedPose = { x: last[4], y: last[5] };
      truePose = { x: last[1], y: last[2] };
    }
    if (estimatedPose) {
      const center = worldToScreen(estimatedPose.x, estimatedPose.y);
      ctx.fillStyle = "#f79009";
      ctx.beginPath(); ctx.arc(center.x, center.y, 4, 0, Math.PI * 2); ctx.fill();
    }
    if (truePose) {
      const center = worldToScreen(truePose.x, truePose.y);
      ctx.fillStyle = "#22c55e";
      ctx.strokeStyle = "#dcfce7";
      ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(center.x, center.y, 6, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    }

    ctx.textAlign = "left";
    ctx.font = "11px system-ui";
    ctx.fillStyle = "#38bdf8"; ctx.fillText("● route you drew", 12, 18);
    ctx.fillStyle = "#22c55e"; ctx.fillText("● robot's true path", 12, 34);
    ctx.fillStyle = "#f79009"; ctx.fillText("● odometry estimate", 12, 50);
    ctx.fillStyle = "#ec4899"; ctx.fillText("● pedestrian safety zone", 12, 66);
  }

  function restoreResult() {
    setPlanMessage();
    if (!incoming.drove || !incoming.metrics) {
      resetRun({ emit: false });
      return;
    }
    const metrics = incoming.metrics;
    find("#mean-track").textContent = `${Number(metrics.mean_tracking_error).toFixed(2)} m`;
    find("#max-track").textContent = `${Number(metrics.max_tracking_error).toFixed(2)} m`;
    find("#ped-gap").textContent = `${Number(metrics.min_pedestrian_gap).toFixed(2)} m`;
    find("#waypoints-reached").textContent = `${metrics.mission_waypoints_reached} / ${WAYPOINTS.length}`;
    const verdict = find("#verdict");
    verdict.className = `verdict ${incoming.passed ? "ok" : "bad"}`;
    if (incoming.passed) verdict.textContent = "Pass: all waypoints, safe clearance, and precise tracking.";
    else if (Number(metrics.min_pedestrian_gap) < SAFE_RADIUS) verdict.textContent = "Too close to a pedestrian. Add route clearance or improve calibration.";
    else if (Number(metrics.mission_waypoints_reached) < WAYPOINTS.length) verdict.textContent = "The real robot missed a waypoint or did not finish the route.";
    else verdict.textContent = "Tracking is not precise enough yet. Tune gains, speed, and odometry.";
    draw();
  }

  restoreResult();
  return () => {
    runGeneration += 1;
    if (animationId !== null) cancelAnimationFrame(animationId);
    for (const removeListener of listenerCleanups) removeListener();
    canvas.classList.remove("drawing");
  };
}
