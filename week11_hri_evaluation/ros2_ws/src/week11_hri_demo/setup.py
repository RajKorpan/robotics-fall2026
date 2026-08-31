from glob import glob
from setuptools import find_packages, setup

package_name = "week11_hri_demo"
setup(name=package_name, version="0.1.0", packages=find_packages(), data_files=[("share/ament_index/resource_index/packages", ["resource/"+package_name]), ("share/"+package_name, ["package.xml"]), ("share/"+package_name+"/launch", glob("launch/*.launch.py")), ("share/"+package_name+"/config", glob("config/*.yaml"))], install_requires=["setuptools"], zip_safe=True, maintainer="Robotics Course Staff", maintainer_email="instructor@example.edu", description="Week 11 HRI prototype", license="MIT", entry_points={"console_scripts":["interaction_demo = week11_hri_demo.interaction_demo:main", "event_recorder = week11_hri_demo.event_recorder:main"]})

