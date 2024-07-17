from setuptools import setup
from setuptools import find_packages
import os

this_dir = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(this_dir, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Set of commands for github
setup(
    name="instruments",
    version="0.1.dev",
    description="Control of Tandem PV Instruments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Sean P. Dunfield, Andrew K. Hoeppner, Berkelley Gonzalez",
    author_email="sdunfield@tandempv.com, ahoeppner@tandempv.com, bgonzalez@tandempv.com",
    download_url="https://github.com/sean-dunfield-tpv/instruments",
    license="MIT",
    install_requires=[
        "pandas",
        "numpy",
        "pyvisa",
        "pyserial",
        "matplotlib",
        "pyyaml",
        "pyqt5",
        "datetime",
    ],
    packages=find_packages(),
    package_data={},
    include_package_data=True,
    keywords=[
        "materials",
        "science",
        "machine",
        "automation",
        "photovoltaic",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
