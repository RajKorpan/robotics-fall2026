from setuptools import find_packages, setup
name="week03_pattern"
setup(name=name,version="0.1.0",packages=find_packages(),data_files=[("share/ament_index/resource_index/packages",[f"resource/{name}"]),(f"share/{name}",["package.xml"])],install_requires=["setuptools"],zip_safe=True,maintainer="Student",maintainer_email="student@example.edu",description="AI-assisted motion pattern",license="Apache-2.0",entry_points={"console_scripts":["pattern_node = week03_pattern.pattern_node:main"]})
