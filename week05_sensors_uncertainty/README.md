# Week 5 — Sensors, Noise, and Uncertainty

An individual, self-contained robotics lab delivered through Streamlit. Students characterize an assigned imperfect sensor, compare filtering and sensor-fusion strategies, and design context-sensitive safety policies for warehouse and assistive robots. ROS is intentionally not required: the lab concentrates on measurement, estimation, evidence, and decisions.

## Learning objectives

By the end of the lab, a student can:

- distinguish random noise, systematic bias, quantization, dropout, false detections, and outliers;
- compute and interpret mean, median, variance, bias, and data availability;
- compare moving-average, median, and exponential filters;
- fuse a fast/noisy sensor with a slow/biased sensor;
- quantify the trade-off between smoothing, error, availability, and response delay;
- evaluate a decision rule using false-safe errors, unnecessary stops, detection delay, and collision events; and
- explain why acceptable errors depend on the people, setting, and consequences involved.

## Student workflow

1. **Sensor playground:** manipulate sensor properties and connect plots to statistics.
2. **Mission 1 — Characterize:** analyze a repeatable, individually assigned dataset and diagnose its dominant defect.
3. **Mission 2 — Filter and fuse:** record at least three configurations, including moving average and median, then select a configuration that satisfies quantitative criteria.
4. **Mission 3 — Decide:** test separate warehouse and assistive policies across seven noisy scenarios and justify their social and technical trade-offs.
5. **Final synthesis:** connect evidence from all three missions and generate a submission manifest.

## Run the lab

Python 3.10 or newer is recommended.

```powershell
cd week05_sensors_uncertainty
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

The app auto-saves locally. A student must use the same Course ID throughout because it deterministically selects their data. No network service or ROS installation is needed.

## Submission

This is an **individual lab**. Submit the complete `student_submission/` directory after the final page generates `manifest.json`. It contains:

- identity metadata and autosaved written responses;
- Mission 1 measurements, statistics, diagnosis, and plot;
- the complete Mission 2 experiment log, selected pipeline, time-series CSV, and plot;
- both Mission 3 policies, scenario metrics, and written analysis; and
- a file manifest for completeness checking.

The app does not create a ZIP automatically, so students can inspect every artifact before uploading the folder to the LMS.

## Instructor checks

Run the dependency-light smoke test:

```powershell
python app.py --smoke-test
```

Run the unit tests:

```powershell
python -m unittest discover -s tests -v
```

See `content/instructor_notes.md` for timing, facilitation, grading evidence, and parameter rationale.


## Required final reflection

After the technical work, complete the individual [final reflection](../FINAL_REFLECTION.md). Respond to any or all of the five prompts in 1–300 words. A blank response or a response over 300 words cannot finalize the submission. The app saves the response as `student_submission/final_reflection.md`, separate from technical syntheses and mission explanations.
