#!/usr/bin/env python3

#
# Import built in packages
#
import pytest
import time
from subprocess import Popen
import os

# import DUT
import pylinx

# The directory of this script file.
__here__ = os.path.dirname(os.path.realpath(__file__))


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
            
        assert vivado.do('puts hello', prompt='% ') == 'hello'
        assert vivado.do('puts world', timeout=1) == 'world'
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
            
        assert vivado.set_var('hello', 'world', prompt='% ', timeout=1)
        assert vivado.get_var('hello', prompt='% ', timeout=1) == 'world'
    finally:
        assert vivado.exit() == 0


def test_vivado_properties():
    vivado = pylinx.Vivado(executable='tclsh', args=[], prompt='% ')
    vivado.waitStartup()

    try:
        dummy_prop = os.path.abspath(os.path.join(__here__, 'dummy_vivado.tcl'))
        vivado.do('source ' + dummy_prop)
        vivado.set_property('freqency', 100, 'sys_clock')
        assert vivado.get_property('freqency', 'sys_clock') == '100'
        
    finally:
        assert vivado.exit() == 0

