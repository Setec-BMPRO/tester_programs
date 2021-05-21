#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVSWT101 Final Test Program."""

import time, serial
import tester

import share
from . import config, device,  arduino


class Final(share.TestSequence):

    """RVSWT101 Final Test Program."""

    ble_adtype_manufacturer = '255'

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.Config.get(self.parameter, uut)
        Devices.fixture_num = self.cfg['fixture_num']
        super().open(self.cfg['limits_fin'], Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('Bluetooth', self._step_bluetooth),
            )
        self.sernum = None
        self.cfg['limits_fin']

    @share.teststep
    def _step_bluetooth(self, dev, mes):
        """Test the Bluetooth interface."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_serialnum')
        # Lookup the MAC address from the server
        mac = dev['serialtomac'].blemac_get(self.sernum)
        mes['ble_mac'].sensor.store(mac)
        mes['ble_mac']()

        # Tell user to push unit's button after clicking OK
        #mes['ui_buttonpress']()

        # Push either 4 or 6 bottons depending on the UUT hardware configuration
        buttons = 4
        
        #TODO
        #if hwType == 'button': buttons = 6
        
        for buttonNum, buttonPress in enumerate(['buttonPress_{0}'.format(n+1) for n in range(buttons)]):
            buttonNum +=1

            # Trigger a buttonpress (buttonpress_n action is defined in the Sensors class below)
            mes[buttonPress]()

            # Scan for the bluetooth transmission
            # Reply is like this: {
            #   'ad_data': {'255': '1f050112022d624c3a00000300d1139e69'},
            #   'rssi': -80,
            #   }

            reply = dev['pi_bt'].scan_advert_blemac(mac, timeout=20)
            mes['scan_mac'].sensor.store(reply is not None)
            mes['scan_mac']()

            packet = reply['ad_data'][self.ble_adtype_manufacturer]
            dev['decoder'].packet = device.Packet(packet)
            self.measure(('cell_voltage', 'switch_type', ))


class Devices(share.Devices):

    """Devices."""

    fixture_num = None      # Fixture number

    def open(self):
        """Create all Instruments."""
        # Connection to RaspberryPi bluetooth server
        self['pi_bt'] = share.bluetooth.RaspberryBluetooth(
            share.config.System.ble_url())
        # Connection to Serial To MAC server
        self['serialtomac'] = share.bluetooth.SerialToMAC()
        # BLE Packet decoder
        self['decoder'] = tester.CANPacketDevice()

        # Serial connection to the Arduino console
        ard_ser = serial.Serial(baudrate=115200, timeout=20.0)
        # Set port separately, as we don't want it opened yet
        ard_ser.port = share.config.Fixture.port(self.fixture_num, 'ARDUINO')
        self['ard'] = arduino.Arduino(ard_ser)
        self['ard'].verbose = True

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


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        sensor = tester.sensor
        self['mirscan'] = sensor.MirrorReadingBoolean()
        self['mirmac'] = sensor.MirrorReadingString()
        self['SnEntry'] = sensor.DataEntry(
            message=tester.translate('rvswt101_final', 'msgSnEntry'),
            caption=tester.translate('rvswt101_final', 'capSnEntry'))
        self['ButtonPress'] = sensor.OkCan(
            message=tester.translate('rvswt101_final', 'msgPressButton'),
            caption=tester.translate('rvswt101_final', 'capPressButton'))
        decoder = self.devices['decoder']
        self['cell_voltage'] = sensor.KeyedReading(decoder, 'cell_voltage')
        self['switch_type'] = sensor.KeyedReading(decoder, 'switch_type')

        # Arduino sensors - sensor_name, key
        ard = self.devices['ard']
        for name, cmdkey in (
                ('debugOn', 'DEBUG'),
                ('debugOff', 'QUIET'),
                ('buttonPress_1', 'PRESS_BUTTON_1'),
                ('buttonPress_2', 'PRESS_BUTTON_2'),
                ('buttonPress_3', 'PRESS_BUTTON_3'),
                ('buttonPress_4', 'PRESS_BUTTON_4'),
                ('buttonPress_5', 'PRESS_BUTTON_5'),
                ('buttonPress_6', 'PRESS_BUTTON_6'),
                ('retractAll', 'RETRACT_ACTUATORS'),
                ('ejectDut', 'EJECT_DUT'),
                ('4ButtonModel', '4BUTTON_MODEL'),
                ('6ButtonModel', '6BUTTON_MODEL'),
            ):
            self[name] = sensor.KeyedReadingString(ard, cmdkey)


class Measurements(share.Measurements):

    """Measurements."""
    def open(self):
        """Create all Measurements.
           measurement_name, limit_name, sensor_name, doc"""

        self.create_from_names((
            ('ui_serialnum', 'SerNum', 'SnEntry', ''),
            ('ble_mac', 'BleMac', 'mirmac', 'Get MAC address from server'),
            ('ui_buttonpress', 'ButtonOk', 'ButtonPress', ''),
            ('debugOn', 'Reply', 'debugOn', ''),
            ('debugOff', 'Reply', 'debugOff', ''),
            ('buttonPress_1', 'Reply', 'buttonPress_1', ''),
            ('buttonPress_2', 'Reply', 'buttonPress_2', ''),
            ('buttonPress_3', 'Reply', 'buttonPress_3', ''),
            ('buttonPress_4', 'Reply', 'buttonPress_4', ''),
            ('buttonPress_5', 'Reply', 'buttonPress_5', ''),
            ('buttonPress_6', 'Reply', 'buttonPress_6', ''),
            ('retractAll', 'Reply', 'retractAll', ''),
            ('ejectDut', 'Reply', 'ejectDut', ''),
            ('4ButtonModel', 'Reply', '4ButtonModel', ''),
            ('6ButtonModel', 'Reply', '6ButtonModel', ''),
            ('scan_mac', 'ScanMac', 'mirscan',
                'Scan for MAC address over bluetooth'),
            ('cell_voltage', 'CellVoltage', 'cell_voltage',
                'Button cell charged'),
            ('switch_type', 'SwitchType', 'switch_type',
                'Switch type'),
            ))
