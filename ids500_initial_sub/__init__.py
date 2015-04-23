#!/usr/bin/env python3
"""IDS-500 Initial Subboard Test Program."""

import os
import logging
import time
import serial
import queue
import threading

import tester
from . import support
from . import limit
import share.programmer
import share.ids500


LIMIT_DATA = limit.DATA

# Serial port for the PIC.
_PIC_PORT = {'posix': '/dev/ttyUSB0',
             'nt': r'COM1',
             }[os.name]

_PIC_HEX = 'Main 1A.hex'

_HEX_DIR = {'posix': '/opt/setec/ate4/ids500_initial_sub',
            'nt': r'C:\TestGear\TcpServer\ids500_initial_sub',
            }[os.name]


# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class MockSerial():

    """Simulated serial port for testing."""

    def __init__(self, port=None, baudrate=9600, bytesize=8, parity='N',
                 stopbits=1, timeout=None, xonxoff=False, rtscts=False,
                 writeTimeout=None, dsrdtr=False, interCharTimeout=None):
        """Create internal data storage queue."""
        # Queue to hold data to be read by read()
        self.in_queue = queue.Queue()
        # Queue to hold data written by write()
        self.out_queue = queue.Queue()
        # Control of read() enable
        self._enable = threading.Event()
        self._enable.set()

    def put(self, data):
        """Put data into the read-back queue."""
        self.in_queue.put(data)

    def get(self):
        """Get data from the written-out queue."""
        if not self.out_queue.empty():
            data = self.out_queue.get()
        else:
            data = b''
        return data

    def flush(self):
        """Flush both input and output queues."""
        self.flushInput()
        self.flushOutput()

    def flushInput(self):
        """Flush input queue."""
        while not self.in_queue.empty():
            self.in_queue.get()

    def flushOutput(self):
        """Flush output queue."""
        while not self.out_queue.empty():
            self.out_queue.get()

    def enable(self):
        """Enable reading of the read-back queue."""
        self._enable.set()

    def disable(self):
        """Disable reading of the read-back queue."""
        self._enable.clear()

    def read(self, size=1):
        """A non-blocking read.

        @return bytes.

        """
# FIXME: Honour the size argument
        if self._enable.is_set() and not self.in_queue.empty():
            data = self.in_queue.get()
        else:
# FIXME: Should we use the timeout from the call to __init__() ?
            time.sleep(0.1)
            data = b''
        return data

    def write(self, data):
        """Write data bytes to the written-out queue."""
        self.out_queue.put(data)


class Main(tester.TestSequence):

    """IDS-500 Initial Subboard Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        _isMicro, _isSyn, _isAux, _isBias, _isBus = {
            'IDS500-INI-MICRO':  (True,  False, False, False, False),
            'IDS500-INI-SYN':    (False,  True, False, False, False),
            'IDS500-INI-AUX':    (False,  False, True, False, False),
            'IDS500-INI-BIAS':   (False,  False, False, True, False),
            'IDS500-INI-BUS':    (False,  False, False, False, True),
            }[selection.name]
        self._logger.debug(
            'Initial TestType: Micro %s, Synbuck %s, Aux %s,'
            ' Bias %s, Bus %s',
            _isMicro, _isSyn, _isAux, _isBias, _isBus)
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerUp', self._step_pwrup_micro, None, _isMicro),
            ('PowerUp', self._step_pwrup_aux, None, _isAux),
            ('KeySw1', self._step_key_switch1, None, _isAux),
            ('Program', self._step_program, None, _isMicro),
            ('Comms', self._step_comms, None, _isMicro),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        if self._fifo:
            self._pic_ser = MockSerial()
        else:
            self._pic_ser = serial.Serial(port=_PIC_PORT,
                                          baudrate=19200, timeout=0.1)
        self._picdev = share.ids500.Console(self._pic_ser)
        global d
        d = support.LogicalDevices(self._devices)
        global s
        s = support.Sensors(d, self._limits, self._picdev)
        global m
        m = support.Measurements(s, self._limits)
        global t
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        self._pic_ser.close()
        global m
        m = None
        global d
        d = None
        global s
        s = None
        global t
        t = None

    def safety(self, run=True):
        """Make the unit safe after a test."""
        self._logger.info('Safety(%s)', run)
        if run:
            # Reset Logical Devices
            d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_pwrup_micro(self):
        """Apply input DC and measure."""
        self.fifo_push(((s.oVsec5VuP, 5.0), ))
        t.pwrup_micro.run()

    def _step_program(self):
        """Program the PIC micro."""
        self._logger.info('Start PIC programmer')
        d.rla_Prog.set_on()
        pic = share.programmer.ProgramPIC(
            hexfile=_PIC_HEX, working_dir=_HEX_DIR, device_type='18F4520',
            sensor=s.oMirPIC, fifo=self._fifo)
        # Wait for programming completion & read results
        pic.read()
        d.rla_Prog.set_off()
        m.pgmPIC.measure()

    def _step_comms(self):
        """Communicate with the PIC console."""
        self._picdev._flush()
        if self._fifo:
            self._pic_ser.put(b'I, 1, 2,Software Revision\r\n')
        m.pic_SwRev.measure()
        if self._fifo:
            self._pic_ser.put(b'D, 16, 25,MICRO Temp.(C)\r\n')
        m.pic_MicroTemp.measure()

    def _step_pwrup_aux(self):
        """Apply input DC and measure."""
        self.fifo_push(
            ((s.o20VL, 21.0), (s.o_20V, -21.0), (s.o5V, 0.0),(s.o15V, 15.0),
             (s.o_15V, -15.0), (s.o15Vp, 0.0), (s.o15VpSw, 0.0),
             (s.oPwrGood, 0.0), ))
        t.pwrup_aux.run()

    def _step_key_switch1(self):
        """Turn on KeySw1 and measure voltages."""
        self.fifo_push(
            ((s.o5V, 5.0), (s.o15V, 15.0), (s.o_15V, -15.0), (s.o15Vp, 15.0),
             (s.o15VpSw, 0.0), (s.oPwrGood, 5.0), ))
        t.key_sw1.run()
