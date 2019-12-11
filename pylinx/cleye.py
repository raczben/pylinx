import logging
import argparse
import os
import platform
import re
import traceback
import time
import sys

# The directory of this script file.
__here__ = os.path.dirname(os.path.realpath(__file__))
__pylinx__ = os.path.join(__here__, '..')
sys.path.insert(0, __pylinx__)

from pylinx import ScanStructure
from pylinx import VivadoHWServer
from pylinx import __version__
from pylinx import PylinxException

cleye_logo = r'''
       _                   
      | |                  
   ___| | ___ _   _  ___   
  / __| |/ _ \ | | |/ _ \  
 | (__| |  __/ |_| |  __/  
  \___|_|\___|\__, |\___|  
               __/ |       
              |___/                  
'''

logger = logging.getLogger('pylinx')


if "XILINX_VIVADO" in os.environ:
    if platform.system() == 'Windows':
        vivado_path = os.path.join(os.environ['XILINX_VIVADO'], 'bin', 'vivado.bat')
    else:
        vivado_path = os.path.join(os.environ['XILINX_VIVADO'], 'bin', 'vivado')
else:
    vivado_path = 'Cannot find out Vivado executable.'


def init(rx_hw_server_url="localhost:3121", tx_hw_server_url="localhost:3121"):
    logger.info('Spawning Vivado instances (TX/RX)')
    vivado_tx = VivadoHWServer(vivado_path, tx_hw_server_url, name='TX')
    vivado_rx = VivadoHWServer(vivado_path, rx_hw_server_url, name='RX')

    return vivado_tx, vivado_rx


def choose_link(vivado_tx, vivado_rx):
    """ Ask user to determine a HW link.

    :param vivado_tx: The TX device/SIO
    :param vivado_rx: The RX device/SIO
    :return: None
    """
    # Choose TX/RX device
    vivado_tx.choose_device()
    vivado_rx.choose_device()

    # Choose SIOs
    vivado_tx.choose_sio(createLink=False)
    vivado_rx.choose_sio()


def independent_finder(vivadoTX, vivadoRX, results_dir='runs'):
    """ Runs the optimizer algorithm.
    """
    TXDIFFSWING_values = [
        # "{269 mV (0000)}" ,
        # "{336 mV (0001)}" ,
        # "{407 mV (0010)}" ,
        # "{474 mV (0011)}" ,
        # "{543 mV (0100)}" ,
        # "{609 mV (0101)}" ,
        # "{677 mV (0110)}" ,
        # "{741 mV (0111)}" ,
        # "{807 mV (1000)}" ,
        # "{866 mV (1001)}" ,
        # "{924 mV (1010)}" ,
        "{973 mV (1011)}",
        "{1018 mV (1100)}",
        "{1056 mV (1101)}",
        "{1092 mV (1110)}",
        "{1119 mV (1111)}"
    ]

    TXPRE_values = [
        "{0.00 dB (00000)}",
        "{0.22 dB (00001)}",
        "{0.45 dB (00010)}",
        "{0.68 dB (00011)}",
        "{0.92 dB (00100)}",
        # "{1.16 dB (00101)}",
        # "{1.41 dB (00110)}",
        # "{1.67 dB (00111)}",
        # "{1.94 dB (01000)}",
        # "{2.21 dB (01001)}",
        # "{2.50 dB (01010)}",
        # "{2.79 dB (01011)}",
        # "{3.10 dB (01100)}",
        # "{3.41 dB (01101)}",
        # "{3.74 dB (01110)}",
        # "{4.08 dB (01111)}",
        # "{4.44 dB (10000)}",
        # "{4.81 dB (10001)}",
        # "{5.19 dB (10010)}",
        # "{5.60 dB (10011)}",
        # "{6.02 dB (10100)}",
        # "{6.02 dB (10101)}",
        # "{6.02 dB (10110)}",
        # "{6.02 dB (10111)}",
        # "{6.02 dB (11000)}",
        # "{6.02 dB (11001)}",
        # "{6.02 dB (11010)}",
        # "{6.02 dB (11011)}",
        # "{6.02 dB (11100)}",
        # "{6.02 dB (11101)}",
        # "{6.02 dB (11110)}",
        # "{6.02 dB (11111)}",
    ]

    TXPOST_values = [
        # "{0.00 dB (00000)}",
        # "{0.22 dB (00001)}",
        "{0.45 dB (00010)}",
        "{0.68 dB (00011)}",
        "{0.92 dB (00100)}",
        "{1.16 dB (00101)}",
        "{1.41 dB (00110)}",
        # "{1.67 dB (00111)}",
        # "{1.94 dB (01000)}",
        # "{2.21 dB (01001)}",
        # "{2.50 dB (01010)}",
        # "{2.79 dB (01011)}",
        # "{3.10 dB (01100)}",
        # "{3.41 dB (01101)}",
        # "{3.74 dB (01110)}",
        # "{4.08 dB (01111)}",
        # "{4.44 dB (10000)}",
        # "{4.81 dB (10001)}",
        # "{5.19 dB (10010)}",
        # "{5.60 dB (10011)}",
        # "{6.02 dB (10100)}",
        # "{6.47 dB (10101)}",
        # "{6.94 dB (10110)}",
        # "{7.43 dB (10111)}",
        # "{7.96 dB (11000)}",
        # "{8.52 dB (11001)}",
        # "{9.12 dB (11010)}",
        # "{9.76 dB (11011)}",
        # "{10.46 dB (11100)}",
        # "{11.21 dB (11101)}",
        # "{12.04 dB (11110)}",
        # "{12.96 dB (11111)}",
    ]

    RXTERM_values = [
        "{100 mV}",
        "{200 mV}",
        "{250 mV}",
        "{300 mV}",
        "{350 mV}",
        "{400 mV}",
        "{500 mV}",
        "{550 mV}",
        "{600 mV}",
        "{700 mV}",
        "{800 mV}",
        "{850 mV}",
        "{900 mV}",
        "{950 mV}",
        "{1000 mV}",
        "{1100 mV}",
    ]

    globalIteration = 1
    globalParameterSpace = {}
    globalParameterSpace["TXDIFFSWING"] = TXDIFFSWING_values  # [0::2]
    globalParameterSpace["TXPRE"] = TXPRE_values  # [0::2]
    globalParameterSpace["TXPOST"] = TXPOST_values  # [0::2]

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    try:
        read_results_tcl = open("read_results.tcl", "w")
        read_results_tcl.writelines('# Generated file by Cleye' + os.linesep)
        read_results_tcl.writelines('# Run this file to read all scan results into Vivado.' + os.linesep)
        read_results_tcl.writelines('' + os.linesep)
        scan_id = 0

        for i in range(globalIteration):
            for pName, pValues in globalParameterSpace.items():
                openAreas = []
                maxArea = 0
                txSioGt = '[get_hw_sio_gts {}]'.format(vivadoTX.sio)
                bestValue = vivadoTX.get_property(pName, txSioGt)

                for pValue in pValues:
                    scan_id += 1
                    # Test keyboard interrupt:
                    time.sleep(.01)

                    logger.info("Create scan ({} {})".format(pName, pValue))
                    vivadoTX.set_property(pName, pValue, txSioGt)
                    vivadoTX.do('commit_hw_sio ' + txSioGt)

                    checkValue = vivadoTX.get_property(pName, txSioGt)
                    if checkValue not in pValue:  # Readback does not contains brackets {}
                        logger.error("Something went wrong. Cannot set value {}  {} ".format(checkValue, pValue))

                    # set_property PORT.GTRXRESET 0 [get_hw_sio_gts  {localhost:3121/xilinx_tcf/Digilent/210203A2513BA/0_1_0/IBERT/Quad_113/MGT_X1Y0}]
                    # commit_hw_sio  [get_hw_sio_gts  {localhost:3121/xilinx_tcf/Digilent/210203A2513BA/0_1_0/IBERT/Quad_113/MGT_X1Y0}]

                    scan_name = "{}{}{}".format(i, pName, pValue)
                    scan_name = re.sub('\\W', '_', scan_name)
                    fname = os.path.join(results_dir, scan_name + '.csv')
                    read_results_tcl.writelines('read_hw_sio_scan ' + os.path.abspath(fname) + os.linesep)

                    # HORIZONTAL_INCREMENT: The greater value sorter scan time
                    hincr = 4
                    # VERTICAL_INCREMENT: The greater value sorter scan time
                    vincr = 4

                    # Specify the scan type. Valid types include:
                    #   *  1d_bathtub - Scan all horizontal sampling points through the 0 vertical
                    #      axis.
                    #   *  2d_full_eye - Scan all horizontal and vertical sampling points to
                    #      create an "eye".
                    scanType = "2d_full_eye"

                    # Link name is generated automatically, but we have only one link/Vivado instance, so wild globbing
                    # is good.
                    link_name = "*"

                    # Provide a brief description that acts as a label for the serial I/O analyzer scan. The description
                    # can be used to identify the <hw_sio_scan> object. For instance, you can identify the
                    # receiver port, so that when you are sweeping many ports you can keep track
                    # of which port the scan plot s for.
                    scan_description = scan_name

                    cmd = 'run_scan "{}" {} {} {} {} {}'.format(
                        fname, hincr, vincr, scanType, link_name, scan_description)
                    vivadoRX.do(cmd, errmsgs=['ERROR: ', 'args: should be'])

                    scan_struc = ScanStructure(fname)
                    open_area = scan_struc.get_open_area()
                    if open_area is None:
                        logger.error('open_area is None after reading file: ' + fname)

                    logger.info('open_area: {}  (parameters: {} = {})'.format(open_area, pName, pValue))
                    openAreas.append(open_area)

                    if open_area > maxArea:
                        maxArea = open_area
                        bestValue = pValue

                print("pName:  {}    bestParam:  {}".format(pName, bestValue))

                vivadoTX.set_property(pName, bestValue, txSioGt)
                vivadoTX.do('commit_hw_sio ' + txSioGt)
    finally:
        read_results_tcl.close()

def interactiveVivadoConsole(vivadoTX, vivadoRX):
    """ gives full control for user over the two (TX and RX) Vivado consoles.
    """

    print('Switching to VivadoRX')
    vivado = vivadoRX
    vivado.interact('')

    while True:
        cmd = input()
        if cmd.startswith('!'):
            # Cleye command
            cmd = cmd[1:].lower()
            if cmd == 'rx':
                print('Switching to VivadoRX')
                vivado = vivadoRX
                vivado.interact('')
            elif cmd == 'tx':
                print('Switching to VivadoTX')
                vivado = vivadoTX
                vivado.interact('')
            elif cmd in ['q', 'quit', 'exit']:
                print('Exiting to VivadoTX')
                vivadoTX.exit()
                print('Exiting to VivadoRX')
                vivadoRX.exit()
                break
        else:
            # Vivado command
            vivado.interact(cmd)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Eye Cleaner for Xilinx transceivers \r\n')

    parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)

    print(cleye_logo)

    try:
        vivado_tx, vivado_rx = init()
        try:
            vivado_tx.fetch_devices()

            choose_link(vivado_tx, vivado_rx)
            results_dir = 'runs'
            independent_finder(vivado_tx, vivado_rx, results_dir=results_dir)
            print('')
            print('All Script has been run.')
            print('Results stored in "' + results_dir + '" directory.')
            print('Switch to RX vivado console:')

        except KeyboardInterrupt:
            print('Exiting to VivadoTX')
            vivado_tx.exit()
            print('Exiting to VivadoRX')
            vivado_rx.exit()
        except PylinxException as ex:
            logger.error(str(ex))
            print(logger.level)
            traceback.print_exc()
            if logger.level <= logging.DEBUG:
                traceback.print_exc()
        except:
            logger.error('Unknown error!')
            traceback.print_exc()
        finally:
            interactiveVivadoConsole(vivado_tx, vivado_rx)
    finally:
        try:
            print('Exiting to VivadoTX')
            vivado_tx.exit()
        except:
            pass
        try:
            print('Exiting to VivadoRX')
            vivado_rx.exit()
        except:
            pass
