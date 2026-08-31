# PID Odometry Lab — Context for Continuation

## What this is

Interactive Streamlit teaching lab for PID control and differential-drive odometry. Features progressive tutorial flow, interactive HTML/JS components, mission-gated progression, reflective check-ins, bridge cards connecting concepts across sections, and ZIP submission export.

## Entry points

- Main app: `app.py` (2205 lines)
- Run app: `.venv/bin/streamlit run app.py`
- Smoke test: `.venv/bin/python app.py --smoke-test`
- Simulation library: `sim_core.py` (612 lines)

## Interactive HTML/JS components

Three custom Streamlit components using `declare_component` (self-contained HTML with Streamlit message protocol):

1. `pid_concepts/index.html` (754 lines) — "You are the controller" mini-game with 5 progressive sections: hero, manual control (3 rounds), P-only demo, PD demo, full PID with disturbance, handoff. Sends `{done: true}` on completion.
2. `pid_playground/index.html` (642 lines) — Real-time PID visualization with draggable target, 2-column layout: canvas (600x300) with robot/target/error + panel with 5 meter bars (Error, P, I, D, Command). Arrow keys for disturbance.
3. `odometry_playground/index.html` (582 lines) — Top-down differential drive visualization, true path (blue) vs odometry estimate (dashed orange), wheel speed sliders, preset buttons, "Drive square" sequence, built-in sensor imperfection, calibration expander.

## App structure

### Page flow (via `st.session_state["stage"]`)

1. `intro` — Hero page with CSS gradient background
2. `pid_concepts` — Interactive "you are the controller" mini-game component
3. `background` — PID theory: error, P/I/D terms, block diagram
4. `pid_playground` — Interactive PID visualization component
5. `odom_background` — Odometry theory: differential drive, encoder integration
6. `odom_playground` — Interactive odometry visualization component
7. `lab` — Multi-mission lab (missions 1-3 + bonus)
8. `export` — Final export page with combined ZIP

### Mission system

- `MISSION_ORDER = ("mission_1", "mission_2", "mission_3")`
- Missions unlock sequentially; each requires passing metrics + completing reflective check-ins + writing explanations
- **Mission 1**: Open-loop vs PID — gate: `final_error < 0.08`, `overshoot < 0.25`, `settling_time < 4.5`
- **Mission 2**: Odometry calibration — gate: `position_error < 0.15`, `heading_error_deg < 8`
- **Mission 3**: Student-drawn pedestrian-safe route + heading PID + odometry — gate: WP1–WP4 in order, pedestrian gap ≥ 0.28 m, mean tracking error ≤ 0.05 m, max tracking error ≤ 0.10 m
- **Bonus**: Disturbance rejection — gate: `final_error < 0.10`

### Key functions

Simulations:
- `simulate_pid(kp, ki, kd, ...)` → `PIDResult`
- `simulate_open_loop_trials(power, run_time)` → list of `OpenLoopTrial`
- `simulate_odometry(wheel_radius, track_width)` → `OdomResult`
- `simulate_path_following(h_kp, h_ki, h_kd, ...)` → `PathFollowResult` (uses `sim_core.py` pure pursuit)
- `simulate_disturbance_rejection(kp, ki, kd, ...)` → `PIDResult`

Plotting:
- `plot_pid`, `plot_open_loop`, `plot_odometry`, `plot_path_following`

Metrics:
- `pid_metrics(result)` → dict with `final_error`, `overshoot`, `settling_time`, `command_effort`
- `odom_metrics(result)` → dict with `final_position_error`, `final_heading_error_deg`, `mean_path_error`

Mission/export:
- `mission_context()`, `active_mission()`, `mark_mission_complete()`, `mission_unlocked()`
- `render_checkin()` — reflective question gate (required by default)
- `render_bridge()` — bridge card connecting concepts across sections
- `render_student_identity()`, `render_mission_explanations()`
- `build_mission_zip()` — per-mission ZIP with JSON, CSV, plots, explanations
- `build_final_zip()` — combined export of all completed missions

Instructor:
- Password-protected sidebar controls (default: `pid-odometry-master`)
- Can override via Streamlit secrets or `PID_MASTER_PASSWORD` env var

### Lazy imports pattern

`st`, `np`, `plt` are set to `None` at module level. `run_streamlit_app()` initializes them via `require()`. This keeps the smoke test path independent of Streamlit.

## Dependencies

`requirements.txt`: `streamlit>=1.30`, `numpy`, `matplotlib`

Virtual environment: `.venv/` (already created with all deps installed)

## Verification status (2026-07-07)

- `python -m py_compile app.py` — passed
- `python app.py --smoke-test` — passed (all 5 simulation types produce valid output)
- All 3 HTML components created and syntactically valid
- `__pycache__` cleaned up

## Ticket log

### T-001 — pid_concepts tutorial improvements (done, 2026-07-21)
Two changes to `pid_concepts/index.html` ("You are the controller" mini-game):
1. Section 1 (manual play): right-only push. Removed LEFT button (RIGHT button now `primary`), dropped ArrowLeft handling, retargeted rounds to progressively rightward `[1.5, 3.0, 4.2]`, updated intro copy + post-play insight text to describe coast/overshoot instead of left-right over-correction.
2. Section 4 (full PID wind demo): replaced the static "WIND <<<" label with an animated leftward-streaming arrow field in `drawTrack` (driven by new `opts.windPhase`, fed from sim time `t`). Shows the constant leftward disturbance the whole run.
Verified: extracted component JS passes `node --check`; `app.py --smoke-test` passes. NOT yet verified live in a browser/Streamlit iframe.

### T-002 — batch of pedagogy improvements (done, 2026-07-21)
Feedback from reviewing the current app state. All 8 implemented:
1. **Open vs closed loop** — new `sec-loop` cards in pid_concepts/index.html (hero reframed to a car at a stop sign) + "Step 1" scaffolding block in `render_background_page` (app.py).
2. **Controller types (bang-bang + P + PID)** — new `sec-types` section in pid_concepts (three .ctrl-type cards) + "Step 2" in background page. Rewired flow: insight → types → P.
3. **More scaffolding at start of background** — background page now opens with numbered Steps 1–3 (intuition before the block-diagram formalism).
4. **Car + stop sign reframe** — pid_concepts hero, sec-loop, manual play (GAS pedal button, "STOP LINE" canvas label via new `opts.targetLabel` in drawTrack). Kept right-only push from T-001 as the accelerator.
5. **Odometry connective tissue** — odom_background page: added "the chain we're building" thread up top + three `st.info(icon=➡️)` transitions between the 4 lesson sections.
6. **Arm pause at poses** — arm_playground/index.html: each pose now MOVE (2.6s) → HOLD (1.3s); scoring happens at end of HOLD; on-canvas "HOLDING ✓" badge + side-panel phase label.
7. **Sociotechnical / consequences** — new `sec-stakes` section in pid_concepts (overshoot-into-crosswalk vs clean stop) + bridge card + new `background_social` check-in (added to export `checkin_keys`; gates the background Continue button alongside `background_compare`).
8. **Mission 1 term toggles** — arm_playground: P/I/D on-off buttons gate each term in the physics (`termOn`); presets re-enable all; Mission 1 intro text tells students to try P-only → P+D → PID.

Verified: `py_compile` OK; `--smoke-test` passes; extracted JS for both components passes `node --check`; Streamlit AppTest renders background/odom_background/pid_concepts/lab with no exceptions; background page gating confirmed (Continue disabled until both check-ins answered). NOT yet eyeballed live in a browser for visual polish.

### T-003 — professional tone pass (done, 2026-07-21)
User: verbiage was too dramatic ("Act then hope") for an educational activity. Rewrote to a neutral, professional register:
- pid_concepts/index.html: hero, sec-loop cards ("Command without feedback" / "Command based on measurement"), sec-types cards, sec-stakes (removed "body count"/"two-ton"), P-only insight, post-manual insight summary (also fixed physics: right-only push can't "drift back"), handoff box ("Power of Three Gains" → "Three gains, many applications"), button labels.
- app.py render_background_page: Step 1/Step 2 copy rewritten to match.
Verified: JS `node --check` OK, `py_compile` OK.

### T-004 — auto-save responses & GIFs (done, 2026-07-21)
User: text responses and GIFs should auto-save to the submissions folder on their own (no button press).
Added to app.py: `AUTOSAVE_DIR = student_submission/autosave`, `ALL_CHECKIN_KEYS`, `collect_text_responses()`, `_text_responses_markdown()`, and `autosave_responses_and_gifs()`. Called at end of `run_streamlit_app()` (after widgets render, so latest values are captured); writes `responses.json` + `responses.md` and `autosave/<mission>/activity_gifs/*.gif`. Change-detected via a hash digest in session_state (`_autosave_digest`) so disk is only touched on change; wrapped in try/except so autosave never breaks the UI. Sidebar shows a "auto-saved (timestamp)" caption. Manual save buttons left intact.
Note: `student_submission/` is intentionally NOT gitignored — the lab's model is save→commit→submit Git link.
Verified via AppTest: typing a check-in writes responses.md/json automatically; digest stable when unchanged, changes on new content. Test artifacts cleaned from student_submission/.

### T-005 — substantive rebuild: Mission 3, ethics, cliff (done, 2026-07-21)
User called out T-002 as a surface pass. Rebuilt the three real asks:
- **Mission 3 → waypoint navigation.** New `simulate_waypoint_nav()` (app.py): robot drives WP1→WP4 steering the heading PID by its OWN odometry estimate; wheels move TRUE pose using true wheel radius, odom integrates same wheel motion with the ESTIMATED radius. Miscalibration → robot "believes" it arrived while truly off-course. New `WaypointNavResult` dataclass, `_waypoint_nav_svg` (true path solid cyan vs believed path dashed orange + WP rings green/orange by true reach), `csv_for_waypoint_nav`. New `render_mission_3` with a step-by-step "how steering works" expander (scaffolds the heading-error→PID→turn loop, notes it's the pure-pursuit idea per goal point) + a wheel-radius calibration slider (44–56mm, true=50). Pass = truly reach all 4 WPs AND final gap <0.20m (needs good tuning AND good calibration). Verified via AppTest: good calib+tuned PASSES; 56mm+same tuning FAILS. Old `simulate_path_following`/`plot_path_following`/`_mission3_pathfollow_svg` left in place (smoke test still uses path_following); export + mission_context + roadmap + explanation prompts updated to waypoint framing.
- **Cliff demo (pid_concepts sec-stakes).** Interactive canvas: road ends at a cliff; stop line = cliff edge. "Run aggressive" (Kp3.2/Kd0.2) overshoots → car tips over; "Run careful" (Kp1.2/Kd2.0, verified settles ~2.97) stops at edge. `drawCliff()` + `runCliff()` in the component JS.
- **Ethics capstone.** New `ethics` stage between bonus and export: `render_ethics_capstone_page()` — delivery-robot case + 3 gated check-ins (failure mode / margin trade-off / accountability). Keys `ethics_failure_mode|margin|accountability` added to autosave `ALL_CHECKIN_KEYS`, export `checkin_keys`, and instructor jump-to-page. Bonus "Continue" now → ethics → export.
- Fixed a pre-existing latent bug: two "Back to lab" buttons on the export page collided (StreamlitDuplicateElementId) when <3 missions done — gave them unique keys.

Verified: `py_compile` OK, `--smoke-test` OK, pid_concepts JS `node --check` OK, all stages (intro→ethics→export, bonus) render with no exceptions via AppTest, M3 pass/fail logic confirmed. Test artifacts cleaned from student_submission/. NOT yet eyeballed live in a browser.

### T-006 — bang-bang live demo (done, 2026-07-21)
Controller-types section named bang-bang but never showed it. Added a live demo to `sec-types` in pid_concepts/index.html: `bb-canvas` + "Run bang-bang controller" button + on/off command bar. JS runner applies full ±CMD_CLAMP toward target outside an 0.08 deadband, nothing inside — classic limit cycle (verified ~8 flips, oscillates ~1.6–2.8 around target 2.0). Caption reports flip count, points to P as the fix. Bang-bang intentionally kept on the plain track (not the cliff) — it oscillates ACROSS the target, and the chatter is its lesson; a cliff would end it on the first swing.

### T-007 — cliff visual across all PID demos + real fall + less overshoot (done, 2026-07-21)
User: P/PD/PID cart demos overshoot too much; the cliff car should ACTUALLY fall off; use the cliff for ALL the PID tutorial demos, not just the stakes section.
- **Less overshoot:** raised shared `DAMPING` 0.5→1.0 in pid_concepts JS. P now overshoots ~0.6 (was ~1.1), PD ~0.08, PID settles ~2.0. Believable, not a wild fly-past. (Also gentler manual game + tighter bang-bang limit cycle — both still fine.)
- **Cliff everywhere:** refactored the stakes `drawCliff` into a reusable `drawCliffScene(ctx,pos,target,opts)` (road → cliff edge, rocky face, dashed centre line, error arc, animated wind streaks for the PID demo, and a real gravity fall via `opts.fall`). `runSim` (the P/PD/PID engine) now draws the cliff instead of `drawTrack`; the three section-open init draws use it too; canvases bumped 160→200px tall.
- **Real fall:** cliff edge sits at `target + EDGE_MARGIN` (0.35) so a small overshoot is a safe near-miss but a big one goes over. When `pos` crosses the edge, `runSim`/`runCliff` switch into a fall animation (car leaves the road, arcs past the edge, accelerates down `~fall²`, tips nose-down, drops off-screen). Verified: **P-only falls off; PD and PID stay safe.** Cliff-demo presets retuned for DAMPING=1.0 (aggressive Kp2.6/Kd0.2 → over; careful Kp2.0/Kd1.6 → stops at edge).
- Copy updated: P lead/insight/caption reference the cliff and use a `fell` flag; stakes intro now says "you already saw P drive off the cliff" instead of introducing it fresh. `drawTrack` retained only for the manual warmup (plain stop line) and bang-bang.
Verified: JS `node --check` OK, `py_compile`+`--smoke-test` OK, all stages render via AppTest, fall/no-fall logic confirmed by headless sim. NOT yet eyeballed live in a browser (the fall animation especially is worth a visual check).

### T-008 — cliff edge = target, remove stakes section, rewrite odometry §4 (done, 2026-07-21)
Three follow-ups:
- **PD/PID stopped short of the cliff.** Root cause: I'd placed the edge 0.35m PAST the target, so PD/PID (which settle at ~2.0) looked like they undershot. Fix: edge is now drawn AT the target; the car may hang over the brink but only FALLS once `pos > target + FALL_TOLERANCE` (0.30). Verified: P falls, PD/PID settle right on the edge. Replaced `EDGE_MARGIN` with `FALL_TOLERANCE`; edge draw uses `target`.
- **Removed the "Tuning has real-world consequences" (sec-stakes) section** entirely per user — HTML block, its cliff A/B demo (`cliff-canvas`, `drawCliff` wrapper, `runCliff`, aggressive/careful handlers, `CLIFF_TARGET`, `cliffAnim`), `stakes-continue`, and the `.stakes-*` CSS. `pid-continue` now goes straight to the handoff (`sec-done`) + `sendDone()`. `drawCliffScene` kept (P/PD/PID use it).
- **Odometry §4 (heading geometry) rewrite** — user: unclear, glitchy, equation didn't render. (a) app.py: replaced fragile inline `$$...\mathrel{+}=...\tfrac...$$` markdown (the `\mathrel{+}=`/`\tfrac` likely broke KaTeX) with plain-language scaffolding + reliable `st.latex()` calls (Δs, Δθ, pose update). (b) Rewrote `odometry_lessons/06_heading_geometry.html` from scratch: dropped the 4-act auto-cycling animation / desyncing derivation slides / pivot constructions; now a single always-in-sync view — two wheel sliders + 4 presets (straight/left/right/spin), live top-down canvas (wheel arcs, pivot, Δθ arc, start-vs-current chassis), and an HTML derivation panel plugging the numbers into Δθ=(dR−dL)/L with a plain-language verdict. Verified pose math (right wheel farther → +19° left turn, etc.).
Verified: both components `node --check` OK, `py_compile`+`--smoke-test` OK, odom_background + pid_concepts render via AppTest.

### T-009 — remove ZIP download buttons (done, 2026-07-21)
User: shouldn't have the ability to download a zip. Removed all 5 `st.download_button` calls (missions 1/2/3, bonus, final export) plus their `zip_bytes = build_*_zip(...)` builds and "before downloading" captions. The save-to-submissions-folder path is now the sole submission mechanism (already backed by autosave). Kept `build_mission_zip`/`build_final_submission_zip` — still used internally by `save_mission_submission`/`save_final_submission` (build archive → extract to folder). Reworded user-facing copy: export page title "Final Export"→"Final Submission" and intro now describes saving to the folder + Git commit; student-info caption drops "ZIP files". Bonus/export save buttons made `type="primary"`.
Verified: `py_compile`+`--smoke-test` OK; lab+export render with zero download buttons via AppTest; Mission 3 pass→save/unlock flow intact (save button present, no Download).

### T-010 — manual gas one-shot, wind arrow direction, PID-wind fall bug (done, 2026-07-21)
Three fixes in pid_concepts/index.html:
- **Gas = one hold-and-release per round.** Was: tap repeatedly. Now `manState.gasSpent`; `pressGas()` ignores presses once spent, `releaseGas()` locks the pedal (disables button → "GAS USED") after the first burst ends. `startManualRound` re-enables/relabels the button. Keydown uses `!e.repeat`. Copy updated ("one press of the gas… hold, then let go").
- **Wind arrows pointed the wrong way.** PID demo wind pushes the car LEFT (wind=-0.8) but the cliff-scene streak arrowheads pointed right. Flipped arrowheads to point left (tip at `hx - streakLen`) and added a left-pointing "◀ WIND" label; streaks already scroll left.
- **Full PID overshot the drawn edge but didn't fall.** Edge is drawn at target(2.0) but fall threshold is target+0.30(2.30); old PID gains (Ki0.5/Kd1.0) peaked at 2.22 — visibly past the edge yet floating. Retuned PID-wind demo to Kp2.0/Ki0.3/Kd1.4: full PID now peaks 2.016 (settles 2.003, right AT the edge, never crosses), PD-only stops short at 1.60 (steady-state offset lesson intact). Updated lead + captions to the new gains and "line" wording.
Verified: JS `node --check` OK, headless sim confirms PD-undershoot / PID-settles-at-edge / neither falls, pid_concepts renders via AppTest.

### T-011 — arm toggles removed, GIF autosave, ethics removed, Mission 3 rebuilt as pedestrian nav (done, 2026-07-21)
Batch of requests:
- **Removed arm P/I/D toggle buttons** (arm_playground/index.html: HTML/CSS/`termOn` state/handlers/preset-reenable/physics gating) + the Mission-1 intro paragraph in app.py that described them.
- **GIF auto-save**: added `_persist_gifs_to_folder()` — uploaded GIFs write straight to `student_submission/<mission>/activity_gifs/` the moment they're attached (plus the existing digest autosave). Uploader caption/help now say "auto-saved". Verified an uploaded GIF lands on disk with no button press.
- **Removed the ethics capstone** stage entirely (page fn, `ETHICS_CHECKIN_KEYS`, router branch, instructor jump entry, bonus→ethics button now → export). Its 3 sociotechnical check-ins moved INTO Mission 3 (keys `ethics_failure_mode|margin|accountability` still in autosave/export lists).
- **Mission 3 rebuilt → "Sidewalk delivery"**: pedestrian-aware waypoint nav. `simulate_waypoint_nav` now has 2 pedestrians at (1.53,0.40)&(0.30,1.51), `safe_radius=0.25`, tracks `min_pedestrian_gap`/`hit_pedestrian` (new dataclass fields). Tuned so 48–51mm wheel-radius clears everyone while ≤46/≥52mm drifts into a pedestrian AND misses waypoints. **Pass = truly reach all 4 WPs AND not hit_pedestrian.** Verified end-to-end via AppTest: 50mm PASSES, 44/56mm FAIL.
- **M3 controls off the sidebar**: now a 2-col layout — animated SVG (robot marker driving the true path, pedestrians with green/red safe rings, believed vs true path) on the left; Kp/Ki/Kd/speed/calibration sliders + metrics on the right. 5 check-ins (2 technical + 3 sociotechnical) gate the check.
- The old static-SVG + sidebar setup was what felt "bugged/doesn't run"; the sim itself was fine (50mm always reached 4/4). New view is animated and self-contained.
Verified: `py_compile`+`--smoke-test` OK; all 7 stages render via AppTest; M3 pass(50)/fail(44,56) confirmed; both components `node --check` OK; 5 check-ins + 5 inline sliders present; no ethics/M3-sidebar dangling refs.

### T-012 — Mission 3 student-drawn route completion (done, 2026-07-21)
Finished the partially created `waypoint_draw` work and made it the real Mission 3 experience:
- Replaced the unconnected legacy iframe prototype with a Streamlit Custom Components v2 implementation (`component.html`, `component.css`, `component.js`) and wired it into `app.py`.
- Students press and drag to draw a smooth route. The component previews the stroke locally and syncs with Streamlit only after pointer-up, avoiding reruns during drawing. Planning is accepted when the route visits WP1→WP4 in order and stays outside both pedestrian safety zones; WP4 is the end, with no loop-back requirement.
- Students tune heading Kp/Ki/Kd, forward speed, and wheel-radius calibration, then drive the route. The component shows the drawn route, true robot path, odometry estimate, pedestrians, waypoint progress, and live metrics.
- Pass now requires the real robot to follow the whole route, truly reach every named waypoint, maintain ≥0.28 m pedestrian clearance, mean tracking error ≤0.05 m, and max error ≤0.10 m.
- Component state survives Streamlit reruns. Mission gating consumes the component's returned result, invalidates stale passes after edits, and submission export now saves both `drawn_route.csv` and the true-vs-odometry `waypoint_nav_run.csv` trace.
- Removed deprecated `use_container_width` arguments encountered during the Streamlit pass.

Verified: `py_compile` and all simulation smoke tests pass; component JS parses as an ES module; Mission 3 renders with zero AppTest exceptions. A live headless-browser test drew the entire open route in one continuous pointer stroke, accepted WP4 as the endpoint, and passed at 50 mm with mean error 0.01 m, max error 0.05 m, clearance 0.34 m, and 4/4 waypoints. Undo removed the full stroke in one action.

### T-013 — Mission 3 baseline difficulty + lifecycle stabilization (done, 2026-07-21)
- Replaced the pre-solved defaults with an intentionally untuned baseline: Kp 0.3, Ki 1.0, Kd 0, speed 0.48 m/s, and wheel-radius estimate 54 mm. Tightened the tracking gate to mean ≤0.05 m and max ≤0.10 m. Versioned state migration invalidates old passing defaults once while preserving the drawn route.
- Fixed the post-WP4 reset/teleport bug. Root causes were event listeners accumulating across CCv2 remounts and Python hydrating the frontend from an external state mirror that lagged the component's own state by one rerun. All listeners now have lifecycle cleanup, and the wrapper hydrates from the component widget state before mounting.
- WP4 is now a hard endpoint: route samples after the first valid WP4 crossing are discarded and old trailing routes are normalized on load.

Verified live after five separate slider-triggered remounts: the untuned default run remained failed and stable (3/4 waypoints, 0.19 m clearance, mean 0.10 m, max 0.28 m); a tuned run produced one stable simulator/result with 4/4, 0.34 m clearance, mean 0.01 m, max 0.05 m, and no reset or teleport after the completion rerun.

### T-014 — automatic Mission 3 GIF recording (done, 2026-07-21)
- Removed the activity-GIF upload widgets from every mission and submission screen.
- Mission 3 now records the actual route canvas while the robot drives. Long runs progressively thin their sampled frames so component state stays bounded.
- On completion, Python encodes the captured frames with Pillow and immediately overwrites `student_submission/mission_3/activity_gifs/latest_drive.gif`; no upload or save click is required. The recorded GIF is also included automatically in mission and final submissions.

### T-015 — automatic artifacts for every mission + Mission 3 stale-run guard (done, 2026-07-21)
- Mission 1 now records the actual arm canvas until three target poses are held and saves `mission_1/activity_gifs/latest_arm_tuning.gif`. The mission check waits for that real activity result.
- Mission 2 records the actual completed odometry test sequence and saves `mission_2/activity_gifs/latest_odometry_test.gif`.
- Mission 3 keeps its actual drive recording. Bonus now renders the actual simulated PID trajectory into `bonus/activity_gifs/latest_disturbance_run.gif` automatically.
- Every mission also writes a compact `latest_run.json` with current parameters and metrics; reflections continue to auto-save under `student_submission/autosave/`.
- Fixed Mission 3's apparent random upward drive: the robot had a hard-coded upward starting heading and briefly targeted the START sample. It now aligns to the first real route segment and skips samples already inside the START arrival radius.
- Tuning controls are locked during a drive, and a per-mount run-generation token invalidates stale animation callbacks during resets/unmounts, preventing old runs from drawing again or teleporting after a Kd change.

### T-016 — Bonus activity removed (done, 2026-07-21)
- Removed the disturbance-rejection Bonus activity and its simulator, animation/GIF generation, check-in, explanation, save flow, instructor jump target, roadmap card, autosave/export registrations, and smoke-test case.
- Mission 3 now saves and proceeds directly to Final Submission.
- Old sessions are normalized to the three real missions, so a stale `bonus` progress entry cannot produce `4/3` completion or route back into a removed page.
- Existing `student_submission/bonus/` files are intentionally preserved as historical student work; the app no longer reads, updates, or exports them.

### T-017 — professional assignment copy (done, 2026-07-21)
- Replaced the promotional intro slogan with a direct description of the course assignment.
- Removed the three feature boxes and the Mission Roadmap from the intro page.
- Reworded nearby pitch-like phrases (`Same idea, new robot skill`, `power of the full PID`, and `Three gains, many applications`) as neutral instructional text.

- Run the Streamlit app in a browser and test all 8 pages render correctly
- Test the remaining tutorial components live in a browser
- Test mission progression flow end-to-end (pass mission 1 → unlock 2 → pass 2 → unlock 3 → pass 3 → bonus → export)
- Test instructor password-protected controls
