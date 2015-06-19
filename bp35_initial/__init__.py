#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BP35 Initial Test Program."""

import os
import logging
import time

import tester
import share.programmer
from . import support
from . import limit

MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA

# Serial port for the ARM. Used by programmer and ARM comms module.
_ARM_PORT = {'posix': '/dev/ttyUSB0',
             'nt': r'\\.\COM1',
             }[os.name]

_ARM_HEX = '.hex'

_HEX_DIR = {'posix': '/opt/setec/ate4/bp35_initial',
            'nt': r'C:\TestGear\TcpServer\bp35_initial',
           }[os.name]


# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.TestSequence):

    """BP35 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('FixtureLock', self._step_fixture_lock, None, True),
            ('Program', self._step_program, None, True),
            ('PowerUp', self._step_power_up, None, True),
            ('OCP', self._step_ocp, None, True),
            ('ShutDown', self._step_shutdown, None, True),
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
            d.acsource.output(voltage=0.0, output=False)
            d.dcl_Out.output(2.0)
            d.dcl_Bat.output(2.0)
            if self._fifo:
                d.discharge.pulse(0.1)
            else:
                time.sleep(1)
                d.discharge.pulse()
            # Reset Logical Devices
            d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_fixture_lock(self):
        """Check that Fixture Lock is closed."""
        self.fifo_push(((s.oLock, 10.0), (s.osw1, 100.0), (s.osw2, 100.0),
                      (s.osw3, 100.0), (s.osw4, 100.0), ))
        MeasureGroup((m.dmm_Lock, m.dmm_sw1, m.dmm_sw2, m.dmm_sw3,
                    m.dmm_sw4, ), timeout=5)

    def _step_program(self):
        """Program the ARM device.

        5Vsb is injected to power the ARM for programming.
        Unit is left running the new code.

        """
        self.fifo_push(((s.o3V3, 3.30), ))

        # Set BOOT active before power-on so the ARM boot-loader runs
        d.rla_boot.set_on()
        # Apply and check injected rails
        d.dcs_vbat.output(12.0, True)
        MeasureGroup((m.dmm_5V, m.dmm_3V3, ), timeout=2)
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

    def _step_power_up(self):
        """ """
        self.fifo_push(((s.oACin, 240.0), ))

        t.pwr_up.run()

    def _step_ocp(self):
        """Ramp up load until OCP."""
        self.fifo_push(((s.oVout, (12.8, ) * 11 + (11.0, ), ), ))
        d.dcl.output(0.0, output=True)
        d.dcl.binary(0.0, 32.0, 5.0)
        m.ramp_OCP.measure()

    def _step_shutdown(self):
        """Apply overload to shutdown. Check load switch."""
        self.fifo_push(((s.oVout, (0.0, 12.0, 0.0, 12.0)), (s.oVbat, 12.0), ))
        t.shdn.run()
