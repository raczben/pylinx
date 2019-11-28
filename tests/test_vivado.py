#!/usr/bin/env python3

#
# Import built in packages
#
import pytest
import time
import os
import psutil

# import DUT
import pylinx

# The directory of this script file.
__here__ = os.path.dirname(os.path.realpath(__file__))

linux_vivado_path = "~/Xilinx/Vivado/2017.4/bin/vivado"
linux_vivado_path = os.path.expanduser(linux_vivado_path)

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

def test_xsct_dummy_vivado_exit():
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
        parent = psutil.Process(vivado.pid())
        children = parent.children(recursive=True)
        assert int(vivado.do('pid')) == children[1].pid
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
