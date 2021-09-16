import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aws-virtual-waiting-room-common",
    version="1.0.0",
    author="AWS Solutions PDX",
    author_email="aws-solutions-pdx@amazon.com",
    description="Common Python modules for AWS Virtual Waiting Room",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aws-solutions/aws-virtual-waiting-room",
    project_urls={
        "Bug Tracker":
        "https://github.com/aws-solutions/aws-virtual-waiting-room/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(where="."),
    python_requires=">=3.8",
    install_requires=[
        'bleach',
    ])
