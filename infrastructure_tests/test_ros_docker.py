import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROS_LABS = (
    "week01_ros_foundations",
    "week03_motion_frames_ai",
    "week06_slam_localization",
    "week08_vision_perception",
    "week09_planning_navigation",
    "week11_hri_evaluation",
)


class SharedRosEnvironmentTests(unittest.TestCase):
    def test_all_ros_labs_are_in_builder_and_launcher(self):
        builder = (ROOT / "docker/scripts/course-build-workspaces").read_text(encoding="utf-8")
        launcher = (ROOT / "docker/scripts/course-lab").read_text(encoding="utf-8")
        for lab in ROS_LABS:
            self.assertIn(lab, builder)
            self.assertIn(lab, launcher)
            self.assertTrue((ROOT / lab / "ros2_ws/src").is_dir())

    def test_domains_are_unique(self):
        launcher = (ROOT / "docker/scripts/course-lab").read_text(encoding="utf-8")
        domains = [int(value) for value in re.findall(r"domain=(\d+)", launcher)]
        self.assertEqual(len(domains), len(ROS_LABS))
        self.assertEqual(len(domains), len(set(domains)))

    def test_dockerfile_has_course_dependencies(self):
        dockerfile = (ROOT / "docker/Dockerfile").read_text(encoding="utf-8")
        for token in (
            "ros:jazzy-ros-base-noble",
            "ros-jazzy-desktop",
            "ros-jazzy-turtlebot3-gazebo",
            "ros-jazzy-navigation2",
            "ros-jazzy-slam-toolbox",
            "ros-jazzy-cv-bridge",
            "novnc",
            "x11vnc",
        ):
            self.assertIn(token, dockerfile)
        self.assertIn("getent passwd 1000", dockerfile)

    def test_windows_launcher_checks_native_exit_codes(self):
        launcher = (ROOT / "scripts/ros_course.ps1").read_text(encoding="utf-8")
        self.assertIn("Assert-DockerSuccess", launcher)
        self.assertIn("$LASTEXITCODE", launcher)

    def test_compose_binds_interfaces_to_localhost(self):
        compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
        self.assertIn('"127.0.0.1:6080:6080"', compose)
        self.assertIn('"127.0.0.1:8501:8501"', compose)
        self.assertIn(".:/workspace", compose)

    def test_ros_lab_docs_reference_shared_setup(self):
        for lab in ROS_LABS:
            readme = (ROOT / lab / "README.md").read_text(encoding="utf-8")
            self.assertIn("ROS_DOCKER_SETUP.md", readme, lab)

    def test_course_doctor_checks_each_workspace(self):
        doctor = (ROOT / "docker/scripts/course-doctor").read_text(encoding="utf-8")
        for lab in ROS_LABS:
            self.assertIn(lab, doctor)

    def test_ros_setup_is_sourced_before_nounset(self):
        scripts = [
            ROOT / "docker/scripts" / script
            for script in ("course-build-workspaces", "course-doctor", "course-lab")
        ]
        for lab in ROS_LABS:
            scripts.extend(sorted((ROOT / lab / "scripts").glob("*.sh")))
        for script in scripts:
            body = script.read_text(encoding="utf-8")
            if "source /opt/ros/jazzy/setup.bash" not in body:
                continue
            source_position = body.index("source /opt/ros/jazzy/setup.bash")
            nounset_matches = list(re.finditer(r"^set\s+-[^\n]*u[^\n]*$", body, re.MULTILINE))
            self.assertTrue(nounset_matches, str(script))
            nounset_position = nounset_matches[0].start()
            self.assertLess(source_position, nounset_position, str(script))
            workspace_sources = list(
                re.finditer(r"^\s*source\s+[^\n]*install/setup\.bash", body, re.MULTILINE)
            )
            for workspace_source in workspace_sources:
                self.assertLess(workspace_source.start(), nounset_position, str(script))

    def test_python_ros_packages_declare_ament_python(self):
        for lab in ROS_LABS:
            for setup_file in (ROOT / lab / "ros2_ws/src").glob("*/setup.py"):
                package_xml = (setup_file.parent / "package.xml").read_text(encoding="utf-8")
                self.assertIn("<build_type>ament_python</build_type>", package_xml, str(setup_file.parent))


if __name__ == "__main__":
    unittest.main()
