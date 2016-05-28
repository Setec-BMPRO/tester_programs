#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C45A-15 Initial Test Program."""

import os
import inspect
import logging

import tester
from share import ProgramPIC
from . import support
from . import limit

INI_LIMIT = limit.DATA

_PIC_HEX = 'c45a-15.hex'

_OCP_PERCENT_REG = 0.015

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.TestSequence):

    """C45A-15 Initial Test Program."""

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
            ('SecCheck', self._step_sec_check, None, True),
            ('Program', self._step_program, None, True),
            ('OVP', self._step_ovp, None, True),
            ('PowerUp', self._step_power_up, None, True),
            ('Load', self._step_load, None, True),
            ('OCP', self._step_ocp, None, True),
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
        global m, d, s, t
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)
        t = support.SubTests(d, m)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_fixture_lock(self):
        """Check that Fixture Lock is closed."""
        self.fifo_push(((s.oLock, 10.0), ))
        m.dmm_Lock.measure(timeout=5)

    def _step_sec_check(self):
        """Apply external dc to secondary and measure voltages."""
        self.fifo_push(
            ((s.oVoutPre, 12.0), (s.oVsense, (0.5, 12.0)),
             (s.oVout, (12.0, 12.0)), (s.oVref, 5.0), ))
        t.sec_chk.run()

    def _step_program(self):
        """
        Program the PIC device.

        Vsec_Bias_In is injected to power the PIC for programming.
        While waiting,

        """
        # Start the PIC programmer (takes about 6 sec)
        self._logger.info('Start PIC programmer')
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        d.rla_Prog.set_on()
        pic = ProgramPIC(
            hexfile=_PIC_HEX, working_dir=folder,
            device_type='16F684', sensor=s.oMirPIC,
            fifo=self._fifo)
        # Wait for programming completion & read results
        pic.read()
        d.rla_Prog.set_off()
        m.pgmPIC.measure()

    def _step_ovp(self):
        """Apply external dc and measure output OVP."""
        self.fifo_push(
            ((s.oVref, 0.5), (s.oGreen, 2.0),
             (s.oVcc, (12.0, ) * 25 + (5.4, ), ), ))
        t.OVP.run()

    def _step_power_up(self):
        """Power up unit at 95Vac and measure primary voltages."""
        self.fifo_push(
            ((s.oVac, (96, 240)), (s.oVcc, 12.0), (s.oVref, 5.0),
             (s.oGreen, 2.0), (s.oYellow, (0.1, 2.0)),
             (s.oRed, (0.1, 4.5)), (s.oVout, (9.0,) * 2 + (16.0,)),
             (s.oVsense, 8.9), ))
        t.pwr_up.run()

    def _step_load(self):
        """Measure load regulatio."""
        self.fifo_push(((s.oVout, (16.0, 15.8)), ))
        d.dcl.output(0.0, True)
        d.rla_Load.set_on()
        noload = m.dmm_Vout.measure(timeout=5).reading1
        d.dcl.output(3.0)
        fullload = m.dmm_Vout.measure(timeout=5).reading1
        reg = ((fullload - noload) / noload) * 100
        s.oMirReg.store(reg)
        m.loadReg.measure()
        # Calculate the trip point of output voltage for OCP check
        reg = self._limits['Reg'].limit[0]
        triplevel = noload + (noload * (reg / 100))
        self._logger.debug('OCP Trip Level: %s', triplevel)
        self._limits['inOCP'].limit = triplevel

    def _step_ocp(self):
        """Measure OCP point."""
        self.fifo_push(((s.oVout, (16.0, ) * 65 + (15.5, ), ), ))
        m.ramp_OCP.measure()
