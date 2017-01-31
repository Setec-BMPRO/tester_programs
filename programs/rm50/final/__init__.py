#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RM-50-24 Final Test Program."""

import logging
import time
import tester
from . import support
from . import limit

FIN_LIMIT = limit.DATA

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """RM-50-24 Final Test Program."""

    def __init__(self, per_panel, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('FixtureLock', self._step_fixture_lock),
            tester.TestStep('DCInputLeakage', self._step_dcinput_leakage),
            tester.TestStep('DCInputTrack', self._step_dcinput_track),
            tester.TestStep('ACInput240V', self._step_acinput240v),
            tester.TestStep('ACInput110V', self._step_acinput110v),
            tester.TestStep('ACInput90V', self._step_acinput90v),
            tester.TestStep('OCP', self._step_ocp),
            tester.TestStep('PowerNoLoad', self._step_power_noload),
            tester.TestStep('Efficiency', self._step_efficiency),
            )
        # Set the Test Sequence in my base instance
        super().__init__(per_panel, sequence, fifo)
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
        self.fifo_push(((s.Lock, 1.0), ))
        m.dmm_Lock.measure(timeout=5)

    def _step_dcinput_leakage(self):
        """Test for input leakage current at the DC input with no load."""
        self.fifo_push(((s.oRsense, 1000), (s.oVsense, 0.05), ))
        t.dcinp_leak.run()

    def _step_dcinput_track(self):
        """
        Measure the drop in the track between dc input and output at full load.
        """
        self.fifo_push(
            ((s.o24Vdcin, 23.6), (s.o24Vdcin, 24.0), (s.o24Vdcout, 23.65), ))
        d.dcl_dcout.output(2.1, True)
        val = m.dmm_24Vdcin.measure(timeout=5).reading1
        # Slightly higher dc input to compensate for drop in fixture cabling
        d.dcs_24V.output(24.0 + (24.0 - val))
        vals = tester.MeasureGroup(
            (m.dmm_24Vdcin, m.dmm_24Vdcout), timeout=5).readings
        s.oMirVdcDrop.store(vals[0] - vals[1])
        m.dmm_vdcDrop.measure()
        d.dcs_24V.output(0.0, output=False)
        d.dcl_dcout.output(0.0)

    def _step_acinput240v(self):
        """Apply 240V AC input and measure output at no load and full load."""
        self.fifo_push(((s.o24V, (24.0, ) * 2), ))
        t.acinput_240V.run()

    def _step_acinput110v(self):
        """Apply 110V AC input and measure output at no load and full load."""
        self.fifo_push(((s.o24V, (24.0, ) * 2), ))
        t.acinput_110V.run()

    def _step_acinput90v(self):
        """Apply 90V AC input and measure outputs at various load steps."""
        self.fifo_push(((s.o24V, (24.0, ) * 4), ))
        t.acinput_90V.run()
        d.dcl_out.linear(2.7, 2.95, step=0.05, delay=0.05)
        for curr in (3.0, 3.05):
            with tester.PathName(str(curr)):
                time.sleep(0.5)
                d.dcl_out.output(curr)
                d.dcl_out.opc()
                m.dmm_24Vpl.measure(timeout=5)

    def _step_ocp(self):
        """Measure OCP point, turn off and recover."""
        self.fifo_push(
            ((s.o24V, 24.0), (s.o24V, (24.0, ) * 15 + (22.5, ), ),
             (s.o24V, 0.0), ))
        t.ocp.run()

    def _step_power_noload(self):
        """Measure input power at no load."""
        self.fifo_push(((s.o24V, 24.0), (s.oInputPow, 2.0), ))
        t.pow_nl.run()

    def _step_efficiency(self):
        """Measure efficiency."""
        self.fifo_push(
            ((s.oInputPow, 59.0), (s.o24V, 24.0), (s.oCurrshunt, 0.0021), ))
        d.dcl_out.output(2.1)
        inp_pwr_fl = m.dmm_powerFL.measure(timeout=5).reading1
        out_volts_fl = m.dmm_24Vfl.measure(timeout=5).reading1
        out_curr_fl = m.dmm_currShunt.measure(timeout=5).reading1
        eff = 100 * out_volts_fl * out_curr_fl / inp_pwr_fl
        s.oMirEff.store(eff)
        m.dmm_eff.measure()
