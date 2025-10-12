"""
@author: Cem Akpolat
@created by cemakpolat at 2021-12-29
"""

from setuptools import find_packages, setup

NAME = "Optabackend"
DESCRIPTION = "Opta Backend Service"
URL = ""
EMAIL = "akpolatcem@statsfabrik.com, sahinel@statsfabrik.com"
AUTHOR = "Cem Akpolat"
REQUIRES_PYTHON = ">=3.8.0"
VERSION = "0.1.0"

# Required packages for running the project
REQUIRED = ["flask", "docker", "werkzeug", "flask_cors"]
# Extra packages
EXTRAS = {}

# Main setup config
setup(
    name=NAME,
    # package_dir={'': 'src'},
    version="0.1.0",
    description=DESCRIPTION,
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=["src"],
    # packages=find_packages(),
    # packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license="",
)
