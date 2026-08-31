from __future__ import annotations

import os

from lab.navigation import set_stage
from lab_config import LAB


def render_instructor_controls(st) -> None:
    with st.sidebar.expander("Instructor controls"):
        expected = os.environ.get(LAB.instructor_password_env, "instructor")
        password = st.text_input("Password", type="password", key="instructor_password")
        if password != expected:
            st.caption("Enter the instructor password to unlock navigation.")
            return
        destination = st.selectbox("Jump to stage", LAB.stages)
        if st.button("Go", key="instructor_jump"):
            set_stage(st, destination)

