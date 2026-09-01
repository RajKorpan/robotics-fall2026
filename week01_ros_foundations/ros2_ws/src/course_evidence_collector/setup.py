from setuptools import find_packages, setup


package_name = "course_evidence_collector"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    tests_require=["pytest"],
    zip_safe=True,
    maintainer="Course Instructor",
    maintainer_email="instructor@example.edu",
    description="Collect machine-readable evidence from a ROS graph.",
    license="Apache-2.0",
    entry_points={"console_scripts": ["evidence_collector = course_evidence_collector.collector:main"]},
)
