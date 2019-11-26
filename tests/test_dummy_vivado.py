#!/usr/bin/env python3

#
# Import built in packages
#
import pytest
import time
from subprocess import Popen

# import DUT
import pylinx


def test_xsct_dummy_vivado_init():
    vivado = pylinx.Vivado(executable='tclsh', args=[], prompt='% ')
    vivado.waitStartup()
    vivado.exit(force=True)
    vivado.exit()
    


def test_xsct_dummy_vivado_exit():
    vivado = pylinx.Vivado(executable='tclsh', args=[], prompt='% ')
    assert vivado.exit(force=False) == 0
    vivado.exit()


def test_vivado_do():
    vivado = pylinx.Vivado(executable='tclsh', args=[], prompt='% ')
    vivado.waitStartup()

    try:
        assert int(vivado.do('pid')) == vivado.pid()
        vivado.do('set a 5')
        vivado.do('set b 4')
        assert int(vivado.do('expr $a + $b')) == 9
        with pytest.raises(pylinx.PyXilException):
            vivado.do('expr $a + $c', errmsgs=[b'can\'t read "c": no such variable'])
    finally:
        assert vivado.exit() == 0

def test_vivado_vars():
    vivado = pylinx.Vivado(executable='tclsh', args=[], prompt='% ')
    vivado.waitStartup()

    try:
        vivado.set_var('foo', 42)
        vivado.set_var('bar', 58)
        assert vivado.get_var('foo') == '42'
        assert vivado.get_var('bar') == '58'
        
        vivado.set_var('res', '[expr $foo+$bar]')
        assert vivado.get_var('res') == '100'
        
        with pytest.raises(pylinx.PyXilException):
            vivado.get_var('c')
    finally:
        assert vivado.exit() == 0

