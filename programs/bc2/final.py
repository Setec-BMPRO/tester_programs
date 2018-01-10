#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC2 Final Program."""

import tester
from tester import (
    TestStep,
    LimitLow, LimitDelta, LimitRegExp
    )
import share
from . import config


class Final(share.TestSequence):

    """BC2 Final Test Program."""

    limitdata = (
        LimitDelta('Vin', 13.5, 0.5),
        LimitLow('TestPinCover', 0.5),
        LimitDelta('Shunt', 50.0, 100.0),
        LimitRegExp('ARM-SwVer',
            '^{0}$'.format(config.SW_VERSION.replace('.', r'\.'))),
        )

    def open(self):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep('Bluetooth', self._step_bluetooth),
            TestStep('Cal', self._step_cal),
            )
        Devices.pi_bt = share.bluetooth.RaspberryBluetooth()
        self.sernum = None

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        self.measure(
            ('dmm_tstpincov', 'dmm_vin', ), timeout=5)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        reply = dev.pi_bt.echo('OK')
        self._logger.debug('Echo Test: "%s"', reply)
        self._logger.debug('Open bluetooth connection to console of unit '
                           'with serial: "%s"', self.sernum)
        dev.pi_bt.open(self.sernum)
        self._logger.debug('Send a command to the console')
        reply = dev.pi_bt.action(command='SW-VERSION?', prompts=1, timeout=10)
        swver = reply.split('\r\n')[1]
        self._logger.debug('Sofware version detected: %s', swver)
        mes['detectSW'].sensor.store(swver)
        mes['detectSW']()

    @share.teststep
    def _step_cal(self, dev, mes):
        """Prepare to run a test."""


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""

        pi_bt = None
        pi_bt = pi_bt

        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('acsource', tester.ACSource, 'ACS'),
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_cover', tester.DCSource, 'DCS5'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        self['dcs_cover'].output(9.0, output=True, delay=5)
        self.add_closer(lambda: self['dcs_cover'].output(0.0, output=False))
        self['acsource'].output(voltage=240.0, output=True, delay=1.0)
        self.add_closer(lambda: self['acsource'].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        self.pi_bt.close()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['tstpin_cover'] = sensor.Vdc(
            dmm, high=16, low=1, rng=100, res=0.01)
        self['shunt'] = sensor.Vdc(
            dmm, high=3, low=1, rng=10, res=0.001, scale=1000)
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('bc2_final', 'msgSnEntry'),
            caption=tester.translate('bc2_final', 'capSnEntry'))
        self['mirbt'] = sensor.Mirror(rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', ''),
            ('dmm_tstpincov', 'TestPinCover', 'tstpin_cover', ''),
            ('dmm_shunt', 'Shunt', 'shunt', ''),
            ('ui_sernum', 'SerNum', 'sernum', ''),
            ('detectSW', 'ARM-SwVer', 'mirbt', ''),
            ))
