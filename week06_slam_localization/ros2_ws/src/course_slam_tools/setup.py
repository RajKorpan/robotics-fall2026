from setuptools import find_packages, setup
package_name = "course_slam_tools"
setup(name=package_name, version="0.1.0", packages=find_packages(), data_files=[
    ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
    ("share/" + package_name, ["package.xml"]),
    ("share/" + package_name + "/launch", ["launch/mapping.launch.py", "launch/localization.launch.py"]),
], install_requires=["setuptools"], zip_safe=True, maintainer="Robotics Course Staff", maintainer_email="robotics@example.edu", description="Week 6 SLAM tools", license="MIT", entry_points={"console_scripts": ["scan_degrader = course_slam_tools.scan_degrader:main", "localization_recorder = course_slam_tools.localization_recorder:main"]})
