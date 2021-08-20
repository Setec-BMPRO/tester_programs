#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVSWT101 Final Test Program."""

import time

import serial
import tester

import share
from . import config, device, arduino


class Final(share.TestSequence):

    """RVSWT101 Final Test Program."""

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.Config.get(self.parameter, uut)
        self.button_count = self.cfg['button_count']
        buttons_in_use = range(1,  self.button_count+1)
        Devices.fixture_num = self.cfg['fixture_num']
        Devices.button_count = self.button_count
        limits_fin = {4: 'limits_fin_4_button',
                      6: 'limits_fin_6_button'}[Devices.button_count]
        super().open(self.cfg[limits_fin], Devices, Sensors, Measurements)

        self.steps = (
            tester.TestStep('Bluetooth', self._step_bluetooth),
            )
        self.sernum = None
        self.buttons = ()                 # Tuple of 12 or 18 measurement strings
        button_presses = tuple(
            ['buttonPress_{0}'.format(n) for n in buttons_in_use])
        button_measurements = tuple(
            ['buttonMeasure_{0}'.format(n) for n in buttons_in_use])
        button_releases = tuple(
            ['buttonRelease_{0}'.format(n) for n in buttons_in_use])
        for button_press, button_test, button_release in zip(
                button_presses, button_measurements, button_releases):
            self.buttons = self.buttons + (button_press, button_test, button_release)

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_serialnum')
        dev['ble'].uut = self.uuts[0]

        # Measure the MAC to save it in test result data
        mac = dev['ble'].mac
        mes['ble_mac'].sensor.store(mac)
        mes['ble_mac']()

        self.devices.check_uut_in_place()
        if not(self.devices.uut_in_place):
            self.measure(('ui_add_uut',))
            self.devices.check_uut_in_place()
            if not(self.devices.uut_in_place): self.no_uut()

        # Perform button press measurements
        self.measure(self.buttons, timeout=10)

        # Don't bt scan for any measurement from here on
        dev['decoder'].always_scan = False
        self.measure(('cell_voltage', 'switch_type', 'rssi'))

        # Eject the UUT if we make it to the end of the test
        self.devices.eject_uut()

    def no_uut(self):
        """ Create a measurment failure if no UUT is detected in the fixture """
        uut_check = tester.Measurement(
                        tester.LimitBoolean('Detect UUT is in fixture', True,
                        'No UUT was detected in the fixture'),
                        tester.sensor.MirrorReadingBoolean()
                        )
        uut_check.sensor.store(False)
        uut_check()


class Devices(share.Devices):

    """Devices."""

    fixture_num = None      # Fixture number
    button_count = None     # 4 or 6 button selection

    def open(self):
        """Create all Instruments."""
        # BLE MAC & Scanning server
        self['ble'] = tester.BLE((self.physical_devices['BLE'],
                                  self.physical_devices['MAC']))

        # BLE Packet decoder
        self['decoder'] = device.RVSWT101(self['ble'])

        # Serial connection to the Arduino console
        ard_ser = serial.Serial(baudrate=115200, timeout=20.0)
        # Set port separately, as we don't want it opened yet
        ard_ser.port = share.config.Fixture.port(self.fixture_num, 'ARDUINO')
        self['ard'] = arduino.Arduino(ard_ser)
        self['ard'].verbose = False
        # On Linux, the ModemManager service opens the serial port
        # for a while after it appears. Wait for it to release the port.
        retry_max = 10
        for retry in range(retry_max + 1):
            try:
                self['ard'].open()
                break
            except:
                if retry == retry_max:
                    raise
                time.sleep(1)
        self.add_closer(lambda: self['ard'].close())
        time.sleep(2)

        self._retract_all()
        self.check_uut_in_place()
        if not(self.uut_in_place):
            self.exercise_actuators()
        self.set_state()

    def exercise_actuators(self):
        """Exercise routine all actuators
           If UUT is in place, routine will be cancelled"""
        self['ard']['EXERCISE']

    def check_uut_in_place(self):
        """Ask arduino if a UUT is in place"""
        self.uut_in_place = int(self['ard']['UUT'])

    def set_state(self):
        """Set to 4 or 6 button mode"""
        command = {
            4: '4BUTTON_MODEL',
            6: '6BUTTON_MODEL',
            }[self.button_count]
        self['ard'][command]

    def eject_uut(self):
        self['ard']['EJECT_DUT']

    def reset(self):
        """Reset instruments."""
        self['decoder'].reset()
        self._retract_all()

    def _retract_all(self):
        """Retract all button actuators."""
        self['ard']['RETRACT_ACTUATORS']


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        sensor = tester.sensor
        self['mirmac'] = sensor.MirrorReadingString()
        self['SnEntry'] = sensor.DataEntry(
            message=tester.translate('rvswt101_final', 'msgSnEntry'),
            caption=tester.translate('rvswt101_final', 'capSnEntry'))
        self['ButtonPress'] = sensor.OkCan(
            message=tester.translate('rvswt101_final', 'msgPressButton'),
            caption=tester.translate('rvswt101_final', 'capPressButton'))
        self['AddUUT'] = sensor.OkCan(
            message=tester.translate('rvswt101_final', 'msgAddUUT'),
            caption=tester.translate('rvswt101_final', 'capAddUUT'))

        decoder = self.devices['decoder']   #tester.BLE device
        self['cell_voltage'] = sensor.KeyedReading(decoder, 'cell_voltage')
        self['switch_type'] = sensor.KeyedReading(decoder, 'switch_type')
        self['RSSI'] = sensor.KeyedReading(decoder, 'rssi')

        for n in range(1, 7):
            name = 'switch_{0}_measure'.format(n)
            self[name] = sensor.KeyedReading(decoder, 'switch_code')
            self[name].rereadable = True

        # Arduino sensors - sensor_name, key
        ard = self.devices['ard']
        for name, cmdkey in (
                ('debugOn', 'DEBUG'),
                ('debugOff', 'QUIET'),
                ('retractAll', 'RETRACT_ACTUATORS'),
                ('ejectDut', 'EJECT_DUT'),
                ('4ButtonModel', '4BUTTON_MODEL'),
                ('6ButtonModel', '6BUTTON_MODEL'),
                ('exercise_actuators', 'EXERCISE'),
            ):
            self[name] = sensor.KeyedReadingString(ard, cmdkey)

        # Create additional arduino sensors for buttonPress and buttonRelease
        for n in range(1, 7):
            _data = (('buttonPress_{}'.format(n), 'PRESS_BUTTON_{}'.format(n)),
                     ('buttonRelease_{}'.format(n), 'RELEASE_BUTTON_{}'.format(n)))
            for name, cmdkey in (_data):
                self[name] = sensor.KeyedReadingString(ard, cmdkey)


class Measurements(share.Measurements):

    """Measurements."""
    def open(self):
        """Create all Measurements.
           measurement_name, limit_name, sensor_name, doc"""

        self.create_from_names((
            ('ui_serialnum', 'SerNum', 'SnEntry', ''),
            ('ble_mac', 'BleMac', 'mirmac', 'Get MAC address from server'),
            ('ui_add_uut', 'ButtonOk', 'AddUUT', ''),
            ('debugOn', 'Reply', 'debugOn', ''),
            ('debugOff', 'Reply', 'debugOff', ''),
            ('buttonPress_1', 'Reply', 'buttonPress_1', ''),
            ('buttonPress_2', 'Reply', 'buttonPress_2', ''),
            ('buttonPress_3', 'Reply', 'buttonPress_3', ''),
            ('buttonPress_4', 'Reply', 'buttonPress_4', ''),
            ('buttonPress_5', 'Reply', 'buttonPress_5', ''),
            ('buttonPress_6', 'Reply', 'buttonPress_6', ''),
            ('buttonRelease_1', 'Reply', 'buttonRelease_1', ''),
            ('buttonRelease_2', 'Reply', 'buttonRelease_2', ''),
            ('buttonRelease_3', 'Reply', 'buttonRelease_3', ''),
            ('buttonRelease_4', 'Reply', 'buttonRelease_4', ''),
            ('buttonRelease_5', 'Reply', 'buttonRelease_5', ''),
            ('buttonRelease_6', 'Reply', 'buttonRelease_6', ''),
            ('retractAll', 'Reply', 'retractAll', ''),
            ('ejectDut', 'Reply', 'ejectDut', ''),
            ('4ButtonModel', 'Reply', '4ButtonModel', ''),
            ('6ButtonModel', 'Reply', '6ButtonModel', ''),
            ('cell_voltage', 'CellVoltage', 'cell_voltage',
                'Button cell charged'),
            ('switch_type', 'SwitchType', 'switch_type',
                'Switch type'),
            ('rssi', 'RSSI Level', 'RSSI', 'Bluetooth RSSI Level'),
            ('buttonMeasure_1', 'switch_1_pressed', 'switch_1_measure',
                'Button 1 tested'),
            ('buttonMeasure_2', 'switch_2_pressed', 'switch_2_measure',
                'Button 2 tested'),
            ('buttonMeasure_3', 'switch_3_pressed', 'switch_3_measure',
                'Button 3 tested'),
            ('buttonMeasure_4', 'switch_4_pressed', 'switch_4_measure',
                'Button 4 tested'),
            ('buttonMeasure_5', 'switch_5_pressed', 'switch_5_measure',
                'Button 5 tested'),
            ('buttonMeasure_6', 'switch_6_pressed', 'switch_6_measure',
                'Button 6 tested'),
            ('exercise_actuators', 'Reply', 'exercise_actuators', ''),
            ))

        # Suppress signals on these measurements.
        for name in (
                'buttonRelease_1', 'buttonRelease_2', 'buttonRelease_3',
                'buttonRelease_4', 'buttonRelease_5', 'buttonRelease_6',
                'retractAll', 'debugOn', 'debugOff', 'retractAll',
                'ejectDut', '4ButtonModel', '6ButtonModel',
                ):
            self[name].send_signal = False
