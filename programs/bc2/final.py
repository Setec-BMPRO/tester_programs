#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC2 Final Program."""

import tester
from tester import (
    TestStep,
    LimitLow, LimitDelta, LimitRegExp, LimitPercent, LimitBetween
    )
import share
from . import console
from . import config


class Final(share.TestSequence):

    """BC2 Final Test Program."""
    # Injected Vbatt
    vbatt = 15.0
    ibatt = 10.0
    # Common limits
    _common = (
        LimitDelta('Vin', vbatt, 0.5, doc='Input voltage present'),
        LimitLow('TestPinCover', 0.5, doc='Cover in place'),
        LimitRegExp('ARM-SwVer',
            '^{0}$'.format(config.SW_VERSION.replace('.', r'\.')),
            doc='Software version'),
        LimitRegExp('ARM-QueryLast', 'cal success:',
            doc='Calibration success'),
        LimitBetween('ARM-I_ADCOffset', -3, 3,
            doc='Current ADC offset calibrated'),
        LimitBetween('ARM-VbattLSB', 2391, 2489,
            doc='LSB voltage calibrated'),
        LimitPercent('ARM-Vbatt', vbatt, 0.5, delta=0.02,
            doc='Battery voltage calibrated'),
        LimitDelta('ARM-IbattZero', 0.0, 0.2,
            doc='Zero battery current calibrated'),
        )
    # Variant specific configuration data. Indexed by test program parameter.
    limitdata = {
        'STD': {
            'Limits': _common + (
                LimitBetween('ARM-ShuntRes', 760000, 840000,
                    doc='Shunt resistance calibrated'),
                LimitPercent('ARM-Ibatt', ibatt, 1, delta=0.015,
                    doc='Battery current calibrated'),
                ),
            },
        'H': {
            'Limits': _common + (
                LimitBetween('ARM-ShuntRes', 65000, 135000,
                    doc='Shunt resistance calibrated'),
                LimitPercent('ARM-Ibatt', ibatt, 3, delta=0.08,
                    doc='Battery current calibrated'),
                ),
            },
        }

    def open(self):
        """Create the test program as a linear sequence."""
        self.config = self.limitdata[self.parameter]
        super().open(
            self.config['Limits'], Devices, Sensors, Measurements)
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep('Bluetooth', self._step_bluetooth),
            TestStep('Calibrate', self._step_cal),
            )
        self.sernum = None

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        dev['dcs_vin'].output(self.vbatt, True)
        self.measure(('dmm_tstpincov', 'dmm_vin', ), timeout=5)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        dev.pi_bt.open(self.sernum)
        mes['arm_swver']()

    @share.teststep
    def _step_cal(self, dev, mes):
        """Calibrate the shunt."""
        bc2 = dev['bc2']
        dmm_v = mes['dmm_vin'].stable(delta=0.001).reading1
        mes['arm_vbatt'].testlimit[0].adjust(nominal=dmm_v)
        bc2['BATT_V_CAL'] = dmm_v
        self.measure(('arm_query_last', 'arm_vbatt'))
        bc2['ZERO_I_CAL'] = 0
        self.measure(('arm_query_last', 'arm_ibattzero'))
        dev['rla_load'].set_on()
        dev['dcl'].output(current=self.ibatt, output=True, delay=0.5)
        bc2['SHUNT_RES_CAL'] = self.ibatt
        mes['arm_query_last']()
        bc2['NVWRITE'] = True
        self.measure(
            ('arm_ioffset', 'arm_shuntres', 'arm_vbattlsb', 'arm_ibatt'))
        dev['dcl'].output(0.0)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('acsource', tester.ACSource, 'ACS'),
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('dcs_cover', tester.DCSource, 'DCS5'),
                ('dcl', tester.DCLoad, 'DCL1'),
                ('rla_load', tester.Relay, 'RLA9'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Apply power to fixture circuits. A BCE282-12 provides 10A for calibration.
        self['dcs_cover'].output(9.0, output=True, delay=5)
        self.add_closer(lambda: self['dcs_cover'].output(0.0, output=False))
        self['acsource'].output(voltage=240.0, output=True, delay=1.0)
        self.add_closer(lambda: self['acsource'].output(0.0, output=False))
        # Bluetooth connection to the console
        self.pi_bt = share.bluetooth.RaspberryBluetooth()
        # Bluetooth console driver
        self['bc2'] = console.Console(self.pi_bt)

    def reset(self):
        """Reset instruments."""
        self['dcs_vin'].output(0.0, False)
        self['dcl'].output(0.0, False)
        self['rla_load'].set_off()
        self.pi_bt.close()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['vin'].doc = 'Within Fixture'
        self['tstpin_cover'] = sensor.Vdc(
            dmm, high=16, low=1, rng=100, res=0.01)
        self['tstpin_cover'].doc = 'Photo sensor'
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('bc2_final', 'msgSnEntry'),
            caption=tester.translate('bc2_final', 'capSnEntry'))
        self['sernum'].doc = 'Barcode scanner'
        # Console sensors
        bc2 = self.devices['bc2']
        qlr = share.console.Base.query_last_response
        self['arm_swver'] = share.console.Sensor(
            bc2, 'SW_VER', rdgtype=sensor.ReadingString)
        self['arm_query_last'] = share.console.Sensor(
            bc2, qlr, rdgtype=sensor.ReadingString)
        for name, cmdkey in (
                ('arm_Ioffset', 'I_ADC_OFFSET'),
                ('arm_ShuntRes', 'SHUNT_RES'),
                ('arm_VbattLSB', 'BATT_V_LSB'),
                ('arm_Vbatt', 'BATT_V'),
                ('arm_Ibatt', 'BATT_I'),
            ):
            self[name] = share.console.Sensor(bc2, cmdkey)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', 'Input voltage'),
            ('dmm_tstpincov', 'TestPinCover', 'tstpin_cover',
                'Cover over BC2 test pins'),
            ('ui_sernum', 'SerNum', 'sernum', 'Unit serial number'),
            ('arm_swver', 'ARM-SwVer', 'arm_swver',
                'Detect SW Ver over bluetooth'),
            ('arm_query_last', 'ARM-QueryLast', 'arm_query_last',
                'Response from a calibration command'),
            ('arm_ioffset', 'ARM-I_ADCOffset', 'arm_Ioffset',
                'Current ADC offset after cal'),
            ('arm_shuntres', 'ARM-ShuntRes', 'arm_ShuntRes',
                'Shunt resistance after cal'),
            ('arm_vbattlsb', 'ARM-VbattLSB', 'arm_VbattLSB',
                'Battery voltage ADC LSB voltage after cal'),
            ('arm_vbatt', 'ARM-Vbatt', 'arm_Vbatt',
                'Battery voltage after cal'),
            ('arm_ibatt', 'ARM-Ibatt', 'arm_Ibatt',
                'Battery current after cal'),
            ('arm_ibattzero', 'ARM-IbattZero', 'arm_Ibatt',
                'Battery current after zero cal'),
            ))
