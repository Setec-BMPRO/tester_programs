#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Initial Test Program."""

import os
import logging
import time
import serial
import queue
import threading

import tester
import share.programmer
import share.trek2
from . import support
from . import limit

MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

# Serial port for the ARM. Used by programmer and ARM comms module.
_ARM_PORT = {'posix': '/dev/ttyUSB0',
             'nt': r'\\.\COM1',
             }[os.name]

_ARM_HEX = 'Trek2_1.0.102.hex'

_HEX_DIR = {'posix': '/opt/setec/ate4/trek2_initial',
            'nt': r'C:\TestGear\TcpServer\trek2_initial',
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
        """Get data from the written-out queue.

        @return bytes

        """
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

        @return bytes

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

    """Trek2 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('PowerUp', self._step_power_up, None, True),
            ('Program', self._step_program, None, True),
            ('TestArm', self._step_test_arm, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        if self._fifo:
            self._arm_ser = MockSerial()
        else:
            self._arm_ser = serial.Serial(port=_ARM_PORT,
                                          baudrate=115200, timeout=0.1)
        self._armdev = share.trek2.Console(self._arm_ser)
        global d
        d = support.LogicalDevices(self._devices)
        global s
        s = support.Sensors(d, self._limits)
        global m
        m = support.Measurements(s, self._limits)
        global t
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        self._arm_ser.close()
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

    def _step_power_up(self):
        """Apply input 12Vdc and measure voltages."""
        self.fifo_push(((s.oVin, 12.0), (s.o3V3, 3.3), ))

        t.pwr_up.run()

    def _step_program(self):
        """Program the ARM device."""
        # Set BOOT active before power-on so the ARM boot-loader runs
        d.rla_boot.set_on()
        # Start the ARM programmer
        self._logger.info('Start ARM programmer')
        arm = share.programmer.ProgramARM(
            _ARM_HEX, _HEX_DIR, s.oMirARM, _ARM_PORT, fifo=self._fifo)
        arm.read()
        m.pgmARM.measure()
        # Reset BOOT to ARM
        d.rla_boot.set_off()
        # Reset micro.
        d.rla_reset.pulse(0.1)
        # ARM startup delay
        if not self._fifo:
            time.sleep(1)

    def _step_test_arm(self):
        """Initialise the ARM device."""
        self.fifo_push(((s.oBkLght, (4.0, 0)),  ))

        self._armdev.bklght(100)
        m.dmm_BkLghtOn.measure(timeout=5)
        self._armdev.bklght(0)
        m.dmm_BkLghtOff.measure(timeout=5)
