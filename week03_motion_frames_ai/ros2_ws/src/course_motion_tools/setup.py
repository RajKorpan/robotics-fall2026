from setuptools import find_packages, setup
name="course_motion_tools"
setup(name=name,version="0.1.0",packages=find_packages(),data_files=[("share/ament_index/resource_index/packages",[f"resource/{name}"]),(f"share/{name}",["package.xml"])],install_requires=["setuptools"],zip_safe=True,maintainer="Course Instructor",maintainer_email="instructor@example.edu",description="Motion and TF evidence tools",license="Apache-2.0",entry_points={"console_scripts":["run_sequence = course_motion_tools.run_sequence:main","frame_probe = course_motion_tools.frame_probe:main"]})
