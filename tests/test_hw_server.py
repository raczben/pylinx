#!/usr/bin/env python3

#
# Import built in packages
#
import pytest
import platform
import os
import psutil

# import DUT
import pylinx

# The directory of this script file.
__here__ = os.path.dirname(os.path.realpath(__file__))

# set XILINX_VIVADO=C:\Xilinx\Vivado\2017.4\

if "XILINX_VIVADO" in os.environ:
    if platform.system() == 'Windows':
        linux_vivado_path = os.path.join(os.environ['XILINX_VIVADO'], 'bin', 'vivado.bat')
    else:
        linux_vivado_path = os.path.join(os.environ['XILINX_VIVADO'], 'bin', 'vivado')
else:
    linux_vivado_path = 'Cannot find out Vivado executable.'


def valid_platform():
    """Vivado is not installed on Travis.
    """
    if "TRAVIS" in os.environ and os.environ["TRAVIS"] == "true":
        return False
    return True


def test_hw_server_init():
    if not valid_platform():
        pytest.skip("unsupported platform")

    vivado = pylinx.VivadoHWServer(linux_vivado_path)
    vivado.exit(force=True)
    vivado.exit()


def test_fetch_devices():
    if not valid_platform():
        pytest.skip("unsupported platform")

    vivado = pylinx.VivadoHWServer(linux_vivado_path)
    devices = vivado.get_devices()
    assert devices == vivado.get_devices()
    vivado.exit()

