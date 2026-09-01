from __future__ import annotations

from pathlib import Path

from lab_config import LAB


PROMPTS = (
    "What did this activity make you think about regarding your own interests in robotics, computing, engineering, or related work?",
    "How did this activity affect your motivation to do similar kinds of work in the future?",
    "What value do you see in connecting technical or computing work with human, ethical, or societal considerations?",
    "What stood out to you about the activity, and why?",
    "Is there anything else you would like to share about your experience with the activity?",
)
RESPONSE_KEY = "final.course_reflection"
MAX_WORDS = 300


def word_count(text: str) -> int:
    return len(text.split())


def render_final_reflection(st) -> bool:
    st.subheader("Final reflection")
    st.write(
        "Write a short reflection of no more than 300 words. "
        "You may respond to any or all of the prompts below."
    )
    st.markdown("\n".join(f"{index}. {prompt}" for index, prompt in enumerate(PROMPTS, 1)))
    responses = dict(st.session_state.get("responses", {}))
    answer = st.text_area(
        "Your reflection",
        value=str(responses.get(RESPONSE_KEY, "")),
        key="field.final.course_reflection",
        height=220,
    )
    responses[RESPONSE_KEY] = answer
    st.session_state["responses"] = responses
    words = word_count(answer)
    st.caption(f"{words}/{MAX_WORDS} words")
    if words == 0:
        st.info("Complete the reflection before generating your submission.")
    elif words > MAX_WORDS:
        st.error(f"Shorten the reflection by {words - MAX_WORDS} words.")
    return 1 <= words <= MAX_WORDS


def write_final_reflection(st) -> Path:
    answer = str(st.session_state.get("responses", {}).get(RESPONSE_KEY, "")).strip()
    words = word_count(answer)
    if not 1 <= words <= MAX_WORDS:
        raise ValueError("Final reflection must contain 1–300 words.")
    root = Path(__file__).resolve().parents[1] / LAB.submission_directory
    root.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Final reflection",
        "",
        "Respond to any or all of these prompts:",
        "",
        *(f"{index}. {prompt}" for index, prompt in enumerate(PROMPTS, 1)),
        "",
        "## Response",
        "",
        answer,
        "",
        f"_Word count: {words}_",
        "",
    ]
    path = root / "final_reflection.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

