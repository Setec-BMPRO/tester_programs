#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2018 SETEC Pty Ltd
"""CN102/3 Initial Test Program."""

import pathlib

import serial
import tester

import share
from . import config, console


class Initial(share.TestSequence):

    """CN102/3 Initial Test Program."""

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.get(self.parameter, uut)
        limits = self.cfg.limits_initial
        Devices.sw_nxp_image = self.cfg.sw_nxp_image
        Sensors.sw_nordic_image = self.cfg.sw_nordic_image
        super().open(limits, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PartCheck', self._step_part_check),
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('PgmARM', self.devices['progARM'].program),
            tester.TestStep('Program', self._step_program),
            tester.TestStep('TestArm', self._step_test_arm),
            tester.TestStep('TankSense', self._step_tank_sense),
            tester.TestStep('Bluetooth', self._step_bluetooth),
            tester.TestStep('CanBus', self._step_canbus),
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
        dev['rla_reset'].set_on()   # Disable ARM to Nordic RESET

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the Nordic BLE module."""
        mes['JLink']()

    @share.teststep
    def _step_test_arm(self, dev, mes):
        """Test the ARM device."""
        dev['rla_reset'].set_off()  # Allow ARM to Nordic RESET
        cn102 = dev['cn102']
        cn102.open()
        cn102.brand(self.cfg.hw_version, self.sernum, self.cfg.banner_lines)

    @share.teststep
    def _step_tank_sense(self, dev, mes):
        """Activate tank sensors and read."""
        dev['cn102']['ADC_SCAN'] = 100
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
        reply = dev['pi_bt'].scan_advert_sernum(self.sernum)
        mes['scan_ser'].sensor.store(reply is not None)
        mes['scan_ser']()

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        mes['cn102_can_bind'](timeout=10)


class Devices(share.Devices):

    """Devices."""

    sw_nxp_image = None     # ARM software image

    def open(self):
        """Create all Instruments."""
        fixture = '028468'
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('rla_reset', tester.Relay, 'RLA1'),    # 1k RESET to 3V3
                ('rla_s1', tester.Relay, 'RLA4'),
                ('rla_s2', tester.Relay, 'RLA5'),
                ('rla_s3', tester.Relay, 'RLA6'),
                ('rla_s4', tester.Relay, 'RLA7'),
                ('JLink', tester.JLink, 'JLINK'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # ARM device programmer
        arm_port = share.config.Fixture.port(fixture, 'ARM')
        self['progARM'] = share.programmer.ARM(
            arm_port,
            pathlib.Path(__file__).parent / self.sw_nxp_image,
            crpmode=False,
            bda4_signals=True  #Use BDA4 serial lines for RESET & BOOT
            )
        # Serial connection to the console
        con_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        con_ser.port = arm_port
        # CN102 Console driver
        self['cn102'] = console.Console(con_ser)
        # Bluetooth connection to server
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth(
            share.config.System.ble_url())

    def reset(self):
        """Reset instruments."""
        self['cn102'].close()
        self['dcs_vin'].output(0.0, False)
        for rla in ('rla_reset', 'rla_s1', 'rla_s2', 'rla_s3', 'rla_s4'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    projectfile = 'cn102.jflash'
    sw_nordic_image = None

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['mirscan'] = sensor.MirrorReadingBoolean()
        self['oVin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['o3V3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['sw1'] = sensor.Res(dmm, high=7, low=3, rng=10000, res=0.1)
        self['sw2'] = sensor.Res(dmm, high=8, low=4, rng=10000, res=0.1)
        self['microsw'] = sensor.Res(dmm, high=9, low=5, rng=10000, res=0.1)
        self['oSnEntry'] = sensor.DataEntry(
            message=tester.translate('cn102_initial', 'msgSnEntry'),
            caption=tester.translate('cn102_initial', 'capSnEntry'))
        # Console sensors
        cn102 = self.devices['cn102']
        for name, cmdkey in (
                ('CANBIND', 'CAN_BIND'),
                ('tank1', 'TANK1'),
                ('tank2', 'TANK2'),
                ('tank3', 'TANK3'),
                ('tank4', 'TANK4'),
            ):
            self[name] = sensor.KeyedReading(cn102, cmdkey)
        self['JLink'] = sensor.JLink(
            self.devices['JLink'],
            pathlib.Path(__file__).parent / self.projectfile,
            pathlib.Path(__file__).parent / self.sw_nordic_image)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_microsw', 'Part', 'microsw', ''),
            ('dmm_sw1', 'Part', 'sw1', ''),
            ('dmm_sw2', 'Part', 'sw2', ''),
            ('dmm_vin', 'Vin', 'oVin', ''),
            ('dmm_3v3', '3V3', 'o3V3', ''),
            ('ui_serialnum', 'SerNum', 'oSnEntry', ''),
            ('tank1_level', 'Tank', 'tank1', ''),
            ('tank2_level', 'Tank', 'tank2', ''),
            ('tank3_level', 'Tank', 'tank3', ''),
            ('tank4_level', 'Tank', 'tank4', ''),
            ('cn102_can_bind', 'CAN_BIND', 'CANBIND', ''),
            ('scan_ser', 'ScanSer', 'mirscan',
                'Scan for serial number over bluetooth'),
            ('JLink', 'ProgramOk', 'JLink', 'Programmed'),
            ))
