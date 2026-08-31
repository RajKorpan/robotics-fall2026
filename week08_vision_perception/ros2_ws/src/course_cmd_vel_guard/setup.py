from setuptools import find_packages, setup
package_name="course_cmd_vel_guard"
setup(name=package_name,version="0.1.0",packages=find_packages(),data_files=[("share/ament_index/resource_index/packages",["resource/"+package_name]),("share/"+package_name,["package.xml"])],install_requires=["setuptools"],zip_safe=True,maintainer="Robotics Course Staff",maintainer_email="robotics@example.edu",description="Velocity guard",license="MIT",entry_points={"console_scripts":["guard = course_cmd_vel_guard.guard:main"]})
