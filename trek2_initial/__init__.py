#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Initial Test Program."""

import os
import logging
import time

import tester
import share.programmer
import share.arm
from . import support
from . import limit

MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

# Serial port for the ARM. Used by programmer and ARM comms module.
_ARM_PORT = {'posix': '/dev/ttyUSB0',
             'nt': r'\\.\COM1',
             }[os.name]

_ARM_HEX = '.hex'

_HEX_DIR = {'posix': '/opt/setec/ate4/trek2_initial',
            'nt': r'C:\TestGear\TcpServer\trek2_initial',
           }[os.name]


# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


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
            ('Initialise', self._step_initialise_arm, None, True),
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
        self._armdev = share.arm.Console(port=_ARM_PORT)
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
        self._armdev.close()
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

    def _step_initialise_arm(self):
        """Initialise the ARM device."""
        if not self._fifo:
            self._armdev.open()
        self._armdev.defaults()
