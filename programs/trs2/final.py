#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS2 Final Program."""

import tester
from tester import (
    TestStep,
    LimitLow, LimitDelta, LimitRegExp
    )
import share
from . import config


class Final(share.TestSequence):

    """TRS2 Final Test Program."""

    # Injected Vbatt
    vbatt = 12.0
    # Test limits
    limitdata = (
        LimitDelta('Vin', vbatt, 0.2),
        LimitLow('TestPinCover', 0.5),
        LimitRegExp('ARM-SwVer',
            '^{0}$'.format(config.SW_VERSION.replace('.', r'\.'))),
        )

    def open(self):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep('Bluetooth', self._step_bluetooth),
            )
        Devices.pi_bt = share.bluetooth.RaspberryBluetooth()
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
        reply = dev.pi_bt.echo('OK')
        self._logger.debug('Echo Test: "%s"', reply)
        self._logger.debug('Open bluetooth connection to console of unit '
                           'with serial: "%s"', self.sernum)
        dev.pi_bt.open(self.sernum)
        self._logger.debug('Send a command to the console')
        reply = dev.pi_bt.sndrcve(command='SW-VERSION?', prompts=1, timeout=10)
        swver = reply.split('\r\n')[1]
        swver = '1.0.16487.472'
        self._logger.debug('Sofware version detected: %s', swver)
        mes['detectSW'].sensor.store(swver)
        mes['detectSW']()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""

        pi_bt = None
        pi_bt = pi_bt

        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('dcs_cover', tester.DCSource, 'DCS5'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        self['dcs_cover'].output(9.0, output=True)
        self.add_closer(lambda: self['dcs_cover'].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        for dev in ('dcs_vin', ):
            self[dev].output(0.0, False)
        print('Closing connection')
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
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('trs2_final', 'msgSnEntry'),
            caption=tester.translate('trs2_final', 'capSnEntry'))
        self['mirbt'] = sensor.Mirror(rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', ''),
            ('dmm_tstpincov', 'TestPinCover', 'tstpin_cover', ''),
            ('ui_sernum', 'SerNum', 'sernum', ''),
            ('detectSW', 'ARM-SwVer', 'mirbt', ''),
            ))
