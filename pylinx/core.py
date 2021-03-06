#!/usr/bin/env python3

#
# Import built in packages
#
import logging
import platform
import os
import time
import socket
import subprocess
import signal
import psutil
from .util import setup_logger
from .util import PylinxException
import re

# Import 3th party modules:
#  - wexpect/pexpect to launch ant interact with subprocesses.
if platform.system() == 'Windows':
    import wexpect as expect

    print(expect.__version__)
else:  # Linux
    import pexpect as expect

# The directory of this script file.
__here__ = os.path.dirname(os.path.realpath(__file__))

#
# Get the logger (util.py has sets it)
#
setup_logger()
logger = logging.getLogger('pylinx')

# xsct_line_end is the line endings in the XSCT console. It doesn't depend on the platform. It is
# always Windows-style \\r\\n.
xsct_line_end = '\r\n'

# The default host and port.
HOST = '127.0.0.1'  # Standard loop-back interface address (localhost)
PORT = 4567


class XsctServer:
    """The controller of the XSCT server application. This is an optional feature. The commands will
    be given to the client.
    """

    def __init__(self, xsct_executable=None, port=PORT, verbose=False):
        """ Initialize the Server object.
        
        :param xsct_executable: The full-path to the XSCT/XSDB executable
        :param port: TCP port where the server should be started
        :param verbose: True: prints the XSCT's stdout to python's stdout.
        """
        self._xsct_server = None
        if (xsct_executable is not None) and (port is not None):
            self.start_server(xsct_executable, port, verbose)

    def start_server(self, xsct_executable=None, port=PORT, verbose=False):
        """Starts the server.

        :param xsct_executable: The full-path to the XSCT/XSDB executable
        :param port: TCP port where the server should be started
        :param verbose: True: prints the XSCT's stdout to python's stdout.
        :return: None
        """
        if (xsct_executable is None) or (port is None):
            raise ValueError("xsct_executable and port must be non None.")
        start_server_command = 'xsdbserver start -port {}'.format(port)
        start_command = '{} -eval "{}" -interactive'.format(xsct_executable, start_server_command)
        self._launch_child(start_command)

    def _start_dummy_server(self):
        """Starts a dummy server, just for test purposes.
        
        :return: None
        """
        dummy_executable = os.path.abspath(os.path.join(__here__, 'dummy_xsct.tcl'))
        start_command = ['tclsh', dummy_executable]
        self._launch_child(start_command)

    def _launch_child(self, start_command, verbose=False):
        logger.info('Starting xsct server: %s', start_command)
        if verbose:
            stdout = None
        else:
            stdout = open(os.devnull, 'w')
        self._xsct_server = subprocess.Popen(start_command, stdout=stdout)
        logger.info('xsct started with PID: %d', self._xsct_server.pid)

    def stop_server(self, wait=True):
        """Kills the server.

        :param wait: Wait for complete kill, or just send kill signals.
        :return: None
        """
        if not self._xsct_server:
            logger.debug('The server is not started or it has been killed.')
            return

        poll = self._xsct_server.poll()
        if poll is None:
            logger.debug("The server is alive, let's kill it.")

            # Kill all child process the XSCT starts in a terminal.
            current_process = None
            try:
                current_process = psutil.Process(self._xsct_server.pid)
                children = current_process.children(recursive=True)
                children.append(current_process)
                for child in reversed(children):
                    logger.debug("Killing child with pid: %d", child.pid)
                    os.kill(child.pid, signal.SIGTERM)  # or signal.SIGKILL
            except psutil._exceptions.NoSuchProcess as e:
                logger.debug('psutil.NoSuchProcess process no longer exists.')
            if wait:
                poll = self._xsct_server.poll()
                while poll is None:
                    logger.debug("The server is still alive, wait for it.")
                    time.sleep(.1)
                    poll = self._xsct_server.poll()

            self._xsct_server = None

        else:
            logger.debug("The server is not alive, return...")

    def pid(self):
        return self._xsct_server.pid


class Xsct:
    """The XSCT client class. This communicates with the server and sends commands.
    """

    def __init__(self, host=HOST, port=PORT):
        """Initializes the client object.

        :param host: the URL of the machine address where the XSDB server is running.
        :param port: the port of the the XSDB server is running.
        """
        self._socket = None

        if host is not None:
            self.connect(host, port)

    def connect(self, host=HOST, port=PORT, timeout=10):
        """Connect to the xsdbserver

        :param host: Host machine where the xsdbserver is running.
        :param port: Port of the xsdbserver.
        :param timeout: Set a timeout on blocking socket operations. The value argument can be a non-negative float
        expressing seconds.
        :return: None
        """
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((host, port))
        if timeout is not None:
            self._socket.settimeout(timeout)
        logger.info('Connected to: %s...', repr((host, port)))

    def close(self):
        """Closes the connection

        :return: None
        """
        self._socket.close()

    def send(self, msg):
        """Sends a simple message to the xsdbserver through the socket. Note, that this method don't appends
        line-endings. It just sends natively the message. Use `do` instead.

        :param msg: The message to be sent.
        :return: Noting
        """
        if isinstance(msg, str):
            msg = msg.encode()
        logger.debug('Sending message: %s ...', repr(msg))
        self._socket.sendall(msg)

    def recv(self, bufsize=1024, timeout=None):
        """Receives the answer from the server. Not recommended to use it natively. Use `do`

        :param bufsize:The maximum amount of data to be received at once is specified by bufsize.
        :param timeout:
        :return:
        """
        if timeout is not None:
            self._socket.settimeout(timeout)
        ans = ''
        while True:
            data = self._socket.recv(bufsize)
            logger.debug('Data received: %s ...', repr(data))
            ans += data.decode("utf-8")
            ans = ans.split(xsct_line_end)
            if len(ans) > 1:
                return ans[0]

    def do(self, command):
        """The main function of the client. Sends a command and returns the return value of the command.

        :param command:
        :return:
        """
        command += xsct_line_end
        logger.info('Sending command: %s ...', repr(command))
        self.send(command)
        ans = self.recv()
        if ans.startswith('okay'):
            return ans[5:]
        if ans.startswith('error'):
            raise PylinxException(ans[6:])
        raise PylinxException('Illegal start-string in protocol. Answer is: ' + ans)


default_vivado_prompt = 'Vivado% '


class Vivado:
    """Vivado is a native interface towards the Vivado TCL console. You can run TCL commands in it
    using do() method. This is a quasi state-less class
    """

    def __init__(self, executable, args=None, name='Vivado_01',
                 prompt=default_vivado_prompt, timeout=10, encoding="utf-8", wait_startup=True):
        self.child_proc = None
        self.name = name
        self.prompt = prompt
        self.timeout = timeout
        self.encoding = encoding
        self.last_cmds = []
        self.last_befores = []
        self.last_prompts = []

        if args is None:
            args = ['-mode', 'tcl']

        if executable is not None:  # None is fake run
            logger.info('Spawning Vivado: ' + executable + str(args))
            self.child_proc = expect.spawn(executable, args)

        if wait_startup:
            self.wait_startup()

    def wait_startup(self, **kwargs):
        self.do(cmd=None, **kwargs)

    def do(self, cmd, prompt=None, timeout=None, wait_prompt=True, errmsgs=[], encoding="utf-8",
           native_answer=False):
        """ do a simple command in Vivado console
        :rtype: str
        """
        if self.child_proc.terminated:
            logger.error('The process has been terminated. Sending command is not possible.')
            raise PylinxException('The process has been terminated. Sending command is not possible.')

        if cmd is not None:
            logger.debug('Sending command: ' + str(cmd))
            if platform.system() == 'Windows':
                self.child_proc.sendline(cmd)
            else:
                self.child_proc.sendline(cmd.encode())
        if prompt is None:
            prompt = self.prompt
        if timeout is None:
            timeout = self.timeout
        if encoding is None:
            encoding = self.encoding
        if wait_prompt:
            self.child_proc.expect(prompt, timeout=timeout)
            logger.debug("before: " + repr(self.child_proc.before))
            self.last_cmds.append(cmd)
            
            if platform.system() == 'Windows':
                before = self.child_proc.before
                prompt = self.child_proc.after
            else:
                before = self.child_proc.before.decode(encoding)
                prompt = self.child_proc.after.decode(encoding)
            self.last_befores.append(before)
            self.last_prompts.append(prompt)
            for em in errmsgs:
                if isinstance(em, str):
                    em = re.compile(em)
                if em.search(before):
                    logger.error('during running command: {}, before: {}'.format(cmd, before))
                    raise PylinxException('during running command: {}, before: {}'.format(cmd, before))

            if native_answer:
                return before
            else:
                # remove first line, which is always empty
                ret = os.linesep.join(before.split(xsct_line_end)[1:-1])
                # print(repr(before.split(xsct_line_end)))
                return ret.rstrip()

        return None

    def interact(self, cmd=None, **kwargs):
        if cmd is not None:
            self.do(cmd, **kwargs)
        before_to_print = os.linesep.join(self.last_befores[-1].split(xsct_line_end)[1:])
        print(before_to_print, end='')
        print(self.last_prompts[-1], end='')

    def get_var(self, varname, **kwargs):
        no_var_msg = 'can\'t read "{}": no such variable'.format(varname)
        errmsgs = [re.compile(no_var_msg)]
        command = 'puts ${}'.format(varname)
        ans = self.do(command, errmsgs=errmsgs, **kwargs)

        return ans

    def set_var(self, varname, value, **kwargs):
        command = 'set {} {}'.format(varname, value)

        ans = self.do(command, **kwargs)

        return ans

    def get_property(self, propName, objectName, **kwargs):
        """ does a get_property command in vivado terminal.

        It fetches the given property and returns it.
        """
        cmd = 'get_property {} {}'.format(propName, objectName)
        return self.do(cmd, **kwargs).strip()

    def set_property(self, propName, value, objectName, **kwargs):
        """ Sets a property.
        """
        cmd = 'set_property {} {} {}'.format(propName, value, objectName)
        self.do(cmd, **kwargs)

    def pid(self):
        parent = psutil.Process(self.child_proc.pid)
        children = parent.children(recursive=True)
        if len(children) == 0:
            return self.child_proc.pid
        for child in children:
            if re.match(".*vivado.*", child.name(), re.I):
                return child.pid
        raise PylinxException('Unknown pid')

    def exit(self, force=False, **kwargs):
        logger.debug('start')
        if self.child_proc is None:
            return None
        if self.child_proc.terminated:
            logger.warning('This process has been terminated.')
            return None
        else:
            if force:
                return self.child_proc.terminate()
            else:
                self.do('exit', wait_prompt=False, **kwargs)
                return self.child_proc.wait()


class VivadoHWServer(Vivado):
    """VivadoHWServer adds hw_server dependent handlers for the Vivado class.
    """

    '''allDevices is a static variable. Its stores all the devices for all hardware server. The indexes
    are the urls and the values are lists of the available hardware devices. The default behaviour
    is the following: One key is "localhost:3121" (which is the default hw server) and this key
    indexes a list with all local devices (which are normally includes two devices).
    See get_devices() and fetchDevices for more details.'''
    allDevices = {}  # type: dict[str, list]

    def __init__(self, executable, hw_server_url='localhost:3121', wait_startup=True, full_init=True, **kwargs):
        self.hw_server_url = hw_server_url
        self.sio = None
        self.sioLink = None
        self.hw_server_url = hw_server_url
        super(VivadoHWServer, self).__init__(executable, wait_startup=wait_startup, **kwargs)

        if full_init:
            assert wait_startup

            hw_server_tcl = os.path.join(__here__, 'hw_server.tcl')
            hw_server_tcl = hw_server_tcl.replace(os.sep, '/')
            self.do('source ' + hw_server_tcl, errmsgs=['no such file or directory'])
            self.do('init ' + hw_server_url)

    def fetch_devices(self, force=True):
        """_fetchDevices go thorugh the blasters and fetches all the hw devices and stores into the
        allDevices dict. Private method, use get_devices, which will fetch devices if it needed.
        """

        if force or self.get_devices(auto_fetch=False) is None:
            logger.info('Exploring target devices (fetch_devices: this can take a while)')
            self.do('set devices [fetch_devices]', errmsgs=["Labtoolstcl 44-133", "No target blaster found"])
            try:
                devices = self.get_var('devices')
            except PylinxException as ex:
                raise PylinxException('No target device found. Please connect and power up your device(s)')

            # Get a list of all devices on all target.
            # Remove the brackets. (fetch_devices returns lists.)
            logger.debug("devices: " + str(devices))
            devices = re.findall(r'\{(.+?)\}', devices)
            VivadoHWServer.allDevices[self.hw_server_url] = devices
            logger.debug("allDevices: " + str(VivadoHWServer.allDevices))

        return self.get_devices(auto_fetch=False)

    def get_devices(self, auto_fetch=True, hw_server_url=None):
        """Returns the hardware devices. auto_fetch fetches automatically the devices, if they have
        not fetched yet."""

        if hw_server_url is None:
            hw_server_url = self.hw_server_url
        try:
            return VivadoHWServer.allDevices[hw_server_url]
        except KeyError:
            if auto_fetch and hw_server_url == self.hw_server_url:
                return self.fetch_devices(force=True)
            raise PylinxException('KeyError: No devices has fetched yet. Use fetchDevices() first!')

    def choose_device(self, **kwargs):
        """ set the hw target (blaster) and device (FPGA) for TX and RX side.
        """
        # Print devices to user to choose from them.
        devices = self.get_devices()

        if len(devices) < 1:
            raise PylinxException("There is no devices! Please use fetch_devices() first!")

        for i, dev in enumerate(devices):
            print(str(i) + ' ' + dev)

        device_id = input('Choose device for {} (Give a number): '.format(self.name))
        device_id = int(device_id)
        device = devices[device_id]

        errmsgs = ['DONE status = 0', 'The debug hub core was not detected.']
        self.do('set_device ' + device, errmsgs=errmsgs, **kwargs)

    def choose_sio(self, createLink=True, **kwargs):
        """ Set the transceiver channel for TX/RX side.
        """
        self.do('', **kwargs)
        errmsgs = ['No matching hw_sio_gts were found.']
        sios = self.do('get_hw_sio_gts', errmsgs=errmsgs, **kwargs).strip()
        sios = sios.split(' ')
        for i, sio in enumerate(sios):
            print(str(i) + ' ' + sio)
        print('Print choose a SIO for {} side (Give a number): '.format(self.name), end='')
        sio_id = int(input())
        self.sio = sios[sio_id]

        if createLink:
            self.do('create_link ' + self.sio, **kwargs)

    def reset_gt(self):
        resetName = 'PORT.GT{}RESET'.format(self.name)
        self.set_property(resetName, '1', '[get_hw_sio_gts  {{}}]'.format(self.sio))
        self.commit_hw_sio()
        self.set_property(resetName, '0', '[get_hw_sio_gts  {{}}]'.format(self.sio))
        self.commit_hw_sio()

    def commit_hw_sio(self):
        self.set_property('commit_hw_sio' '0' '[get_hw_sio_gts  {{}}]'.format(self.sio))
