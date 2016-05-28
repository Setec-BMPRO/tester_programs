#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TS3020H Initial Test Program."""

import logging

import tester
from . import support
from . import limit

MeasureGroup = tester.measure.group

INI_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.TestSequence):

    """TS3020H Initial Test Program."""

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
            ('FuseCheck', self._step_fuse_check, None, True),
            ('FanCheck', self._step_fan_check, None, True),
            ('OutputOV_UV', self._step_ov_uv, None, True),
            ('PowerUp', self._step_power_up, None, True),
            ('MainsCheck', self._step_mains_check, None, True),
            ('AdjOutput', self._step_adj_output, None, True),
            ('Load', self._step_load, None, True),
            ('InputOV', self._step_input_ov, None, True),
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

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_fixture_lock(self):
        """Check that Fixture Lock is closed."""
        self.fifo_push(
            ((s.oLock, 10.0), (s.oFanConn, 150.0), (s.oInrush, 160.0), ))
        MeasureGroup((m.dmm_Lock, m.dmm_FanConn, m.dmm_InrushOff), timeout=5)

    def _step_fuse_check(self):
        """Check for output fuse in/out.

        Apply external Vout, SecCtl2 and measure led voltages.

        """
        self.fifo_push(
            ((s.oVout, 13.8), (s.oSecCtl, 13.5), (s.oSecCtl2, 13.8),
             (s.oGreenLed, (2.0, 0.0)), (s.oRedLed, (0.0, 2.0)), ))
        t.fuse_check.run()

    def _step_fan_check(self):
        """Check the operation of the fan.

        Apply external Vout, SecCtl2. Connect 56R to SecCtl to
        activate fan. Check for fan on/off.

        """
        self.fifo_push(
            ((s.oFan12V, (13.8, 0.5)), (s.oSecShdn, 13.0)))
        t.fan_check.run()

    def _step_ov_uv(self):
        """Apply external Vout and measure output OVP and UVP."""
        self.fifo_push(
            ((s.oSecShdn, ((13.0, ) * 14 + (12.4, )) * 2, ), ))
        t.OV_UV.run()

    def _step_power_up(self):
        """Apply low input AC and measure primary voltages."""
        self.fifo_push(
            ((s.oVac, 100.0), (s.oAcDetect, 11.0), (s.oInrush, 5.0),
             (s.oVbus, (400.0, 30.0)), (s.oVout, 13.8), (s.oSecCtl, 13.8),
             (s.oSecCtl2, 13.8), ))
        t.pwr_up.run()
        d.discharge.pulse(2.0)
        m.dmm_VbusOff.measure(timeout=10)

    def _step_mains_check(self):
        """Apply input AC with min load and measure voltages."""
        self.fifo_push(
            ((s.oAcDetect, 4.0), (s.oAcDetect, 11.0), (s.oVac, 240.0),
             (s.oAcDetect, 11.0), (s.oVbias, 12.0), (s.oSecCtl, 13.8),
             (s.oVout, 13.8), ))
        t.mains_chk.run()

    def _step_adj_output(self):
        """Adjust the output voltage.

        Set output voltage, apply load and measure voltages.

        """
#        self.fifo_push(((s.oAdjVout, True), ))
        self.fifo_push(
            ((s.oVout, (13.77, 13.78, 13.79, 13.8, 13.8)), ))
        m.ui_AdjVout.measure()
        m.dmm_VoutSet.measure(timeout=5)

    def _step_load(self):
        """Measure output voltage under load conditions.

           Load and measure output.
           Check output regulation.
           Check for shutdown with overload.

        """
        self.fifo_push(
            ((s.oVbus, 400.0), (s.oVbias, 12.0), (s.oSecCtl, 13.8),
             (s.oSecCtl2, 13.8), (s.oVout, (13.8, 13.8, 13.7, 0.0)),))
        t.load.run()
        # Measure load regulation
        d.dcl.output(0.0)
        noload = m.dmm_Vout.measure(timeout=5).reading1
        d.dcl.output(24.0)
        fullload = m.dmm_Vout.measure(timeout=5).reading1
        reg = ((noload - fullload) / noload) * 100
        s.oMirReg.store(reg)
        m.dmm_reg.measure()
        t.shutdown.run()

    def _step_input_ov(self):
        """Check for shutdown with input over voltage."""
        self.fifo_push(((s.oPWMShdn, (10.0, 0.5, 0.5)), ))
        t.inp_ov.run()
