from glob import glob
from setuptools import find_packages, setup
name="course_robot_bringup"
setup(name=name,version="0.1.0",packages=find_packages(),data_files=[("share/ament_index/resource_index/packages",[f"resource/{name}"]),(f"share/{name}",["package.xml"]),(f"share/{name}/launch",glob("launch/*.launch.py"))],install_requires=["setuptools"],zip_safe=True,maintainer="Course Instructor",maintainer_email="instructor@example.edu",description="Week 3 bringup",license="Apache-2.0")
