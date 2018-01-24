#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS2 Final Program."""

import tester
from tester import (
    TestStep,
    LimitLow, LimitDelta, LimitRegExp
    )
import share
from . import console
from . import config


class Final(share.TestSequence):

    """TRS2 Final Test Program."""

    # Injected Vbatt
    vbatt = 12.0
    # Test limits
    limitdata = (
        LimitDelta('Vin', vbatt, 0.2, doc='Input voltage present'),
        LimitLow('TestPinCover', 0.5, doc='Cover in place'),
        LimitRegExp('ARM-SwVer',
            '^{0}$'.format(config.SW_VERSION.replace('.', r'\.')),
            doc='Software version'),
        )

    def open(self):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep('Bluetooth', self._step_bluetooth),
            )
        self.sernum = None

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        dev['dcs_vin'].output(self.vbatt, True)
        self.measure(
            ('dmm_tstpincov', 'dmm_vin', ), timeout=5)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        self._logger.debug('Open bluetooth connection to console of unit '
                           'with serial: "%s"', self.sernum)
        dev.pi_bt.open(self.sernum)
        self._logger.debug('Send a command to the console')
        mes['arm_swver'](timeout=5)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('dcs_cover', tester.DCSource, 'DCS5'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Apply power to fixture circuits.
        self['dcs_cover'].output(9.0, output=True)
        self.add_closer(lambda: self['dcs_cover'].output(0.0, output=False))
        # Bluetooth connection to the console
        self.pi_bt = share.bluetooth.RaspberryBluetooth()
        # Bluetooth console driver
        self['trs2'] = console.BTConsole(self.pi_bt)

    def reset(self):
        """Reset instruments."""
        self['dcs_vin'].output(0.0, False)
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
            message=tester.translate('trs2_final', 'msgSnEntry'),
            caption=tester.translate('trs2_final', 'capSnEntry'))
        self['sernum'].doc = 'Barcode scanner'
        # Console sensors
        trs2 = self.devices['trs2']
        self['arm_swver'] = share.console.Sensor(
            trs2, 'SW_VER', rdgtype=sensor.ReadingString)


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
            ))
