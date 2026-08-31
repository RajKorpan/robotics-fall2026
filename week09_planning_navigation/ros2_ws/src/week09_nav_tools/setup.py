from glob import glob
from setuptools import find_packages, setup

package_name = "week09_nav_tools"
setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Robotics Course Staff",
    maintainer_email="instructor@example.edu",
    description="Week 9 Nav2 evidence tools",
    license="MIT",
    entry_points={"console_scripts": [
        "plan_probe = week09_nav_tools.plan_probe:main",
        "navigate_probe = week09_nav_tools.navigate_probe:main",
        "social_monitor = week09_nav_tools.social_monitor:main",
    ]},
)

