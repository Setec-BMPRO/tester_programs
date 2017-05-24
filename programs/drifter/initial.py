#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drifter Initial Test Program."""
# FIXME: Upgrade this program to 3rd Generation standards with unittest.

import os
import inspect
import time
from pydispatch import dispatcher
import tester
from tester.testlimit import lim_hilo, lim_hilo_delta, lim_hilo_int, lim_string
import share
from . import console

# Serial port for the PIC.
PIC_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM1'}[os.name]

FORCE_OFFSET = -8
FORCE_THRESHOLD = 160

_COMMON = (
    lim_hilo_delta('Vin', 12.0, 0.1),
    lim_hilo_delta('Vsw', 0, 100),
    lim_hilo_delta('Vref', 0, 100),
    lim_hilo_delta('Vcc', 3.30, 0.07),
    lim_hilo_delta('Isense', -90, 5),
    lim_hilo('3V3', -2.8, -2.5),
    lim_hilo_delta('%ErrorV', 0, 2.24),
    lim_hilo_delta('%CalV', 0, 0.36),
    lim_hilo_delta('%ErrorI', 0, 2.15),
    lim_hilo_delta('%CalI', 0, 0.50),
    # Data reported by the PIC
    lim_hilo_int('PicStatus 0', 0),
    lim_hilo_delta('PicZeroChk', 0, 65.0),
    lim_hilo_delta('PicVin', 12.0, 0.5),
    lim_hilo_delta('PicIsense', -90, 5),
    lim_hilo_delta('PicVfactor', 20000, 1000),
    lim_hilo_delta('PicIfactor', 15000, 1000),
    lim_hilo('PicIoffset', -8.01, -8),
    lim_hilo('PicIthreshold', 160, 160.01),
    )

LIMITS_STD = tester.testlimit.limitset(_COMMON + (
    lim_string('Software', 'Drifter-5.hex'),
    lim_hilo('0V8', -1.2, -0.4),
    ))

LIMITS_BM = tester.testlimit.limitset(_COMMON + (
    lim_string('Software', 'DrifterBM-2.hex'),
    lim_hilo('0V8', -1.4, -0.6),
    ))

LIMITS = {      # Test limit selection keyed by program parameter
    None: LIMITS_STD,
    'STD': LIMITS_STD,
    'BM': LIMITS_BM,
    }

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Initial(tester.TestSequence):

    """Drifter Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('Program', self._step_program, not self.fifo),
            tester.TestStep('CalPre', self._step_cal_pre),
            tester.TestStep('Calibrate', self._step_calibrate),
            )
        self._limits = LIMITS[self.parameter]
        global d, s, m
        d = LogicalDevices(self.physical_devices, self._limits, self.fifo)
        s = Sensors(d, self._limits)
        m = Measurements(s, self._limits)

    def close(self):
        """Finished testing."""
        global m, d, s
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
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
            d.pic.puts(str)

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
            d.pic.puts(str)

        # Simulate zero current
        d.rla_ZeroCal.set_on()
        time.sleep(0.2)
        self._cal_reload()
        m.pic_ZeroChk.measure(timeout=5)
        # Auto-zero the PIC current
        d.pic['CAL_I_ZERO'] = True
        # Assign forced offset & threshold for current display
        d.pic['CAL_OFFSET_CURRENT'] = FORCE_OFFSET
        d.pic['ZERO-CURRENT-DISPLAY-THRESHOLD'] = FORCE_THRESHOLD
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
        d.pic.puts('', priority=True)

        d.pic['CAL_RELOAD'] = True
        time.sleep(10)


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices, limits, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        self.dcs_RS232 = tester.DCSource(devices['DCS1'])
        self.dcs_SlopeCal = tester.DCSource(devices['DCS2'])
        self.dcs_Vin = tester.DCSource(devices['DCS3'])
        self.rla_Prog = tester.Relay(devices['RLA1'])
        self.rla_ZeroCal = tester.Relay(devices['RLA2'])
        # PIC device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self.program_pic = share.ProgramPIC(
            limits['Software'].limit, folder, '18F87J93', self.rla_Prog)
        # Serial connection to the console
        pic_ser = tester.SimSerial(
            simulation=self._fifo, baudrate=9600, timeout=5)
        # Set port separately, as we don't want it opened yet
        pic_ser.port = PIC_PORT
        self.pic = console.Console(pic_ser)

    def reset(self):
        """Reset instruments."""
        self.pic.close()
        for dcs in (self.dcs_RS232, self.dcs_SlopeCal, self.dcs_Vin):
            dcs.output(0.0, output=False)
        for rla in (self.rla_Prog, self.rla_ZeroCal):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        dmm = logical_devices.dmm
        pic = logical_devices.pic
        sensor = tester.sensor
        self.oMirErrorV = sensor.Mirror()
        self.oMirErrorI = sensor.Mirror()
        self.oVin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self.oVsw = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.001)
        self.oVref = sensor.Vdc(dmm, high=3, low=1, rng=10, res=0.001)
        self.oVcc = sensor.Vdc(dmm, high=4, low=1, rng=10, res=0.001)
        self.oIsense = sensor.Vdc(
            dmm, high=5, low=1, rng=10, res=0.00001, scale=-1000.0)
        self.o3V3 = sensor.Vdc(dmm, high=6, low=1, rng=10, res=0.001)
        self.o0V8 = sensor.Vdc(dmm, high=7, low=1, rng=10, res=0.001)
        self.pic_Status = console.Sensor(pic, 'NVSTATUS')
        self.pic_ZeroChk = console.Sensor(pic, 'ZERO_CURRENT')
        self.pic_Vin = console.Sensor(pic, 'VOLTAGE')
        self.pic_isense = console.Sensor(pic, 'CURRENT')
        self.pic_Vfactor = console.Sensor(pic, 'V_FACTOR')
        self.pic_Ifactor = console.Sensor(pic, 'I_FACTOR')
        self.pic_Ioffset = console.Sensor(pic, 'CAL_OFFSET_CURRENT')
        self.pic_Ithreshold = console.Sensor(
            pic, 'ZERO-CURRENT-DISPLAY-THRESHOLD')

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirErrorV.flush()
        self.oMirErrorI.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.ErrorV = Measurement(limits['%ErrorV'], sense.oMirErrorV)
        self.CalV = Measurement(limits['%CalV'], sense.oMirErrorV)
        self.ErrorI = Measurement(limits['%ErrorI'], sense.oMirErrorI)
        self.CalI = Measurement(limits['%CalI'], sense.oMirErrorI)
        self.dmm_vin = Measurement(limits['Vin'], sense.oVin)
        self.dmm_Vsw = Measurement(limits['Vsw'], sense.oVsw)
        self.dmm_Vref = Measurement(limits['Vref'], sense.oVref)
        self.dmm_Vcc = Measurement(limits['Vcc'], sense.oVcc)
        self.dmm_isense = Measurement(limits['Isense'], sense.oIsense)
        self.dmm_3V3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_0V8 = Measurement(limits['0V8'], sense.o0V8)
        self.pic_Status = Measurement(limits['PicStatus 0'], sense.pic_Status)
        self.pic_ZeroChk = Measurement(limits['PicZeroChk'], sense.pic_ZeroChk)
        self.pic_vin = Measurement(limits['PicVin'], sense.pic_Vin)
        self.pic_isense = Measurement(limits['PicIsense'], sense.pic_isense)
        self.pic_Vfactor = Measurement(limits['PicVfactor'], sense.pic_Vfactor)
        self.pic_Ifactor = Measurement(limits['PicIfactor'], sense.pic_Ifactor)
        self.pic_Ioffset = Measurement(limits['PicIoffset'], sense.pic_Ioffset)
        self.pic_Ithreshold = Measurement(
            limits['PicIthreshold'], sense.pic_Ithreshold)
