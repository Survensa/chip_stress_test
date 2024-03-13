
import os
import sys
import io
import traceback
import yaml
from matter_qa.library.helper_libs.logger import log
DEFAULT_CONFIG_DIR = './Matter_QA/Configs/'

class TestConfig(object):
    def __init__(self, config_dict=None):
        if config_dict:
            for key, value in config_dict.items():
                if isinstance(value, dict):
                    setattr(self, key, TestConfig(value))
                else:
                    setattr(self, key, value)
        

def default_config_reader():
    try:
        config_yaml_file = os.path.join(DEFAULT_CONFIG_DIR, "configFile.yaml")
        if not os.path.exists(config_yaml_file):
            
            log.error("The config file does not exist! exiting now! ")
            sys.exit(0)
        with io.open(config_yaml_file, 'r') as f:
            test_config_dict = yaml.safe_load(f)
            test_config = TestConfig(test_config_dict)
        return test_config
    except Exception as e:
        log.error(e)
        traceback.print_exc()