from setuptools import find_packages, setup


package_name = "course_lab_tools"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Course Instructor",
    maintainer_email="instructor@example.edu",
    description="Record safe timed motion trials.",
    license="Apache-2.0",
    entry_points={"console_scripts": ["timed_twist = course_lab_tools.timed_twist:main"]},
)

