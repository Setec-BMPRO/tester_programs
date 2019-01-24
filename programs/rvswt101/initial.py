#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RVSWT101 Initial Test Program."""

import os
import inspect
import serial
import tester
import share
from . import console
from . import config


class Initial(share.TestSequence):

    """RVSWT101 Initial Test Program."""

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.RVSWT101.select(uut)
        limits = self.cfg.limits_initial
        Devices.sw_arm_version = self.cfg.sw_arm_version
        Devices.sw_nrf_version = self.cfg.sw_nrf_version
        super().open(limits, Devices, Sensors, Measurements)
        self.limits['SwArmVer'].adjust(
            '^{0}$'.format(self.cfg.sw_arm_version.replace('.', r'\.')))
        self.limits['SwNrfVer'].adjust(
            '^{0}$'.format(self.cfg.sw_nrf_version.replace('.', r'\.')))
        self.steps = (
            tester.TestStep('PartCheck', self._step_part_check),
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('PgmNordic', self.devices['progNRF'].program),
            tester.TestStep('TestArm', self._step_test_arm),
            tester.TestStep('Bluetooth', self._step_bluetooth),
            )
        self.sernum = None

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_serialnum')
        dev['dcs_vin'].output(8.6, output=True)
        dev['dcs_vcom'].output(12.0, output=True, delay=5)
        self.measure(('dmm_vin', 'dmm_3v3', ), timeout=5)

    @share.teststep
    def _step_test_arm(self, dev, mes):
        """Test the ARM device."""
        # Cycle power to get the Nordic running
        dev['dcs_vin'].output(0, output=True, delay=2)
        dev['dcs_vin'].output(8.6, output=True)
        mes['dmm_3v3'](timeout=5)
        cn102 = dev['cn102']
        cn102.open()
        cn102.brand(
            self.cfg.hw_version, self.sernum, dev['rla_reset'],
            self.cfg.banner_lines)
        mes['cn102_swver']()

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        dev['dcs_vin'].output(0.0, delay=1.0)
        dev['dcs_vin'].output(12.0, delay=5.0)
        reply = dev['pi_bt'].scan_advert_sernum(self.sernum)
        mes['scan_ser'].sensor.store(reply)
        mes['scan_ser']()


class Devices(share.Devices):

    """Devices."""

    sw_nrf_version = None   # Nordic software version

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vin', tester.DCSource, 'DCS1'),
                ('rla_switch', tester.Relay, 'RLA21'),
                ('rla_reset', tester.Relay, 'RLA22'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Relay position selectors
        self['relays'] = []
        for num in range(1, 21):
            self['relays'].append(
                tester.Relay(self.physical_devices['RLA{0}'.format(num)])
                )
        # ARM device programmer
        arm_port = share.fixture.port('028468', 'ARM')
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['progARM'] = share.programmer.ARM(
            arm_port,
            os.path.join(
                folder,
                'cn102_arm_{0}.bin'.format(self.sw_arm_version)),
            crpmode=False,
            boot_relay=self['rla_boot'],
            reset_relay=self['rla_reset'])
        # NRF52 device programmer
        self['progNRF'] = share.programmer.Nordic(
            os.path.join(
                folder,
                'cn102_nrf_{0}.hex'.format(self.sw_nrf_version)),
            folder)
        # Serial connection to the console
        cn102_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        cn102_ser.port = arm_port
        # CN102 Console driver
        self['cn102'] = console.DirectConsole(cn102_ser)
        # Bluetooth connection to server
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth()

    def reset(self):
        """Reset instruments."""
        self['cn102'].close()
        for dcs in ('dcs_vin', ):
            self[dcs].output(0.0, False)
        for rla in ('rla_switch', 'rla_reset'):
            self[rla].set_off()
        for rla in self['relays']:
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['mirscan'] = sensor.Mirror(rdgtype=sensor.ReadingBoolean)
        self['oVin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['oSnEntry'] = sensor.DataEntry(
            message=tester.translate('cn102_initial', 'msgSnEntry'),
            caption=tester.translate('cn102_initial', 'capSnEntry'))
        # Console sensors
        cn102 = self.devices['cn102']
        for name, cmdkey in (
                ('tank1', 'TANK1'),
                ('tank2', 'TANK2'),
                ('tank3', 'TANK3'),
                ('tank4', 'TANK4'),
            ):
            self[name] = share.console.Sensor(cn102, cmdkey)
        for device, name, cmdkey in (
                (cn102, 'SwVer', 'SW_VER'),
            ):
            self[name] = share.console.Sensor(
                device, cmdkey, rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'oVin', ''),
            ('dmm_3v3', '3V3', 'o3V3', ''),
            ('ui_serialnum', 'SerNum', 'oSnEntry', ''),
            ('cn102_swver', 'SwArmVer', 'SwVer', ''),
            ('tank1_level', 'Tank', 'tank1', ''),
            ('tank2_level', 'Tank', 'tank2', ''),
            ('tank3_level', 'Tank', 'tank3', ''),
            ('tank4_level', 'Tank', 'tank4', ''),
            ('scan_ser', 'ScanSer', 'mirscan',
                'Scan for serial number over bluetooth'),
            ))
