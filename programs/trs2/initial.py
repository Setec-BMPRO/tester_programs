#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""TRS2 Initial Program."""

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

    """TRS2 Initial Test Program."""

    # Injected Vbatt
    vbatt = 12.0
    # Injected Vbrake for offset calibration
    vbrake_offset = 0.3
    # Brake current
    ibrake = 1.0
    # Common limits
    _common = (
        LimitDelta('Vin', vbatt, 0.2, doc='Input voltage present'),
        LimitPercent('3V3', 3.3, 0.5, doc='3V3 present'),
        LimitLow('BrakeOff', 0.5, doc='Brakes off'),
        LimitDelta('BrakeOn', vbatt, (0.5, 0), doc='Brakes on'),
        LimitDelta('BrakeOffset', vbrake_offset, 0.1,
            doc='Input voltage present'),
        LimitDelta('BrakeGain', vbatt, 0.1, doc='Input voltage present'),
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
        LimitLow('TestPinCover', 0.5, doc='Cover in place'),
        LimitRegExp('ARM-SwVer',
            '^{0}$'.format(config.SW_VERSION.replace('.', r'\.')),
            doc='Software version'),
        LimitLow('ARM-FaultCode', 0, doc='No error'),
        LimitPercent('ARM-Vbatt', vbatt, 4.6, delta=0.088,
            doc='Voltage present'),
        LimitPercent('ARM-Vbrake', vbatt, 4.6, delta=0.088,
            doc='Voltage present'),
        LimitPercent('ARM-Vbatt-Cal', vbatt, 0.6, delta=0.033,
            doc='Voltage present'),
        LimitPercent('ARM-Vbrake-Cal', vbatt, 0.6, delta=0.033,
            doc='Voltage present'),
        LimitPercent('ARM-Ibrake', ibrake, 4.0, delta=0.82,
            doc='Brake current flowing'),
        LimitDelta('ARM-Vpin', 0.0, 0.2, doc='No voltage drop'),
        LimitRegExp('BtMac', share.bluetooth.MAC.line_regex,
            doc='Valid MAC address '),
        LimitBoolean('DetectBT', True, doc='MAC address detected'),
        )
    # Variant specific configuration data. Indexed by test program parameter.
    config_data = {
        'STD': {
            'Limits': _common + (
                LimitDelta('RemoteOn', vbatt, (0.25, 0), doc='Remote on'),
                LimitLow('RemoteOff', 0.5, doc='Remote off'),
                ),
            },
        'AS': {
            'Limits': _common + (
                LimitLow('RemoteOn', 0.5, doc='Not applicable'),
                LimitLow('RemoteOff', 0.5, doc='Not applicable'),
                ),
            },
        }

    def open(self, uut):
        """Prepare for testing."""
        super().open(
            self.config_data[self.parameter]['Limits'],
            Devices, Sensors, Measurements)
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep('Operation', self._step_operation),
            TestStep('Calibrate', self._step_calibrate),
            TestStep('Bluetooth', self._step_bluetooth),
            )
        self.sernum = None

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Set the Input DC voltage to 12V.

        """
        dev['trs2'].open()
        mes['dmm_tstpincov'](timeout=5)
        dev['dcs_vin'].output(self.vbatt, True)
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        dev['dcl_brake'].output(0.1, output=True)
        self.measure(
            ('dmm_vin', 'dmm_3v3', 'dmm_BrakeOff'), timeout=5)
        dev['rla_pin'].remove()
        mes['dmm_BrakeOn'](timeout=5)
        dev['rla_pin'].insert()

    @share.teststep
    def _step_operation(self, dev, mes):
        """Test the operation of LEDs."""
        trs2 = dev['trs2']
        trs2.brand(config.HW_VERSION, self.sernum)
        self.measure(
            ('arm_swver', 'arm_fltcode', 'dmm_redoff', 'dmm_greenoff'),
            timeout=5)
        trs2.override(share.console.parameter.OverrideTo.force_on)
        self.measure(
            ('dmm_lighton', 'dmm_remoteon', 'dmm_redon', 'dmm_greenon',
             'dmm_blueon'), timeout=5)
        trs2.override(share.console.parameter.OverrideTo.force_off)
        self.measure(
            ('dmm_lightoff', 'dmm_remoteoff', 'dmm_redoff', 'dmm_greenoff',
             'dmm_blueoff'), timeout=5)
        trs2.override(share.console.parameter.OverrideTo.normal)

    @share.teststep
    def _step_calibrate(self, dev, mes):
        """Calibrate BRAKE input voltage.

        Vbatt is at 12V, console is open.

        """
        trs2 = dev['trs2']
        brakes = dev['dcs_brakes']
        dev['rla_pin'].remove()
        self.measure(
            ('arm_Vbatt', 'arm_Vbrake', ), timeout=5)
        dev['rla_pin'].insert()     # Pin IN for calibration
        # Offset calibration at low voltage
        brakes.output(self.vbrake_offset, output=True)
        dmm_V = mes['dmm_BrakeOffset'].stable(delta=0.001).reading1
        trs2['VBRAKE_OFFSET'] = dmm_V
        # Gain calibration at nominal voltage
        brakes.output(self.vbatt, output=True)
        dmm_V = mes['dmm_BrakeGain'].stable(delta=0.001).reading1
        trs2['VBRAKE_GAIN'] = dmm_V
        # Save new calibration settings
        trs2['NVWRITE'] = True
        self.measure(
            ('arm_Vbatt_cal', 'arm_Vbrake_cal', ), timeout=5)
        dev['rla_pin'].remove()
        dev['dcl_brake'].output(self.ibrake)
        self.measure(
            ('arm_Ibrake', 'arm_Vpin', ),
            timeout=5)
        dev['dcl_brake'].output(0.0)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        btmac = share.bluetooth.MAC(mes['arm_btmac']().reading1)
        self._logger.debug('Scanning for Bluetooth MAC: "%s"', btmac)
        ble = dev['ble']
        ble.open()
        reply = ble.scan(btmac)
        ble.close()
        self._logger.debug('Bluetooth MAC detected: %s', reply)
        mes['detectBT'].sensor.store(reply)
        mes['detectBT']()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_vfix', tester.DCSource, 'DCS1'),
                ('dcs_vin', tester.DCSource, 'DCS2'),
                ('dcs_brakes', tester.DCSource, 'DCS3'),
                ('dcs_cover', tester.DCSource, 'DCS5'),
                ('dcl_brake', tester.DCLoad, 'DCL5'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_wdg', tester.Relay, 'RLA2'),  #Normally closed
                ('rla_pin', tester.Relay, 'RLA3'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Some more obvious ways to use this relay
        pin = self['rla_pin']
        pin.insert = pin.set_off
        pin.remove = pin.set_on
        # Serial connection to the console
        trs2_ser = serial.Serial(baudrate=115200, timeout=15.0)
        # Set port separately, as we don't want it opened yet
        trs2_ser.port = share.config.Fixture.port('030451', 'ARM')
        # Console driver
        self['trs2'] = console.Console(trs2_ser)
        # Serial connection to the BLE module
        ble_ser = serial.Serial(baudrate=115200, timeout=0.1, rtscts=True)
        # Set port separately, as we don't want it opened yet
        ble_ser.port = share.config.Fixture.port('030451', 'BLE')
        self['ble'] = share.bluetooth.BleRadio(ble_ser)
        # Enable the watchdog
        self['rla_wdg'].set_on()
        self.add_closer(self['rla_wdg'].set_off)
        # Apply power to fixture circuits.
        self['dcs_vfix'].output(9.0, output=True, delay=5)
        self.add_closer(lambda: self['dcs_vfix'].output(0.0, output=False))
        self['dcs_cover'].output(9.0, output=True)
        self.add_closer(lambda: self['dcs_cover'].output(0.0, output=False))

    def reset(self):
        """Reset instruments."""
        self['trs2'].close()
        for dev in ('dcs_vin', 'dcs_brakes', ):
            self[dev].output(0.0, False)
        self['dcl_brake'].output(0.0, False)
        for rla in ('rla_reset', 'rla_pin', ):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['vin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['vin'].doc = 'Across X1-X3'
        self['3v3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['3v3'].doc = 'U1 output'
        self['red'] = sensor.Vdc(dmm, high=2, low=2, rng=10, res=0.01)
        self['red'].doc = 'Across led'
        self['green'] = sensor.Vdc(dmm, high=2, low=3, rng=10, res=0.01)
        self['green'].doc = 'Across led'
        self['blue'] = sensor.Vdc(dmm, high=2, low=4, rng=10, res=0.01)
        self['blue'].doc = 'Across led'
        self['brake'] = sensor.Vdc(dmm, high=12, low=1, rng=100, res=0.01)
        self['brake'].doc = 'Brakes output'
        self['light'] = sensor.Vdc(dmm, high=13, low=1, rng=100, res=0.01)
        self['light'].doc = 'Lights output'
        self['remote'] = sensor.Vdc(dmm, high=14, low=1, rng=100, res=0.01)
        self['remote'].doc = 'Remote output'
        self['tstpin_cover'] = sensor.Vdc(
            dmm, high=16, low=1, rng=100, res=0.01)
        self['tstpin_cover'].doc = 'Photo sensor'
        self['mirbt'] = sensor.MirrorReadingBoolean()
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('trs2_initial', 'msgSnEntry'),
            caption=tester.translate('trs2_initial', 'capSnEntry'))
        self['sernum'].doc = 'Barcode scanner'
        # Console sensors
        trs2 = self.devices['trs2']
        for name, cmdkey in (
                ('arm_BtMAC', 'BT_MAC'),
                ('arm_SwVer', 'SW_VER'),
            ):
            self[name] = sensor.KeyedReadingString(trs2, cmdkey)
        for name, cmdkey, units in (
                ('arm_Fault', 'FAULT_CODE', '0/1'),
                ('arm_Vbatt', 'VBATT', 'V'),
                ('arm_Vbrake', 'VBRAKE', 'V'),
                ('arm_Ibrake', 'IBRAKE', 'A'),
                ('arm_Vpin', 'VPIN', 'V'),
            ):
            self[name] = sensor.KeyedReading(trs2, cmdkey)
            if units:
                self[name].units = units


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_vin', 'Vin', 'vin', 'Input voltage'),
            ('dmm_3v3', '3V3', '3v3', '3V3 rail voltage'),
            ('dmm_BrakeOff', 'BrakeOff', 'brake', 'Brakes output off'),
            ('dmm_BrakeOn', 'BrakeOn', 'brake', 'Brakes output on'),
            ('dmm_BrakeOffset', 'BrakeOffset', 'brake',
                'Calibration input voltage (Offset)'),
            ('dmm_BrakeGain', 'BrakeGain', 'brake',
                'Calibration input voltage (Gain)'),
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
            ('dmm_tstpincov', 'TestPinCover', 'tstpin_cover',
                'Cover over BC2 test pins'),
            ('arm_btmac', 'BtMac', 'arm_BtMAC', 'MAC address'),
            ('detectBT', 'DetectBT', 'mirbt', 'Scanned MAC address'),
            ('arm_swver', 'ARM-SwVer', 'arm_SwVer', 'Unit software version'),
            ('arm_fltcode', 'ARM-FaultCode', 'arm_Fault', 'Fault code'),
            ('arm_Vbatt', 'ARM-Vbatt', 'arm_Vbatt',
                'Vbatt before cal'),
            ('arm_Vbrake', 'ARM-Vbrake', 'arm_Vbrake',
                'Brakes voltage before cal'),
            ('arm_Vbatt_cal', 'ARM-Vbatt-Cal', 'arm_Vbatt',
                'Vbatt after cal'),
            ('arm_Vbrake_cal', 'ARM-Vbrake-Cal', 'arm_Vbrake',
                'Brakes voltage after cal'),
            ('arm_Ibrake', 'ARM-Ibrake', 'arm_Ibrake', 'Brakes current'),
            ('arm_Vpin', 'ARM-Vpin', 'arm_Vpin',
                'Voltage across breakaway switch with pin OUT'),
            ('ui_sernum', 'SerNum', 'sernum', 'Unit serial number'),
            ))
