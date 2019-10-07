#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drifter(BM) Initial Test Program."""

import os
import inspect
import time
import serial
import tester
from tester import TestStep, LimitBetween, LimitDelta, LimitInteger
import share
from . import console


class Initial(share.TestSequence):

    """Drifter Initial Test Program."""

    # Calibration values
    force_offset = -8
    force_threshold = 160
    # Limits common to both versions
    _common = (
        LimitDelta('Vin', 12.0, 0.1),
        LimitDelta('Vsw', 0, 100),
        LimitDelta('Vref', 0, 100),
        LimitDelta('Vcc', 3.30, 0.07),
        LimitDelta('Isense', -90, 5),
        LimitBetween('3V3', -2.8, -2.5),
        LimitDelta('%ErrorV', 0, 2.24),
        LimitDelta('%CalV', 0, 0.36),
        LimitDelta('%ErrorI', 0, 2.15),
        LimitDelta('%CalI', 0, 0.50),
        # Data reported by the PIC
        LimitInteger('PicStatus 0', 0),
        LimitDelta('PicZeroChk', 0, 65.0),
        LimitDelta('PicVin', 12.0, 0.5),
        LimitDelta('PicIsense', -90, 5),
        LimitDelta('PicVfactor', 20000, 1000),
        LimitDelta('PicIfactor', 15000, 1000),
        LimitBetween('PicIoffset', -8.01, -8),
        LimitBetween('PicIthreshold', 160, 160.01),
        )
    # Test limit selection keyed by program parameter
    limitdata = {
        'STD': {
            'Limits': _common + (
                LimitBetween('0V8', -1.2, -0.4),
                ),
            'Software': 'Drifter-5.hex',
            },
        'BM': {
            'Limits': _common + (
                LimitBetween('0V8', -1.4, -0.6),
                ),
            'Software': 'DrifterBM-2.hex',
            },
        }

    def open(self, uut):
        """Prepare for testing."""
        super().open(
            self.limitdata[self.parameter]['Limits'],
            Devices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerUp', self._step_power_up),
            TestStep('Program', self.devices['program_pic'].program),
            TestStep('CalPre', self._step_cal_pre),
            TestStep('Calibrate', self._step_calibrate),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input DC and measure voltages."""
        dev['dcs_Vin'].output(12.0, output=True, delay=2)
        self.measure(('dmm_vin', 'dmm_Vcc'), timeout=5)

    @share.teststep
    def _step_cal_pre(self, dev, mes):
        """Calibrate the PIC."""
        dev['dcs_RS232'].output(12.0, output=True, delay=4)
        pic = dev['pic']
        pic.open()
        pic['UNLOCK'] = True
        pic['NVDEFAULT'] = True
        pic['RESTART'] = True
        time.sleep(4)
        pic['UNLOCK'] = True
        mes['pic_Status'](timeout=5)
        pic['APS_DISABLE'] = 1
        self.measure(
            ('dmm_Vsw', 'dmm_Vref', 'dmm_3V3', 'dmm_0V8', ),
            timeout=5)

    @share.teststep
    def _step_calibrate(self, dev, mes):
        """Calibrate zero current, voltage, high current."""
        # Simulate zero current
        dev['rla_ZeroCal'].set_on(delay=0.2)
        pic = dev['pic']
        self._cal_reload(pic)
        mes['pic_ZeroChk'](timeout=5)
        # Auto-zero the PIC current
        pic['CAL_I_ZERO'] = True
        # Assign forced offset & threshold for current display
        pic['CAL_OFFSET_CURRENT'] = self.force_offset
        pic['ZERO-CURRENT-DISPLAY-THRESHOLD'] = self.force_threshold
        # Calibrate voltage
        dmm_vin = mes['dmm_vin'](timeout=5).reading1
        pic_vin = mes['pic_vin'](timeout=5).reading1
        err = ((dmm_vin - pic_vin) / dmm_vin) * 100
        mes['ErrorV'].sensor.store(err)
        mes['ErrorV']()
        adjust_vcal = (err != self.limits['%CalV'])
        # Adjust voltage if required
        if adjust_vcal:
            pic['CAL_V_SLOPE'] = dmm_vin
        dev['rla_ZeroCal'].set_off()
        # Simulate a high current
        dev['dcs_SlopeCal'].output(17.1, output=True, delay=0.2)
        self._cal_reload(pic)
        if adjust_vcal:
            # This will check any voltage adjust done above
            # ...we are using this CAL_RELOAD to save 10sec
            pic_vin = mes['pic_vin'](timeout=5).reading1
            err = ((dmm_vin - pic_vin) / dmm_vin) * 100
            mes['CalV'].sensor.store(err)
            mes['CalV']()
        # Now we proceed to calibrate the current
        dmm_isense = mes['dmm_isense'](timeout=5).reading1
        pic_isense = mes['pic_isense'](timeout=5).reading1
        err = ((dmm_isense - pic_isense) / dmm_isense) * 100
        mes['ErrorI'].sensor.store(err)
        mes['ErrorI']()
        # Adjust current if required
        if err != self.limits['%CalI']:
            pic['CAL_I_SLOPE'] = dmm_isense
            self._cal_reload(pic)
            pic_isense = mes['pic_isense'](timeout=5).reading1
            err = ((dmm_isense - pic_isense) / dmm_isense) * 100
            mes['CalI'].sensor.store(err)
            mes['CalI']()
        dev['dcs_SlopeCal'].output(0.0, output=False)
        # Write all adjusted parameters in a single write
        pic['NVWRITE'] = True
        time.sleep(5)
        # Read internal settings
        self.measure((
            'pic_Vfactor', 'pic_Ifactor', 'pic_Ioffset', 'pic_Ithreshold', ),
            timeout=5)

    @staticmethod
    def _cal_reload(pic):
        """Re-Load data readings.

        @param pic PIC logical device.

        """
        pic['CAL_RELOAD'] = True
        time.sleep(10)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_RS232', tester.DCSource, 'DCS1'),
                ('dcs_SlopeCal', tester.DCSource, 'DCS2'),
                ('dcs_Vin', tester.DCSource, 'DCS3'),
                ('rla_Prog', tester.Relay, 'RLA1'),
                ('rla_ZeroCal', tester.Relay, 'RLA2'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # PIC device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['program_pic'] = share.programmer.PIC(
            Initial.limitdata[self.parameter]['Software'],
            folder, '18F87J93', self['rla_Prog'])
        # Serial connection to the console
        pic_ser = serial.Serial(baudrate=9600, timeout=5)
        # Set port separately, as we don't want it opened yet
        pic_ser.port = share.config.Fixture.port('021299', 'PIC')
        self['pic'] = console.Console(pic_ser)

    def reset(self):
        """Reset instruments."""
        self['pic'].close()
        for dcs in ('dcs_RS232', 'dcs_SlopeCal', 'dcs_Vin'):
            self[dcs].output(0.0, output=False)
        for rla in ('rla_Prog', 'rla_ZeroCal'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        pic = self.devices['pic']
        sensor = tester.sensor
        self['oMirErrorV'] = sensor.MirrorReading()
        self['oMirErrorI'] = sensor.MirrorReading()
        self['oVin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self['oVsw'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.001)
        self['oVref'] = sensor.Vdc(dmm, high=3, low=1, rng=10, res=0.001)
        self['oVcc'] = sensor.Vdc(dmm, high=4, low=1, rng=10, res=0.001)
        self['oIsense'] = sensor.Vdc(
            dmm, high=5, low=1, rng=10, res=0.00001, scale=-1000.0)
        self['o3V3'] = sensor.Vdc(dmm, high=6, low=1, rng=10, res=0.001)
        self['o0V8'] = sensor.Vdc(dmm, high=7, low=1, rng=10, res=0.001)
        for sen, cmd in (
            ('pic_Status', 'NVSTATUS'),
            ('pic_ZeroChk', 'ZERO_CURRENT'),
            ('pic_Vin', 'VOLTAGE'),
            ('pic_isense', 'CURRENT'),
            ('pic_Vfactor', 'V_FACTOR'),
            ('pic_Ifactor', 'I_FACTOR'),
            ('pic_Ioffset', 'CAL_OFFSET_CURRENT'),
            ('pic_Ithreshold', 'ZERO-CURRENT-DISPLAY-THRESHOLD'),
            ):
            self[sen] = share.console.Sensor(pic, cmd)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('ErrorV', '%ErrorV', 'oMirErrorV', ''),
            ('CalV', '%CalV', 'oMirErrorV', ''),
            ('ErrorI', '%ErrorI', 'oMirErrorI', ''),
            ('CalI', '%CalI', 'oMirErrorI', ''),
            ('dmm_vin', 'Vin', 'oVin', ''),
            ('dmm_Vsw', 'Vsw', 'oVsw', ''),
            ('dmm_Vref', 'Vref', 'oVref', ''),
            ('dmm_Vcc', 'Vcc', 'oVcc', ''),
            ('dmm_isense', 'Isense', 'oIsense', ''),
            ('dmm_3V3', '3V3', 'o3V3', ''),
            ('dmm_0V8', '0V8', 'o0V8', ''),
            ('pic_Status', 'PicStatus 0', 'pic_Status', ''),
            ('pic_ZeroChk', 'PicZeroChk', 'pic_ZeroChk', ''),
            ('pic_vin', 'PicVin', 'pic_Vin', ''),
            ('pic_isense', 'PicIsense', 'pic_isense', ''),
            ('pic_Vfactor', 'PicVfactor', 'pic_Vfactor', ''),
            ('pic_Ifactor', 'PicIfactor', 'pic_Ifactor', ''),
            ('pic_Ioffset', 'PicIoffset', 'pic_Ioffset', ''),
            ('pic_Ithreshold', 'PicIthreshold', 'pic_Ithreshold', ''),
            ))
