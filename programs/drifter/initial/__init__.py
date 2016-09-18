#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drifter Initial Test Program."""

import logging
import time
import tester
from . import support
from . import limit

INI_LIMIT = limit.DATA
INI_LIMIT_BM = limit.DATA_BM

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Initial(tester.TestSequence):

    """Drifter Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('Program', self._step_program, not fifo),
            tester.TestStep('CalPre', self._step_cal_pre),
            tester.TestStep('Calibrate', self._step_calibrate),
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
        global d, s, m
        d = support.LogicalDevices(self._devices, self._limits, self.fifo)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        d.reset()

    def _step_power_up(self):
        """Apply input DC and measure voltages."""
        self.fifo_push(((s.oVin, 12.0), (s.oVcc, 3.3), ))

        d.dcs_Vin.output(12.0, output=True)
        time.sleep(2)
        tester.MeasureGroup((m.dmm_vin, m.dmm_Vcc), timeout=5)

    def _step_program(self):
        """Program the PIC device."""
        d.program_pic.program()

    def _step_cal_pre(self):
        """Setup the PIC device for calibration.

        The PIC is accessed via the serial port.

        """
        self.fifo_push(
            ((s.oVsw, 3.3), (s.oVref, 3.3), (s.o3V3, -2.7), (s.o0V8, -0.8), ))
        for str in (
                ('', ) * 2 +
                ('Banner1\r\nBanner2', ) +
                ('', '0', '')
                ):
            d.pic_puts(str)

        d.dcs_RS232.output(10.0, output=True)
        time.sleep(4)
        d.pic.open()
        d.pic['UNLOCK'] = True
        d.pic['NVDEFAULT'] = True
        d.pic['RESTART'] = True
        time.sleep(4)
        d.pic['UNLOCK'] = True
        m.pic_Status.measure(timeout=5)
        d.pic['APS_DISABLE'] = 1
        tester.MeasureGroup(
            (m.dmm_Vsw, m.dmm_Vref, m.dmm_3V3, m.dmm_0V8, ), timeout=5)

    def _step_calibrate(self):
        """Calibrate zero current, voltage, high current."""
        self.fifo_push(((s.oVin, 12.0), (s.oIsense, 0.090), (s.oVcc, 3.3), ))
        for str in (
                ('-35', '', '', '', ) +
                ('11950', '', '11980', ) +
                ('-89000', '', '-89900', ) +
                ('', ) +
                ('20000', '15000', '-8', '160', )
                ):
            d.pic_puts(str)

        # Simulate zero current
        d.rla_ZeroCal.set_on()
        time.sleep(0.2)
        self._cal_reload()
        m.pic_ZeroChk.measure(timeout=5)
        # Auto-zero the PIC current
        d.pic['CAL_I_ZERO'] = True
        # Assign forced offset & threshold for current display
        d.pic['CAL_OFFSET_CURRENT'] = limit.FORCE_OFFSET
        d.pic['ZERO-CURRENT-DISPLAY-THRESHOLD'] = limit.FORCE_THRESHOLD
        # Calibrate voltage
        dmm_vin = m.dmm_vin.measure(timeout=5).reading1
        pic_vin = m.pic_vin.measure(timeout=5).reading1
        err = ((dmm_vin - pic_vin) / dmm_vin) * 100
        s.oMirErrorV.store(err)
        m.ErrorV.measure()
        adjust_vcal = (err != self._limits['%CalV'])
        # Adjust voltage if required
        if adjust_vcal:
            d.pic['CAL_V_SLOPE'] = dmm_vin
        d.rla_ZeroCal.set_off()
        # Simulate a high current
        d.dcs_SlopeCal.output(17.1, output=True)
        time.sleep(0.2)
        self._cal_reload()
        if adjust_vcal:
            # This will check any voltage adjust done above
            # ...we are using this CAL_RELOAD to save 10sec
            pic_vin = m.pic_vin.measure(timeout=5).reading1
            err = ((dmm_vin - pic_vin) / dmm_vin) * 100
            s.oMirErrorV.store(err)
            m.CalV.measure()
        # Now we proceed to calibrate the current
        dmm_isense = m.dmm_isense.measure(timeout=5).reading1
        pic_isense = m.pic_isense.measure(timeout=5).reading1
        err = ((dmm_isense - pic_isense) / dmm_isense) * 100
        s.oMirErrorI.store(err)
        m.ErrorI.measure()
        # Adjust current if required
        if err != self._limits['%CalI']:
            d.pic['CAL_I_SLOPE'] = dmm_isense
            self._cal_reload()
            pic_isense = m.pic_isense.measure(timeout=5).reading1
            err = ((dmm_isense - pic_isense) / dmm_isense) * 100
            s.oMirErrorI.store(err)
            m.CalI.measure()
        d.dcs_SlopeCal.output(0.0, output=False)
        # Write all adjusted parameters in a single write
        d.pic['NVWRITE'] = True
        time.sleep(5)
        # Read internal settings
        tester.MeasureGroup((
            m.pic_Vfactor, m.pic_Ifactor, m.pic_Ioffset, m.pic_Ithreshold, ),
            timeout=5)

    def _cal_reload(self):
        """Re-Load data readings."""
        d.pic_puts('', priority=True)

        d.pic['CAL_RELOAD'] = True
        time.sleep(10)
