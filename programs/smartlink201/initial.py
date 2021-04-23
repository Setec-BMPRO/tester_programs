#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021 SETEC Pty Ltd
"""SmartLink201 Test Programs."""

import inspect
import os

import serial
import tester

import share
from . import config, console


class Initial(share.TestSequence):

    """SmartLink201 Initial Test Program."""

    vin_set = 12.0      # Input voltage (V)
    limitdata = (
        tester.LimitRegExp('SwVer',
            '^{0}$'.format(config.sw_nrf_version.replace('.', r'\.')),
            doc='Correct Software version'),
        tester.LimitRegExp('BleMac', r'^[0-9a-f]{12}$',
            doc='Valid MAC address '),
        tester.LimitLow('PartOk', 2.0, doc='All parts present'),
        tester.LimitLow('S5can', 4e3, doc='S5 CAN ON'),
        tester.LimitLow('S5tank', 2.0, doc='S5 tank ON'),
        tester.LimitDelta('Vbatt', vin_set, 0.5, doc='At nominal'),
        tester.LimitDelta('Vin', vin_set - 2.0, 0.5, doc='At nominal'),
        tester.LimitPercent('3V3', 3.33, 3.0, doc='At nominal'),
        tester.LimitDelta('SL_VbattPre', vin_set, 0.25, doc='Before cal'),
        tester.LimitDelta('SL_Vbatt', vin_set, 0.05, doc='After cal'),
        # Analog tank inputs
        #   Open: approx. > 0xFF0
        #   Short:  Sense 1: 170-200    Sense 2-4: 60-80
        tester.LimitHigh('TankHi', 0xF00),
        tester.LimitLow('TankLo', 0x200),
        )
    analog_read_wait = 2        # Analog read response time
    sernum = None

    def open(self, uut):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('PgmARM', self.devices['progARM'].program),
            tester.TestStep('PgmNordic', self.devices['progNordic'].program),
            tester.TestStep('Nordic', self._step_test_nordic),
            tester.TestStep('Calibrate', self._step_calibrate),
            tester.TestStep('TankSense', self._step_tank_sense),
            )

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply Vbatt and check voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_serialnum')
        self.measure(('dmm_Parts', 'dmm_S5can', 'dmm_S5tank', ), timeout=5)
        dev['dcs_Vbatt'].output(self.vin_set, output=True)
        self.measure(('dmm_Vbatt', 'dmm_Vin', 'dmm_3V3', ), timeout=5)

    @share.teststep
    def _step_test_nordic(self, dev, mes):
        """Test the Nordic device."""
        smartlink201 = dev['smartlink201']
        smartlink201.open()
        # Cycle power to get the Nordic running
        dev['dcs_Vbatt'].output(0, output=True, delay=2)
        dev['dcs_Vbatt'].output(self.vin_set,  output=True)
        mes['dmm_3V3'](timeout=5)
        smartlink201.brand(
            self.sernum, config.product_rev, config.hardware_rev)
        # Save SerialNumber & MAC on a remote server.
        mac = mes['SL_MAC']().reading1
        dev['serialtomac'].blemac_set(self.sernum, mac)
        mes['SL_SwVer']()

    @share.teststep
    def _step_calibrate(self, dev, mes):
        """Calibrate Vbatt."""
        smartlink201 = dev['smartlink201']
        vbatt = mes['dmm_Vbatt'](timeout=5).reading1
        # Adjust Pre & Post reading dependant limits
        self.limits['SL_VbattPre'].adjust(nominal=vbatt)
        self.limits['SL_Vbatt'].adjust(nominal=vbatt)
        mes['SL_VbattPre']()
        smartlink201.vbatt_cal(vbatt)
        mes['SL_Vbatt']()

    @share.teststep
    def _step_tank_sense(self, dev, mes):
        """Tank sensors."""
        smartlink201 = dev['smartlink201']
        smartlink201.analog_read()      # Read all tank sensor inputs
        for index in range(16):         # All analog tank inputs
            name = smartlink201.tank_name(index)
            mes[name]()
        self.relay(                     # Pull down alternate inputs
            (('rla_s1', True), ('rla_s3', True), ),
            delay=self.analog_read_wait)
        smartlink201.analog_read()      # Read all tank sensor inputs
        for index in range(16):         # All analog tank inputs
            name = smartlink201.tank_name(index)
            if not index % 2:           # Every 2nd input is now low
                name += '_L'
            mes[name]()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        fixture = '035827'
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_Vbatt', tester.DCSource, 'DCS2'),
                ('dcs_USB', tester.DCSource, 'DCS3'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_boot', tester.Relay, 'RLA2'),
                ('rla_s1', tester.Relay, 'RLA4'),   # 4k7 pull-down on tanks
                ('rla_s2', tester.Relay, 'RLA5'),
                ('rla_s3', tester.Relay, 'RLA6'),
                ('rla_s4', tester.Relay, 'RLA7'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # ARM device programmer
        arm_port = share.config.Fixture.port(fixture, 'ARM')
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        sw_arm_image = config.sw_arm_image
        self['progARM'] = share.programmer.ARM(
            arm_port,
            os.path.join(folder, sw_arm_image),
            crpmode=False,
            boot_relay=self['rla_boot'],
            reset_relay=self['rla_reset'])
        # Nordic NRF52 device programmer
        sw_nrf_image = config.sw_nrf_image
        self['progNordic'] = share.programmer.Nordic(
            os.path.join(folder, sw_nrf_image),
            folder)
        # Serial connection to the Nordic console
        smartlink201_ser = serial.Serial(baudrate=115200, timeout=5.0)
        #   Set port separately, as we don't want it opened yet
        smartlink201_ser.port = share.config.Fixture.port(fixture, 'NORDIC')
        self['smartlink201'] = console.Console(smartlink201_ser)
        # Connection to Serial To MAC server
        self['serialtomac'] = share.bluetooth.SerialToMAC()
        # Fixture USB power
        self['dcs_USB'].output(8.0, output=True, delay=10)
        self.add_closer(lambda: self['dcs_USB'].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        self['smartlink201'].close()
        self['dcs_Vbatt'].output(0.0, False)
        for rla in (
                'rla_reset', 'rla_boot',
                'rla_s1', 'rla_s2', 'rla_s3', 'rla_s4',
                ):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['Vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['Vin'].doc = 'Vin rail'
        self['3V3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['3V3'].doc = '3V3 rail'
        self['photosense'] = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.1)
        self['photosense'].doc = 'Part detector output'
        self['Vbatt'] = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.01)
        self['Vbatt'].doc = 'X13 pin 1'
        self['S5can'] = sensor.Res(dmm, high=5, low=3, rng=11e3, res=1)
        self['S5can'].doc = 'S5 CAN lines'
        self['S5tank'] = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.01)
        self['S5tank'].doc = 'S5 Tank Type'
        self['SnEntry'] = sensor.DataEntry(
            message=tester.translate('smartlink201_initial', 'msgSnEntry'),
            caption=tester.translate('smartlink201_initial', 'capSnEntry'))
        self['SnEntry'].doc = 'Entered S/N'
        # Console sensors
        smartlink201 = self.devices['smartlink201']
        self['SL_SwVer'] = sensor.KeyedReadingString(smartlink201, 'SW_VER')
        self['SL_SwVer'].doc = 'Nordic software version'
        self['SL_MAC'] = sensor.KeyedReadingString(smartlink201, 'MAC')
        self['SL_MAC'].doc = 'Nordic BLE MAC'
        # Convert "xx:xx:xx:xx:xx:xx(random)" to "xxxxxxxxxxxx"
        self['SL_MAC'].on_read = (
            lambda value: value.replace(':', '').replace(' (random)', '')
            )
        self['SL_Vbatt'] = sensor.KeyedReading(smartlink201, 'BATT')
        self['SL_Vbatt'].doc = 'Nordic Vbatt reading'
        self['SL_Vbatt'].scale = 1000
        # Convert "Current Battery Voltage: xxxxx mV" to "xxxxx"
        self['SL_Vbatt'].on_read = (
            lambda value: value.replace(
                'Current Battery Voltage: ', '').replace(' mV', '')
            )
        for index in range(16):     # 16 analog tank inputs
            name = smartlink201.tank_name(index)
            self[name] = sensor.KeyedReading(smartlink201, name)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_Parts', 'PartOk', 'photosense',
                'All hand loaded parts fitted'),
            ('dmm_S5can', 'S5can', 'S5can',
                'S5 CAN switch ON'),
            ('dmm_S5tank', 'S5tank', 'S5tank',
                'S5 Tank switch ON'),
            ('dmm_Vin', 'Vin', 'Vin', 'Vin rail ok'),
            ('dmm_3V3', '3V3', '3V3', '3V3 rail ok'),
            ('dmm_Vbatt', 'Vbatt', 'Vbatt', 'Actual Vbatt rail'),
            ('ui_serialnum', 'SerNum', 'SnEntry', 'S/N valid'),
            ('SL_SwVer', 'SwVer', 'SL_SwVer', 'Software version correct'),
            ('SL_VbattPre', 'SL_VbattPre', 'SL_Vbatt',
                'Nordic Vbatt before adjustment'),
            ('SL_Vbatt', 'SL_Vbatt', 'SL_Vbatt',
                'Nordic Vbatt after adjustment'),
            ('SL_MAC', 'BleMac', 'SL_MAC', 'Nordic MAC address valid'),
            ))
        for index in range(16):         # All tank inputs High
            name = console.Console.tank_name(index)
            self[name] = tester.Measurement(
                self.limits['TankHi'],
                self.sensors[name],
                doc='Input open circuit')
            if not index % 2:           # S1,S3 tank inputs Low
                self[name + '_L'] = tester.Measurement(
                    self.limits['TankLo'],
                    self.sensors[name],
                    doc='Input pulled down')
