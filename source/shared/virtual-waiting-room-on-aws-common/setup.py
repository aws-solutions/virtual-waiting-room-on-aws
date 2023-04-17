"""
This module sets up the metadata for the waiting room common library.
"""

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="virtual-waiting-room-on-aws-common",
    version="1.1.1",
    author="AWS Solutions PDX",
    author_email="aws-solutions-pdx@amazon.com",
    description="Common Python modules for Virtual Waiting Room on AWS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aws-solutions/virtual-waiting-room-on-aws",
    project_urls={
        "Bug Tracker":
        "https://github.com/aws-solutions/virtual-waiting-room-on-aws/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(where="."),
    python_requires=">=3.8",
    install_requires=[
        'bleach~=4.1.0',
    ])
