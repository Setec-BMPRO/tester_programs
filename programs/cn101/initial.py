#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CN101 Initial Test Program."""

import os
import inspect
import serial
import tester
from tester import (
    TestStep,
    LimitLow, LimitRegExp, LimitBoolean, LimitDelta, LimitPercent, LimitInteger
    )
import share
from . import console
from . import config


class Initial(share.TestSequence):

    """CN101 Initial Test Program."""

    # ARM software image file
    arm_file = 'cn101_{0}.bin'.format(config.SW_VERSION)
    # Test limits
    limitdata = (
        LimitLow('Part', 20.0),
        LimitDelta('Vin', 8.0, 0.5),
        LimitPercent('3V3', 3.30, 3.0),
        LimitInteger('CAN_BIND', 1 << 28),
        LimitRegExp(
            'SwVer', '^{0}$'.format(config.SW_VERSION.replace('.', r'\.'))),
        LimitRegExp('BtMac', share.bluetooth.MAC.line_regex),
        LimitBoolean('DetectBT', True),
        LimitInteger('Tank', 5),
        )

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('PartCheck', self._step_part_check),
            TestStep('PowerUp', self._step_power_up),
            TestStep('Program', self.devices['programmer'].program),
            TestStep('TestArm', self._step_test_arm),
            TestStep('TankSense', self._step_tank_sense),
            TestStep('Bluetooth', self._step_bluetooth),
            TestStep('CanBus', self._step_canbus),
            )
        self.sernum = None

    @share.teststep
    def _step_part_check(self, dev, mes):
        """Measure Part detection microswitches."""
        self.measure(('dmm_microsw', 'dmm_sw1', 'dmm_sw2'), timeout=5)

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_serialnum')
        dev['dcs_vin'].output(8.6, output=True)
        self.measure(('dmm_vin', 'dmm_3v3', ), timeout=5)

    @share.teststep
    def _step_test_arm(self, dev, mes):
        """Test the ARM device."""
        cn101 = dev['cn101']
        cn101.open()
        cn101.brand(config.HW_VERSION, self.sernum, dev['rla_reset'])
        mes['cn101_swver']()

    @share.teststep
    def _step_tank_sense(self, dev, mes):
        """Activate tank sensors and read."""
        dev['cn101']['ADC_SCAN'] = 100
        self.relay(
            (('rla_s1', True), ('rla_s2', True),
             ('rla_s3', True), ('rla_s4', True), ),
            delay=0.2)
        self.measure(
            ('cn101_s1', 'cn101_s2', 'cn101_s3', 'cn101_s4'), timeout=5)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        dev['dcs_vin'].output(0.0, delay=1.0)
        dev['dcs_vin'].output(12.0, delay=15.0)
        btmac = share.bluetooth.MAC(mes['cn101_btmac']().reading1)
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
        mes['cn101_can_bind'](timeout=10)
        cn101tunnel = dev['cn101tunnel']
        cn101tunnel.open()
        mes['TunnelSwVer']()
        cn101tunnel.close()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vcom', tester.DCSource, 'DCS1'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_boot', tester.Relay, 'RLA2'),
                ('rla_s1', tester.Relay, 'RLA4'),
                ('rla_s2', tester.Relay, 'RLA5'),
                ('rla_s3', tester.Relay, 'RLA6'),
                ('rla_s4', tester.Relay, 'RLA7'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # ARM device programmer
        arm_port = share.fixture.port('028468', 'ARM')
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['programmer'] = share.programmer.ARM(
            arm_port,
            os.path.join(folder, Initial.arm_file),
            crpmode=False,
            boot_relay=self['rla_boot'],
            reset_relay=self['rla_reset'])
        # Serial connection to the console
        cn101_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        cn101_ser.port = arm_port
        # CN101 Console driver
        self['cn101'] = console.DirectConsole(cn101_ser)
        # Tunneled Console driver
        tunnel = share.can.Tunnel(
            self.physical_devices['CAN'], tester.CAN.DeviceID.cn101)
        self['cn101tunnel'] = console.TunnelConsole(tunnel)
        # Serial connection to the BLE module
        ble_ser = serial.Serial(baudrate=115200, timeout=0.1, rtscts=True)
        # Set port separately, as we don't want it opened yet
        ble_ser.port = share.fixture.port('028468', 'BLE')
        self['ble'] = share.bluetooth.BleRadio(ble_ser)
        # Apply power to fixture circuits.
        self['dcs_vcom'].output(12.0, output=True, delay=5)
        self.add_closer(lambda: self['dcs_vcom'].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        self['cn101'].close()
        self['cn101tunnel'].close()
        self['dcs_vin'].output(0.0, False)
        for rla in (
                'rla_reset', 'rla_boot', 'rla_s1',
                'rla_s2', 'rla_s3', 'rla_s4',
                ):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['oMirBT'] = sensor.Mirror()
        self['microsw'] = sensor.Res(dmm, high=7, low=3, rng=10000, res=0.1)
        self['sw1'] = sensor.Res(dmm, high=8, low=4, rng=10000, res=0.1)
        self['sw2'] = sensor.Res(dmm, high=9, low=5, rng=10000, res=0.1)
        self['oVin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['o3V3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['oSnEntry'] = sensor.DataEntry(
            message=tester.translate('cn101_initial', 'msgSnEntry'),
            caption=tester.translate('cn101_initial', 'capSnEntry'))
        # Console sensors
        cn101 = self.devices['cn101']
        cn101tunnel = self.devices['cn101tunnel']
        for name, cmdkey in (
                ('oCANBIND', 'CAN_BIND'),
                ('tank1', 'TANK1'),
                ('tank2', 'TANK2'),
                ('tank3', 'TANK3'),
                ('tank4', 'TANK4'),
            ):
            self[name] = share.console.Sensor(cn101, cmdkey)
        for device, name, cmdkey in (
                (cn101, 'oSwVer', 'SW_VER'),
                (cn101, 'oBtMac', 'BT_MAC'),
                (cn101tunnel, 'TunnelSwVer', 'SW_VER'),
            ):
            self[name] = share.console.Sensor(
                device, cmdkey, rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_microsw', 'Part', 'microsw', ''),
            ('dmm_sw1', 'Part', 'sw1', ''),
            ('dmm_sw2', 'Part', 'sw2', ''),
            ('detectBT', 'DetectBT', 'oMirBT', ''),
            ('dmm_vin', 'Vin', 'oVin', ''),
            ('dmm_3v3', '3V3', 'o3V3', ''),
            ('ui_serialnum', 'SerNum', 'oSnEntry', ''),
            ('cn101_swver', 'SwVer', 'oSwVer', ''),
            ('cn101_btmac', 'BtMac', 'oBtMac', ''),
            ('cn101_s1', 'Tank', 'tank1', ''),
            ('cn101_s2', 'Tank', 'tank2', ''),
            ('cn101_s3', 'Tank', 'tank3', ''),
            ('cn101_s4', 'Tank', 'tank4', ''),
            ('cn101_can_bind', 'CAN_BIND', 'oCANBIND', ''),
            ('TunnelSwVer', 'SwVer', 'TunnelSwVer', ''),
            ))
