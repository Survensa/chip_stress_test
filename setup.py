#
#
#  Copyright (c) 2023 Project CHIP Authors
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
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
    packages=find_packages(include=('MatterQA/*')),
    install_requires=requirements,
    )
