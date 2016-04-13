#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drifter Initial Test Program."""

import os
import inspect
import logging
import time
import tester
from . import support
from . import limit
from ...share.programmer import ProgramPIC
from ...share.sim_serial import SimSerial
from ..console import Console

MeasureGroup = tester.measure.group

LIMIT_DATA = limit.DATA
LIMIT_DATA_BM = limit.DATA_BM

# Serial port for the PIC.
_PIC_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM1'}[os.name]
_UNLOCK_KEY = 'XDEADBEA7'

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements


class Main(tester.TestSequence):

    """Drifter Initial Test Program."""

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
            ('CalPre', self._step_cal_pre, None, True),
            ('Calibrate', self._step_calibrate, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        # Serial connection to the console
        self._pic_ser = SimSerial(
            simulation=self._fifo, baudrate=9600, timeout=2)
        # Set port separately, as we don't want it opened yet
        self._pic_ser.setPort(_PIC_PORT)
        self._picdev = Console(self._pic_ser)

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits, self._picdev)
        m = support.Measurements(s, self._limits)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        self._picdev.close()
        global m, d, s
        m = d = s = None

    def safety(self):
        """Make the unit safe after a test."""
        self._logger.info('Safety')
        # Reset Logical Devices
        d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_power_up(self):
        """Apply input DC and measure voltages."""
        self.fifo_push(((s.oVin, 12.0), (s.oVcc, 3.3), ))

        d.dcs_Vin.output(12.0, output=True)
        time.sleep(2)
        MeasureGroup((m.dmm_vin, m.dmm_Vcc), timeout=5)

    def _step_program(self):
        """Program the PIC device."""
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        d.rla_Prog.set_on()
        hexfile = self._limits['Software'].limit
        self._logger.debug('HexFile "%s"', hexfile)
        pic = ProgramPIC(
            hexfile=hexfile, working_dir=folder,
            device_type='18F87J93', sensor=s.oMirPIC,
            fifo=self._fifo)
        # Wait for programming completion & read results
        pic.read()
        d.rla_Prog.set_off()
        m.pgmPIC.measure()

    def _step_cal_pre(self):
        """Setup the PIC device for calibration.

        The PIC is accessed via the serial port.

        """
        self.fifo_push(
            ((s.pic_Status, 0), (s.oVsw, 3.3), (s.oVref, 3.3),
             (s.o3V3, -2.7), (s.o0V8, -0.8), ))

        d.dcs_RS232.output(10.0, output=True)
        time.sleep(4)
        self._picdev.open()
        self._picdev['UNLOCK'] = _UNLOCK_KEY
        self._picdev['NVDEFAULT'] = True
        self._picdev['RESTART'] = True
        time.sleep(4)
        self._picdev['UNLOCK'] = _UNLOCK_KEY
        m.pic_Status.measure(timeout=5)
        self._picdev['APS_DISABLE'] = 1
        MeasureGroup(
            (m.dmm_Vsw, m.dmm_Vref, m.dmm_3V3, m.dmm_0V8, ), timeout=5)

    def _step_calibrate(self):
        """Calibrate zero current, voltage, high current."""
        self.fifo_push(
            ((s.oVin, 12.0), (s.pic_ZeroChk, -35), (s.pic_Status, 0),
             (s.pic_Vin, (11.95, 11.98)),
             (s.pic_isense, (-89.0, -89.9)), (s.oIsense, 0.090),
             (s.pic_Status, 0), (s.oVin, 12.0), (s.oVcc, 3.3),
             (s.pic_Vfactor, 20000), (s.pic_Ifactor, 15000),
             (s.pic_Ioffset, -8), (s.pic_Ithreshold, 160), ))

        # Simulate zero current
        d.rla_ZeroCal.set_on()
        time.sleep(0.2)
        self._picdev['CAL_RELOAD'] = True
        time.sleep(10)
        m.pic_ZeroChk.measure(timeout=5)
        # Auto-zero the PIC current
        self._picdev['CAL_I_ZERO'] = True
        # Assign forced offset & threshold for current display
        self._picdev['CAL_OFFSET_CURRENT'] = limit.FORCE_OFFSET
        self._picdev['ZERO-CURRENT-DISPLAY-THRESHOLD'] = limit.FORCE_THRESHOLD
        # Calibrate voltage
        dmm_vin = m.dmm_vin.measure(timeout=5)[1][0]
        pic_vin = m.pic_vin.measure(timeout=5)[1][0]
        err = ((dmm_vin - pic_vin) / dmm_vin) * 100
        s.oMirErrorV.store(err)
        m.ErrorV.measure()
        # Adjust voltage if required
        if err != self._limits['%CalV']:
            self._picdev['CAL_V_SLOPE'] = dmm_vin
        d.rla_ZeroCal.set_off()
        # Simulate a high current
        d.dcs_SlopeCal.output(17.1, output=True)
        time.sleep(0.2)
        self._picdev['CAL_RELOAD'] = True
        time.sleep(10)
        # This will check any voltage adjust done above
        # ...we are using this CAL_RELOAD to save 10sec
        dmm_vin = m.dmm_vin.measure(timeout=5)[1][0]
        pic_vin = m.pic_vin.measure(timeout=5)[1][0]
        err = ((dmm_vin - pic_vin) / dmm_vin) * 100
        s.oMirErrorV.store(err)
        m.CalV.measure()
        # Now we proceed to calibrate the current
        dmm_isense = m.dmm_isense.measure(timeout=5)[1][0]
        pic_isense = m.pic_isense.measure(timeout=5)[1][0]
        err = ((dmm_isense - pic_isense) / dmm_isense) * 100
        s.oMirErrorI.store(err)
        m.ErrorI.measure()
        # Adjust current if required
        if err != self._limits['%CalI']:
            self._picdev['CAL_I_SLOPE'] = dmm_isense
            self._picdev['CAL_RELOAD'] = True
            time.sleep(10)
            pic_isense = m.pic_isense.measure(timeout=5)[1][0]
            err = ((dmm_isense - pic_isense) / dmm_isense) * 100
            s.oMirErrorI.store(err)
            m.CalI.measure()
        d.dcs_SlopeCal.output(0.0, output=False)
        # Write all adjusted parameters in a single write
        self._picdev['NVWRITE'] = True
        time.sleep(5)
#        # Restart the unit
#        d.dcs_Vin.output(0.0)
#        time.sleep(0.5)
#        d.dcs_Vin.output(12.0)
#        time.sleep(4)
#        MeasureGroup((m.dmm_vin, m.dmm_Vcc), timeout=5)
#        self._picdev['UNLOCK'] = _UNLOCK_KEY
        # Read internal settings
        m.pic_Vfactor.measure(timeout=5)
        m.pic_Ifactor.measure(timeout=5)
        m.pic_Ioffset.measure(timeout=5)
        m.pic_Ithreshold.measure(timeout=5)
