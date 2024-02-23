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
from abc import ABC, abstractmethod


class BaseDutNodeClass(ABC):

    @abstractmethod
    def reboot_dut(self):
        pass

    @abstractmethod
    def factory_reset_dut(self, stop_reset):
        """
        this fucntion will factory reset the DUT meaning the matter app will be restarted
        'stop_reset' parameter is used as boolean flag to stop the function from restarting matter app
        """
        pass

    @abstractmethod
    def start_matter_app(self):
        pass

    @abstractmethod
    def start_logging(self, file_name):
        pass

    @abstractmethod
    def stop_logging(self):
        pass


class BaseNodeDutConfiguration(object):

    def __init__(self, test_config) -> None:
        pass

    def get_dut_config(self):
        pass


def register_dut_object():
    pass
