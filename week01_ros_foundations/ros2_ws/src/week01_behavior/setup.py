from setuptools import find_packages, setup


package_name = "week01_behavior"

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
    maintainer="Student",
    maintainer_email="student@example.edu",
    description="Student obstacle-stop behavior.",
    license="Apache-2.0",
    entry_points={"console_scripts": ["obstacle_guard = week01_behavior.obstacle_guard:main"]},
)
