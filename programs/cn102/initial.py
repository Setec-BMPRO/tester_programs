#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CN102 Initial Test Program."""

import os
import inspect
import serial
import tester
import share
from . import console
from . import config


class Initial(share.TestSequence):

    """CN102 Initial Test Program."""

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.CN102.select(uut)
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
            tester.TestStep('PgmARM', self.devices['progARM'].program),
            tester.TestStep('PgmNordic', self.devices['progNRF'].program),
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
        dev['dcs_vin'].output(0.0, delay=1.0)
        dev['dcs_vin'].output(12.0, delay=5.0)
        reply = dev['pi_bt'].scan_advert_sernum(self.sernum)
        mes['scan_ser'].sensor.store(reply)
        mes['scan_ser']()

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        mes['cn102_can_bind'](timeout=10)
        cn102tunnel = dev['cn102tunnel']
        cn102tunnel.open()
        mes['TunnelSwVer']()
        cn102tunnel.close()


class Devices(share.Devices):

    """Devices."""

    sw_arm_version = None   # ARM software version
    sw_nrf_version = None   # Nordic software version

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
        # Tunneled Console driver
        tunnel = tester.CANTunnel(
            self.physical_devices['CAN'],
            tester.devphysical.can.DeviceID.cn101)
        self['cn102tunnel'] = console.TunnelConsole(tunnel)
        # Bluetooth connection to server
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth()

    def reset(self):
        """Reset instruments."""
        self['cn102'].close()
        self['cn102tunnel'].close()
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
        self['mirscan'] = sensor.Mirror()
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
        cn102tunnel = self.devices['cn102tunnel']
        for name, cmdkey in (
                ('CANBIND', 'CAN_BIND'),
                ('tank1', 'TANK1'),
                ('tank2', 'TANK2'),
                ('tank3', 'TANK3'),
                ('tank4', 'TANK4'),
            ):
            self[name] = share.console.Sensor(cn102, cmdkey)
        for device, name, cmdkey in (
                (cn102, 'SwVer', 'SW_VER'),
                (cn102tunnel, 'TunnelSwVer', 'SW_VER'),
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
            ('dmm_vin', 'Vin', 'oVin', ''),
            ('dmm_3v3', '3V3', 'o3V3', ''),
            ('ui_serialnum', 'SerNum', 'oSnEntry', ''),
            ('cn102_swver', 'SwArmVer', 'SwVer', ''),
            ('tank1_level', 'Tank', 'tank1', ''),
            ('tank2_level', 'Tank', 'tank2', ''),
            ('tank3_level', 'Tank', 'tank3', ''),
            ('tank4_level', 'Tank', 'tank4', ''),
            ('cn102_can_bind', 'CAN_BIND', 'CANBIND', ''),
            ('TunnelSwVer', 'SwArmVer', 'TunnelSwVer', ''),
            ('scan_ser', 'ScanSer', 'mirscan',
                'Scan for serial number over bluetooth'),
            ))
