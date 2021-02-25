#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2018 SETEC Pty Ltd
"""SmartLink201 Test Programs."""

import inspect
import os

import serial
import tester

import share
from . import config, console


class Initial(share.TestSequence):

    """SmartLink201 Initial Test Program."""

    limitdata = (
        tester.LimitRegExp('SwArmVer',
            '^{0}$'.format(config.sw_arm_version.replace('.', r'\.')),
            doc='ARM Software version'),
        tester.LimitRegExp('SwNrfVer',
            '^{0}$'.format(config.sw_nrf_version.replace('.', r'\.')),
            doc='Nordic Software version'),
        tester.LimitLow('PartCheck', 2.0),
        tester.LimitDelta('Vin', 8.0, 0.5),
        tester.LimitPercent('3V3', 3.30, 3.0),
        tester.LimitInteger('CAN_BIND', 1 << 28),
        tester.LimitBoolean('ScanSer', True,
            doc='Serial number detected'),
        tester.LimitInteger('Tank', 5),
        )

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('PgmARM', self.devices['progARM'].program),
            tester.TestStep('PgmNordic', self.devices['progNRF'].program),
            tester.TestStep('TestArm', self._step_test_arm),
            tester.TestStep('TankSense', self._step_tank_sense),
            tester.TestStep('Bluetooth', self._step_bluetooth),
            tester.TestStep('CanBus', self._step_canbus),
            )
        self.sernum = None

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_serialnum')
        mes['dmm_partcheck'](timeout=5)
        dev['dcs_vin'].output(8.6, output=True)
        dev['dcs_vcom'].output(12.0, output=True, delay=5)
        self.measure(('dmm_vin', 'dmm_3v3', ), timeout=5)

    @share.teststep
    def _step_test_arm(self, dev, mes):
        """Test the ARM device."""
        smartlink201 = dev['smartlink201']
        smartlink201.open()
        # Cycle power to get the Nordic running
        dev['dcs_vin'].output(0, output=True, delay=2)
        dev['dcs_vin'].output(8.6, output=True)
        mes['dmm_3v3'](timeout=5)
        smartlink201.brand(
            config.hw_version,
            self.sernum,
            dev['rla_reset'],
            config.banner_lines
            )
        mes['smartlink201_swver']()

    @share.teststep
    def _step_tank_sense(self, dev, mes):
        """Activate tank sensors and read."""
        dev['smartlink201']['ADC_SCAN'] = 100
        self.relay(
            (('rla_s1', True), ('rla_s2', True),
             ('rla_s3', True), ('rla_s4', True), ),
            delay=0.2)
        self.measure(
            ('tank1_level', 'tank2_level', 'tank3_level', 'tank4_level'),
            timeout=5)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        dev['dcs_vin'].output(0.0, delay=1.0)
        dev['dcs_vin'].output(12.0, delay=5.0)
        dev['smartlink201'].action(None, expected=config.banner_lines)
        reply = dev['pi_bt'].scan_advert_sernum(self.sernum)
        mes['scan_ser'].sensor.store(reply is not None)
        mes['scan_ser']()

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        mes['smartlink201_can_bind'](timeout=10)
        smartlink201tunnel = dev['smartlink201tunnel']
        smartlink201tunnel.open()
        mes['TunnelSwVer']()
        smartlink201tunnel.close()


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
        arm_port = share.config.Fixture.port('028468', 'ARM')
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        sw_arm_image = config.sw_arm_version
        self['progARM'] = share.programmer.ARM(
            arm_port,
            os.path.join(folder, sw_arm_image),
            crpmode=False,
            boot_relay=self['rla_boot'],
            reset_relay=self['rla_reset'])
        # NRF52 device programmer
        sw_nrf_image = config.sw_nrf_version
        self['progNRF'] = share.programmer.Nordic(
            os.path.join(folder, sw_nrf_image),
            folder)
        # Serial connection to the console
        smartlink201_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        smartlink201_ser.port = arm_port
        # SmartLink201 Console driver
        self['smartlink201'] = console.DirectConsole(smartlink201_ser)
        # Tunneled Console driver
        tunnel = tester.CANTunnel(
            self.physical_devices['CAN'],
            tester.devphysical.can.SETECDeviceID.cn101)
        self['smartlink201tunnel'] = console.TunnelConsole(tunnel)
        # Bluetooth connection to server
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth(
            share.config.System.ble_url())

    def reset(self):
        """Reset instruments."""
        self['smartlink201'].close()
        self['smartlink201tunnel'].close()
        for dcs in ('dcs_vin', 'dcs_vcom'):
            self[dcs].output(0.0, False)
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
        self['mirscan'] = sensor.MirrorReadingBoolean()
        self['oVin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['o3V3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['photosense'] = sensor.Res(dmm, high=3, low=2, rng=100, res=0.1)
        self['oSnEntry'] = sensor.DataEntry(
            message=tester.translate('smartlink201_initial', 'msgSnEntry'),
            caption=tester.translate('smartlink201_initial', 'capSnEntry'))
        # Console sensors
        smartlink201 = self.devices['smartlink201']
        smartlink201tunnel = self.devices['smartlink201tunnel']
        for name, cmdkey in (
                ('CANBIND', 'CAN_BIND'),
                ('tank1', 'TANK1'),
                ('tank2', 'TANK2'),
                ('tank3', 'TANK3'),
                ('tank4', 'TANK4'),
            ):
            self[name] = sensor.KeyedReading(smartlink201, cmdkey)
        for device, name, cmdkey in (
                (smartlink201, 'SwVer', 'SW_VER'),
                (smartlink201tunnel, 'TunnelSwVer', 'SW_VER'),
            ):
            self[name] = sensor.KeyedReadingString(device, cmdkey)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_partcheck', 'PartCheck', 'photosense', ''),
            ('dmm_vin', 'Vin', 'oVin', ''),
            ('dmm_3v3', '3V3', 'o3V3', ''),
            ('ui_serialnum', 'SerNum', 'oSnEntry', ''),
            ('smartlink201_swver', 'SwArmVer', 'SwVer', ''),
            ('tank1_level', 'Tank', 'tank1', ''),
            ('tank2_level', 'Tank', 'tank2', ''),
            ('tank3_level', 'Tank', 'tank3', ''),
            ('tank4_level', 'Tank', 'tank4', ''),
            ('smartlink201_can_bind', 'CAN_BIND', 'CANBIND', ''),
            ('TunnelSwVer', 'SwArmVer', 'TunnelSwVer', ''),
            ('scan_ser', 'ScanSer', 'mirscan',
                'Scan for serial number over bluetooth'),
            ))
