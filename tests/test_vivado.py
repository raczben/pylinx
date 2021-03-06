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
    '''Vivado is not installed on Travis.
    '''
    if "TRAVIS" in os.environ and os.environ["TRAVIS"] == "true":
        return False
    return True


def test_vivado_init():
    if not valid_platform():
        pytest.skip("unsupported platform")

    vivado = pylinx.Vivado(linux_vivado_path)
    vivado.exit(force=True)
    vivado.exit()


def test_xsct_vivado_exit():
    if not valid_platform():
        pytest.skip("unsupported platform")

    vivado = pylinx.Vivado(linux_vivado_path)
    assert vivado.exit(force=False) == 0
    vivado.exit()


def test_vivado_do():
    if not valid_platform():
        pytest.skip("unsupported platform")

    vivado = pylinx.Vivado(linux_vivado_path)

    try:
        assert int(vivado.do('pid')) == vivado.pid()
        vivado.do('set a 5')
        vivado.do('set b 4')
        assert int(vivado.do('expr $a + $b')) == 9
        with pytest.raises(pylinx.PylinxException):
            vivado.do('expr $a + $c', errmsgs=['can\'t read "c": no such variable'])

        assert vivado.do('puts hello', prompt='% ') == 'hello'
        assert vivado.do('puts world', timeout=1) == 'world'
    except:
        print(vivado.last_cmds)
        print(vivado.last_befores)
        raise
    finally:
        assert vivado.exit() == 0
