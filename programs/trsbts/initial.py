#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS-BTS Initial Program."""

import inspect
import os

import serial
import tester
from tester import (
    TestStep,
    LimitLow, LimitDelta, LimitPercent, LimitBoolean, LimitRegExp
    )
import share
from . import console
from . import config


class Initial(share.TestSequence):

    """TRS-BTS Initial Test Program."""

    # Injected Vbatt
    vbatt = 12.0

    limitdata = (
        LimitDelta('Vbat', 12.0, 0.5, doc='Battery input present'),
        LimitDelta('Vin', 8.0, 0.5, doc='Input voltage present'),
        LimitPercent('3V3', 3.3, 1.7, doc='3V3 present'),
        LimitLow('BrakeOff', 0.5, doc='Brakes off'),
        LimitDelta('BrakeOn', vbatt, (0.5, 0), doc='Brakes on'),
        LimitLow('LightOff', 0.5, doc='Lights off'),
        LimitDelta('LightOn', vbatt, (0.25, 0), doc='Lights on'),
        LimitLow('RemoteOff', 0.5, doc='Remote off'),
        LimitDelta('RemoteOn', vbatt, (0.25, 0), doc='Remote on'),
        LimitLow('RedLedOff', 1.0, doc='Led off'),
        LimitDelta('RedLedOn', 1.8, 0.14, doc='Led on'),
        LimitLow('GreenLedOff', 1.0, doc='Led off'),
        LimitDelta('GreenLedOn', 2.5, 0.4, doc='Led on'),
        LimitLow('BlueLedOff', 1.0, doc='Led off'),
        LimitDelta('BlueLedOn', 2.8, 0.14, doc='Led on'),
        LimitDelta('Chem wire', 3.0, 0.4, doc='Voltage present'),
        LimitDelta('Sway- wire', 2.0, 0.4, doc='Voltage present'),
        LimitDelta('Sway+ wire', 1.0, 0.4, doc='Voltage present'),
        LimitRegExp('ARM-SwVer',
            '^{0}$'.format(config.SW_VERSION.replace('.', r'\.')),
            doc='Software version'),
        LimitPercent('ARM-Vbatt', vbatt, 4.8, delta=0.088,
            doc='Voltage present'),
        LimitPercent('ARM-Vbatt-Cal', vbatt, 1.8, delta=0.088,
            doc='Voltage present'),
        LimitDelta('ARM-Vpin', 0.0, 0.2, doc='No voltage drop'),
        LimitRegExp('BleMac', '^[0-9a-f]{12}$',
            doc='Valid MAC address'),
        LimitBoolean('ScanMac', True,
            doc='MAC address detected'),
        )

    def open(self, uut):
        """Prepare for testing."""
        Devices.sw_image = config.SW_VERSION
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep('PgmNordic', self.devices['progNordic'].program),
            TestStep('Operation', self._step_operation),
            TestStep('Calibrate', self._step_calibrate),
            TestStep('Bluetooth', self._step_bluetooth),
            )
        self.sernum = None

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Set the input battery voltage to 12V.

        """
        dev['trsbts'].open()
        dev['dcs_vbat'].output(self.vbatt, True)
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        self.measure(
            ('dmm_vin', 'dmm_3v3', 'dmm_chem', 'dmm_sway-', 'dmm_sway+'),
            timeout=5)
        dev['dcl_brake'].output(0.1, output=True)
        self.measure(
            ('dmm_brakeoff', 'dmm_lightoff'), timeout=5)
        dev['rla_pin'].remove()
        self.measure(
            ('dmm_brakeon', 'dmm_lighton'), timeout=5)
        dev['rla_pin'].insert()

    @share.teststep
    def _step_operation(self, dev, mes):
        """Test the operation of LEDs."""
        trsbts = dev['trsbts']
        trsbts.brand(config.HW_VERSION, self.sernum)
        self.measure(
            ('arm_swver', 'dmm_redoff', 'dmm_greenoff'),
            timeout=5)
        trsbts.override(share.console.parameter.OverrideTo.force_on)
        self.measure(
            ('dmm_remoteon', 'dmm_redon', 'dmm_greenon', 'dmm_blueon'),
            timeout=5)
        trsbts.override(share.console.parameter.OverrideTo.force_off)
        self.measure(
            ('dmm_remoteoff', 'dmm_redoff', 'dmm_greenoff', 'dmm_blueoff'),
            timeout=5)
        trsbts.override(share.console.parameter.OverrideTo.normal)

    @share.teststep
    def _step_calibrate(self, dev, mes):
        """Calibrate BRAKE input voltage.

        Input battery voltage is at 12V, console is open.

        """
        trsbts = dev['trsbts']
        dev['rla_pin'].insert()     # Pin IN for calibration
        mes['arm_vbatt'](timeout=5)
        # Battery calibration at nominal voltage
        dmm_v = mes['dmm_vbat'].stable(delta=0.001).reading1
        trsbts['VBATT_CAL'] = dmm_v
        # Save new calibration settings
        trsbts['NVWRITE'] = True
        mes['arm_vbatt_cal'](timeout=5)
        dev['rla_pin'].remove()
        mes['arm_vpin'](timeout=5)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        dev['dcs_vbat'].output(0.0, delay=0.5)
        dev['trsbts'].port.flushInput()
        dev['dcs_vbat'].output(self.vbatt, delay=0.1)
        # Get the MAC address from the console.
        self.mac = dev['trsbts'].get_mac()
        mes['ble_mac'].sensor.store(self.mac)
        mes['ble_mac']()
        reply = dev['pi_bt'].scan_advert_blemac(self.mac, timeout=20)
        mes['scan_mac'].sensor.store(reply is not None)
        mes['scan_mac']()


class Devices(share.Devices):

    """Devices."""

    sw_image = None

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vfix', tester.DCSource, 'DCS1'),
                ('dcs_vbat', tester.DCSource, 'DCS2'),
                ('dcl_brake', tester.DCLoad, 'DCL5'),
                ('rla_pin', tester.Relay, 'RLA3'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Some more obvious ways to use this relay
        pin = self['rla_pin']
        pin.insert = pin.set_off
        pin.remove = pin.set_on
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        # Nordic NRF52 device programmer
        self['progNordic'] = share.programmer.Nordic(
            os.path.join(folder, self.sw_image),
            folder)
        # Serial connection to the console
        trsbts_ser = serial.Serial(baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        bl652_port = share.config.Fixture.port('034352', 'NORDIC')
        trsbts_ser.port = bl652_port
        # trsbts Console driver
        self['trsbts'] = console.Console(trsbts_ser)
        self['trsbts'].measurement_fail_on_error = False
        # Connection to RaspberryPi bluetooth server
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth(
            share.config.System.ble_url())
        # Connection to Serial To MAC server
        self['serialtomac'] = share.bluetooth.SerialToMAC()
        # Apply power to fixture circuits.
        self['dcs_vfix'].output(9.0, output=True, delay=5)
        self.add_closer(lambda: self['dcs_vfix'].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        self['trsbts'].close()
        self['dcs_vbat'].output(0.0, False)
        self['dcl_brake'].output(0.0, False)
        self['rla_pin'].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vbat'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['vbat'].doc = 'Across X1 and X2'
        self['vin'] = sensor.Vdc(dmm, high=2, low=1, rng=100, res=0.01)
        self['vin'].doc = 'TP17'
        self['3v3'] = sensor.Vdc(dmm, high=3, low=1, rng=10, res=0.01)
        self['3v3'].doc = 'TP1'
        self['red'] = sensor.Vdc(dmm, high=3, low=2, rng=10, res=0.01)
        self['red'].doc = 'Across red led'
        self['green'] = sensor.Vdc(dmm, high=3, low=3, rng=10, res=0.01)
        self['green'].doc = 'Across green led'
        self['blue'] = sensor.Vdc(dmm, high=3, low=4, rng=10, res=0.01)
        self['blue'].doc = 'Across blue led'
        self['chem'] = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.01)
        self['chem'].doc = 'TP11'
        self['sway-'] = sensor.Vdc(dmm, high=6, low=1, rng=10, res=0.01)
        self['sway-'].doc = 'TP12'
        self['sway+'] = sensor.Vdc(dmm, high=7, low=1, rng=10, res=0.01)
        self['sway+'].doc = 'TP13'
        self['brake'] = sensor.Vdc(dmm, high=12, low=1, rng=100, res=0.01)
        self['brake'].doc = 'Brakes output'
        self['light'] = sensor.Vdc(dmm, high=13, low=1, rng=100, res=0.01)
        self['light'].doc = 'Lights output'
        self['remote'] = sensor.Vdc(dmm, high=14, low=1, rng=100, res=0.01)
        self['remote'].doc = 'Remote output'
        self['mirmac'] = sensor.MirrorReadingString()
        self['mirscan'] = sensor.MirrorReadingBoolean()
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('trsbts_initial', 'msgSnEntry'),
            caption=tester.translate('trsbts_initial', 'capSnEntry'))
        self['sernum'].doc = 'Barcode scanner'
        # Console sensors
        trsbts = self.devices['trsbts']
        for name, cmdkey in (
                ('arm_swver', 'SW_VER'),
            ):
            self[name] = sensor.KeyedReadingString(trsbts, cmdkey)
        for name, cmdkey, units in (
                ('arm_vbatt', 'VBATT', 'V'),
                ('arm_vpin', 'VPIN', 'V'),
            ):
            self[name] = sensor.KeyedReading(trsbts, cmdkey)
            if units:
                self[name].units = units


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vbat', 'Vbat', 'vbat', 'Battery input voltage'),
            ('dmm_vin', 'Vin', 'vin', 'Input to 3V3 regulator'),
            ('dmm_3v3', '3V3', '3v3', '3V3 rail voltage'),
            ('dmm_brakeoff', 'BrakeOff', 'brake', 'Brakes output off'),
            ('dmm_brakeon', 'BrakeOn', 'brake', 'Brakes output on'),
            ('dmm_lightoff', 'LightOff', 'light', 'Lights output off'),
            ('dmm_lighton', 'LightOn', 'light', 'Lights output on'),
            ('dmm_remoteoff', 'RemoteOff', 'remote', 'Remote output off'),
            ('dmm_remoteon', 'RemoteOn', 'remote', 'Remote output on'),
            ('dmm_redoff', 'RedLedOff', 'red', 'Red led off'),
            ('dmm_redon', 'RedLedOn', 'red', 'Red led on'),
            ('dmm_greenoff', 'GreenLedOff', 'green', 'Green led off'),
            ('dmm_greenon', 'GreenLedOn', 'green', 'Green led on'),
            ('dmm_blueoff', 'BlueLedOff', 'blue', 'Blue led off'),
            ('dmm_blueon', 'BlueLedOn', 'blue', 'Blue led on'),
            ('dmm_chem', 'Chem wire', 'chem',
                'Check for correct mounting of Chem Select wire'),
            ('dmm_sway-', 'Sway- wire', 'sway-',
                'Check for correct mounting of Sway- wire'),
            ('dmm_sway+', 'Sway+ wire', 'sway+',
                'Check for correct mounting of Sway+ wire'),
            ('ble_mac', 'BleMac', 'mirmac', 'Get MAC address from console'),
            ('scan_mac', 'ScanMac', 'mirscan',
                'Scan for MAC address over bluetooth'),
            ('arm_swver', 'ARM-SwVer', 'arm_swver', 'Unit software version'),
            ('arm_vbatt', 'ARM-Vbatt', 'arm_vbatt',
                'Vbatt before cal'),
            ('arm_vbatt_cal', 'ARM-Vbatt-Cal', 'arm_vbatt',
                'Vbatt after cal'),
            ('arm_vpin', 'ARM-Vpin', 'arm_vpin',
                'Voltage across breakaway switch with pin OUT'),
            ('ui_sernum', 'SerNum', 'sernum', 'Unit serial number'),
            ))