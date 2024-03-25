from .raspi_mutiadmin import Raspi

def create_dut_object(test_config):
    return Raspi(test_config)