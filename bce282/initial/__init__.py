#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BCE282-12/24 Initial Test Program."""

# FIXME: This program is not finished yet!

import os
import logging
import time

import tester.testsequence
import tester.measure
import tester.sensor

from . import msp
from . import support
from . import limit

LIMIT_DATA12 = limit.DATA12       # BCE282-12 limits
LIMIT_DATA24 = limit.DATA24       # BCE282-24 limits

# Serial port for MSP430 console.
_MSP430_PORT = {'posix': '/dev/ttyUSB0',
                'nt': r'\\.\COM2',
                }[os.name]

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements
t = None        # Shortcut to SubTests


class Main(tester.testsequence.TestSequence):

    """BCE282-12/24 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('FixtureLock', self._step_fixture_lock, None, True),
            ('ProgramMicro', self._step_program_micro, None, True),
            ('PowerUp', self._step_power_up, None, False),
            ('Calibration', self._step_cal, None, False),
            ('OCP', self._step_ocp, None, False),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        # It is a BCE282-12 if FullLoad current > 15.0A
        self._isbce12 = test_limits['FullLoad'].limit > 15.0

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        self._msp = msp.Console(port=_MSP430_PORT)
        global d, s, m, t
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits, self._msp)
        m = support.Measurements(s, self._limits)
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        self._msp.close()
        global m, d, s, t
        m = d = s = t = None

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.acsource.output(voltage=0.0, output=False)
        d.dcl_Vout.output(2.0)
        d.dcl_Vbat.output(2.0)
        time.sleep(1)
        d.discharge.pulse()
        # Reset Logical Devices
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_fixture_lock(self):
        """Check that Fixture Lock is closed."""
        self.fifo_push(((s.Lock, 10.0), ))
        m.dmm_Lock.measure(timeout=5)

    def _step_program_micro(self):
        """Program the microprocessor.

           Powers bootloader interface and MSP430.
           Dumps existing password if any.
           Programs.

        """
        self.fifo_push(((s.oVccBias, 15.0), ))
        t.prog_setup.run()
        if not self._fifo:
            self._msp.open()
        passwd = self._msp.bsl_passwd()
        self._logger.debug('Dump password: %s', passwd)
        #Program MSP430
        d.rla_Prog.set_on()
        d.rla_Prog.set_off()
        d.dcs_VccBias.output(0.0)

    def _step_power_up(self):
        """Power up the unit at 240Vac and measure voltages at min load."""
        self.fifo_push(((s.oVac, 240.0), (s.oVbus, 340.0), (s.oVccPri, 15.5),
                       (s.oVccBias, 15.0), (s.oVbat, 0.1), (s.oAlarm, 2200), ))
        t.pwr_up.run()

    def _step_cal(self):
        """Calibration."""
        self._msp.defaults()
        m.msp_Status.measure(timeout=5)
        self._msp.test_mode_enable()
#        dmm_Vout = m.dmm_Vout.measure(timeout=5)[1][0]
#        msp_Vout = m.msp_Vout.measure(timeout=5)[1][0]

    def _step_ocp(self):
        """Measure Vout and Vbat OCP points."""
        if self._isbce12:
            self.fifo_push(((s.oAlarm, 12000),
                            (s.oVbat, (13.6, ) * 15 + (12.9, ), ),
                            (s.oVout, (13.6, ) * 15 + (12.9, ), ), ))
        else:
            self.fifo_push(((s.oAlarm, 12000),
                            (s.oVbat, (27.3, ) * 15 + (25.9, ), ),
                            (s.oVout, (27.3, ) * 15 + (25.9, ), ), ))
        tester.measure.group((m.dmm_AlarmOpen, m.ramp_BattOCP,
                              m.ramp_OutOCP, ), timeout=5)
