"""
Matter QA Python Module install
"""
import imp
import os

from setuptools import find_packages, setup

DIR_PATH = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(DIR_PATH, 'requirements.txt')) as f:
    requirements = f.read().splitlines()

setup(
    name='MatterQA',
    version='1.0.0',
    description='Matter Automated QA tests',
    long_description='This python modules contains Matter Functional and Reliability Tests',
    packages=find_packages(include=('MatterQA/*'))
    )
