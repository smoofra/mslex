#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

version = "1.3.0"

setup(
    author="Lawrence D'Anna",
    author_email="larry@elder-gods.org",
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="shlex for windows",
    entry_points={
        "console_scripts": [
            "mslex-split=mslex:split_cli",
        ],
    },
    install_requires=[],
    license="Apache Software License 2.0",
    long_description=readme,
    include_package_data=True,
    keywords="mslex",
    name="mslex",
    package_data={"mslex": ["py.typed"]},
    packages=["mslex"],
    setup_requires=[],
    test_suite="tests",
    tests_require=[],
    url="https://github.com/smoofra/mslex",
    version=version,
)
