#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BLE2CAN Initial Program."""

import serial
import tester
from tester import (
    LimitLow, LimitHigh, LimitDelta, LimitPercent,
    LimitBoolean, LimitRegExp, LimitInteger
    )
import share
from . import console
from . import config


class Initial(share.TestSequence):

    """BLE2CAN Initial Test Program."""

    # Injected Vbatt
    vbatt = 12.0
    # Test limits
    limitdata = (
        LimitDelta('Vin', 12.0, 0.5, doc='Input voltage present'),
        LimitPercent('3V3', 3.3, 0.5, doc='3V3 present'),
        LimitPercent('5V', 5.0, 0.5, doc='5V present'),
        LimitHigh('RedLedOff', 3.1, doc='Led off'),
        LimitDelta('RedLedOn', 0.45, 0.05, doc='Led on'),
        LimitHigh('BlueLedOff', 3.1, doc='Led off'),
        LimitDelta('BlueLedOn', 0.3, 0.09, doc='Led on'),
        LimitHigh('GreenLedOff', 3.1, doc='Led off'),
        LimitLow('GreenLedOn', 0.2, doc='Led on'),
        LimitLow('TestPinCover', 0.5, doc='Cover in place'),
        LimitRegExp('SwVer',
            '^{0}$'.format(config.SW_VERSION.replace('.', r'\.')),
            doc='Software version'),
        LimitRegExp('BtMac', share.bluetooth.MAC.line_regex,
            doc='Valid MAC address'),
        LimitBoolean('DetectBT', True, doc='MAC address detected'),
        LimitInteger('CAN_BIND', 1 << 28, doc='CAN bus bound'),
        )

    def open(self, uut):
        """Prepare for testing."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('Prepare', self._step_prepare),
            tester.TestStep('TestArm', self._step_test_arm),
            tester.TestStep('Bluetooth', self._step_bluetooth),
            tester.TestStep('CanBus', self._step_canbus),
            )
        self.sernum = None

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Set the Input DC voltage to 12V.

        """
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        mes['dmm_tstpincov'](timeout=5)
        dev['dcs_vin'].output(self.vbatt, True)
        self.measure(('dmm_vin', 'dmm_3v3', 'dmm_5v'), timeout=5)

    @share.teststep
    def _step_test_arm(self, dev, mes):
        """Test operation."""
        dev['rla_wdog'].disable()
        ble2can = dev['ble2can']
        ble2can.open()
        ble2can.brand(config.HW_VERSION, self.sernum)
        self.measure(
            ('SwVer', 'dmm_redoff', 'dmm_blueoff', 'dmm_greenoff'),
            timeout=5)
        ble2can.override(share.console.parameter.OverrideTo.force_on)
        self.measure(
            ('dmm_redon', 'dmm_blueon', 'dmm_greenon'), timeout=5)
        ble2can.override(share.console.parameter.OverrideTo.force_off)
        self.measure(
            ('dmm_redoff' , 'dmm_blueoff', 'dmm_greenoff'), timeout=5)
        ble2can.override(share.console.parameter.OverrideTo.normal)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        btmac = share.bluetooth.MAC(mes['BtMac']().reading1)
        dev['rla_pair_btn'].press()
        self._reset_unit()
        self._logger.debug('Scanning for Bluetooth MAC: "%s"', btmac)
        ble = dev['ble']
        ble.open()
        reply = ble.scan(btmac)
        ble.close()
        self._logger.debug('Bluetooth MAC detected: %s', reply)
        mes['detectBT'].sensor.store(reply)
        mes['detectBT']()

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        dev['rla_pair_btn'].release()
        self._reset_unit()
        mes['CANbind'](timeout=10)
# The present software release does not have CAN tunneling
#        ble2cantunnel = dev['ble2cantunnel']
#        ble2cantunnel.open()
#        mes['TunnelSwVer']()
#        ble2cantunnel.close()

    def _reset_unit(self):
        """Reset the unit."""
        dev = self.devices
        dev['rla_wdog'].enable()
        dev['rla_reset'].pulse(0.1)
        dev['rla_wdog'].disable()
        dev['ble2can'].banner()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vfix', tester.DCSource, 'DCS1'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('dcs_cover', tester.DCSource, 'DCS5'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_wdog', tester.Relay, 'RLA2'),
                ('rla_pair_btn', tester.Relay, 'RLA8'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Some more obvious ways to use the relays
        wdog = self['rla_wdog']
        wdog.disable = wdog.set_on
        wdog.enable = wdog.set_off
        pair = self['rla_pair_btn']
        pair.press = pair.set_on
        pair.release = pair.set_off
        # Serial connection to the console
        ble2can_ser = serial.Serial(baudrate=115200, timeout=15.0)
        # Set port separately, as we don't want it opened yet
        ble2can_ser.port = share.fixture.port('030451', 'ARM')
        # Console driver
        self['ble2can'] = console.Console(ble2can_ser)
        # Tunneled Console driver
        tunnel = tester.CANTunnel(
            self.physical_devices['CAN'],
            tester.devphysical.can.SETECDeviceID.ble2can)
        self['ble2cantunnel'] = console.Console(tunnel)
        # Serial connection to the BLE module
        ble_ser = serial.Serial(baudrate=115200, timeout=5.0, rtscts=True)
        # Set port separately, as we don't want it opened yet
        ble_ser.port = share.fixture.port('030451', 'BLE')
        self['ble'] = share.bluetooth.BleRadio(ble_ser)
        # Apply power to fixture circuits.
        self['dcs_vfix'].output(9.0, output=True, delay=5)
        self.add_closer(lambda: self['dcs_vfix'].output(0.0, output=False))
        self['dcs_cover'].output(9.0, output=True)
        self.add_closer(lambda: self['dcs_cover'].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        self['ble2can'].close()
        self['ble2cantunnel'].close()
        self['dcs_vin'].output(0.0, False)
        for rla in ('rla_reset', 'rla_wdog', 'rla_pair_btn'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['vin'].doc = 'X1/X2'
        self['3v3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['3v3'].doc = 'U4 output'
        self['5v'] = sensor.Vdc(dmm, high=4, low=1, rng=10, res=0.01)
        self['5v'].doc = 'U5 output'
        self['red'] = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.01)
        self['red'].doc = 'Led cathode'
        self['green'] = sensor.Vdc(dmm, high=6, low=1, rng=10, res=0.01)
        self['green'].doc = 'Led cathode'
        self['blue'] = sensor.Vdc(dmm, high=7, low=1, rng=10, res=0.01)
        self['blue'].doc = 'Led cathode'
        self['tstpin_cover'] = sensor.Vdc(
            dmm, high=16, low=1, rng=100, res=0.01)
        self['tstpin_cover'].doc = 'Photo sensor'
        self['mirbt'] = sensor.Mirror(rdgtype=sensor.ReadingBoolean)
        # Console sensors
        ble2can = self.devices['ble2can']
        ble2cantunnel = self.devices['ble2cantunnel']
        self['CANbind'] = share.console.Sensor(ble2can, 'CAN_BIND')
        for name, cmdkey in (
                ('BtMac', 'BT_MAC'),
                ('SwVer', 'SW_VER'),
            ):
            self[name] = share.console.Sensor(
                ble2can, cmdkey, rdgtype=sensor.ReadingString)
        self['TunnelSwVer'] = share.console.Sensor(
            ble2cantunnel, 'SW_VER', rdgtype=sensor.ReadingString)
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('ble2can_initial', 'msgSnEntry'),
            caption=tester.translate('ble2can_initial', 'capSnEntry'))
        self['sernum'].doc = 'Barcode scanner'


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', 'Input voltage'),
            ('dmm_3v3', '3V3', '3v3', '3V3 rail voltage'),
            ('dmm_5v', '5V', '5v', '5V rail voltage'),
            ('dmm_redoff', 'RedLedOff', 'red', 'Red led off'),
            ('dmm_redon', 'RedLedOn', 'red', 'Red led on'),
            ('dmm_greenoff', 'GreenLedOff', 'green', 'Green led off'),
            ('dmm_greenon', 'GreenLedOn', 'green', 'Green led on'),
            ('dmm_blueoff', 'BlueLedOff', 'blue', 'Blue led off'),
            ('dmm_blueon', 'BlueLedOn', 'blue', 'Blue led on'),
            ('dmm_tstpincov', 'TestPinCover', 'tstpin_cover',
                'Cover over BC2 test pins'),
            ('BtMac', 'BtMac', 'BtMac', 'MAC address'),
            ('detectBT', 'DetectBT', 'mirbt', 'Scanned MAC address'),
            ('SwVer', 'SwVer', 'SwVer', 'Unit software version'),
            ('ui_sernum', 'SerNum', 'sernum', 'Unit serial number'),
            ('CANbind', 'CAN_BIND', 'CANbind', 'CAN bound'),
            ('TunnelSwVer', 'SwVer', 'TunnelSwVer',
                'Unit software version'),
            ))
