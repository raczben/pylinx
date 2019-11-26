#!/usr/bin/env python3

#
# Import built in packages
#
import pytest
import time
from subprocess import Popen

# inport DUT
import pylinx


def test_xsct_dummy_server():
    xsct_server = pylinx.XsctServer()
    xsct_server._start_dummy_server()
    time.sleep(.1)
    xsct_server.stop_server()
    
    
def test_xsct():
    xsct_server = pylinx.XsctServer()
    try:
        xsct_server._start_dummy_server()
        time.sleep(.1)
        xsct = pylinx.Xsct()
        
        assert int(xsct.do('pid')) == xsct_server.pid()
        xsct.do('set a 5')
        xsct.do('set b 4')
        assert int(xsct.do('expr $a + $b')) == 9
        with pytest.raises(pylinx.PyXilException):
            xsct.do('expr $a + $c')

        xsct.send('exit')
        xsct.close()
    finally:
        xsct_server.stop_server()