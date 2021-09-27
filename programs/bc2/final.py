#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""BC2 Final Program."""

import tester
import share

from . import config, console


class Final(share.TestSequence):

    """BC2 Final Test Program."""

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.get(self.parameter, uut)
        self.limits = self.cfg.limits_final()
        super().open(self.limits, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('Prepare', self._step_prepare),
            tester.TestStep('Bluetooth', self._step_bluetooth),
            tester.TestStep('Calibrate', self._step_cal),
            )
        self.sernum = None

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        dev['dcs_vin'].output(self.cfg.vbatt, True)
        mes['dmm_vin'](timeout=5)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        dev['pi_bt'].open(
            self.sernum, passkey=console.Console.passkey(self.sernum))
        mes['arm_swver']()

    @share.teststep
    def _step_cal(self, dev, mes):
        """Calibrate shunt resistance at 10A.

        Vbatt is at 15V, console is open via bluetooth.

        """
        bc2 = dev['bc2']
        dev['dcl'].output(current=self.cfg.ibatt, output=True, delay=0.5)
        bc2['SHUNT_RES_CAL'] = self.cfg.ibatt
        mes['arm_query_last']()
        bc2['NVWRITE'] = True
        self.measure(('arm_shuntres', 'arm_ibatt', ))
        dev['dcl'].output(0.0, False)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('acsource', tester.ACSource, 'ACS'),
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('dcl', tester.DCLoad, 'DCL1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Power the BCE282-12 in the fixture to provide 10A for calibration.
        self['acsource'].output(voltage=240.0, output=True, delay=1.0)
        self.add_closer(lambda: self['acsource'].output(0.0, output=False))
        # Bluetooth connection to the console
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth(
            share.config.System.ble_url())
        # Bluetooth console driver
        self['bc2'] = console.Console(self['pi_bt'])

    def reset(self):
        """Reset instruments."""
        self['dcs_vin'].output(0.0, False)
        self['dcl'].output(0.0, False)
        self['pi_bt'].close()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.01)
        self['vin'].doc = 'Within Fixture'
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('bc2_final', 'msgSnEntry'),
            caption=tester.translate('bc2_final', 'capSnEntry'))
        self['sernum'].doc = 'Barcode scanner'
        # Console sensors
        bc2 = self.devices['bc2']
        qlr = share.console.Base.query_last_response
        self['arm_swver'] = sensor.KeyedReadingString(bc2, 'SW_VER')
        self['arm_query_last'] = sensor.KeyedReadingString(bc2, qlr)
        for name, cmdkey in (
                ('arm_ShuntRes', 'SHUNT_RES'),
                ('arm_Ibatt', 'BATT_I'),
            ):
            self[name] = sensor.KeyedReading(bc2, cmdkey)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', 'Input voltage'),
            ('ui_sernum', 'SerNum', 'sernum', 'Unit serial number'),
            ('arm_swver', 'ARM-SwVer', 'arm_swver',
                'Detect SW Ver over bluetooth'),
            ('arm_query_last', 'ARM-QueryLast', 'arm_query_last',
                'Response from a calibration command'),
            ('arm_shuntres', 'ARM-ShuntRes', 'arm_ShuntRes',
                'Shunt resistance after cal'),
            ('arm_ibatt', 'ARM-Ibatt', 'arm_Ibatt',
                'Battery current after cal'),
            ))
