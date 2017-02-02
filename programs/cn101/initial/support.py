#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CN101 Initial Test Program."""

import os
import inspect
from pydispatch import dispatcher
import share
import tester
from . import limit
from .. import console


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        # Power RS232 + Fixture Trek2.
        self.dcs_vcom = tester.DCSource(devices['DCS1'])
        # Power unit under test.
        self.dcs_vin = tester.DCSource(devices['DCS2'])
        self.rla_reset = tester.Relay(devices['RLA1'])
        self.rla_boot = tester.Relay(devices['RLA2'])
        self.rla_s1 = tester.Relay(devices['RLA4'])
        self.rla_s2 = tester.Relay(devices['RLA5'])
        self.rla_s3 = tester.Relay(devices['RLA6'])
        self.rla_s4 = tester.Relay(devices['RLA7'])
        # ARM device programmer
        file = os.path.join(os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe()))),
            limit.ARM_BIN)
        self.programmer = share.ProgramARM(
            limit.ARM_PORT, file, crpmode=False,
            boot_relay=self.rla_boot, reset_relay=self.rla_reset)
        # Serial connection to the CN101 console
        self.cn101_ser = tester.SimSerial(
            simulation=self._fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self.cn101_ser.port = limit.ARM_PORT
        # CN101 Console driver
        self.cn101 = console.Console(self.cn101_ser)
        # Auto add prompt to puts strings
        self.cn101.puts_prompt = '\r\n> '
        # Serial connection to the BLE module
        ble_ser = tester.SimSerial(
            simulation=self._fifo, baudrate=115200, timeout=0.1, rtscts=True)
        # Set port separately, as we don't want it opened yet
        ble_ser.port = limit.BLE_PORT
        self.ble = share.BleRadio(ble_ser)

    def reset(self):
        """Reset instruments."""
        self.cn101.close()
        self.dcs_vin.output(0.0, False)
        for rla in (self.rla_reset, self.rla_boot, self.rla_s1, self.rla_s2,
                        self.rla_s3, self.rla_s4):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        dmm = logical_devices.dmm
        cn101 = logical_devices.cn101
        sensor = tester.sensor
        self.oMirBT = sensor.Mirror()
        self.oMirCAN = sensor.Mirror(rdgtype=sensor.ReadingString)
        self.microsw = sensor.Res(dmm, high=7, low=3, rng=10000, res=0.1)
        self.sw1 = sensor.Res(dmm, high=8, low=4, rng=10000, res=0.1)
        self.sw2 = sensor.Res(dmm, high=9, low=5, rng=10000, res=0.1)
        self.oVin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self.o3V3 = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self.oSnEntry = sensor.DataEntry(
            message=tester.translate('cn101_initial', 'msgSnEntry'),
            caption=tester.translate('cn101_initial', 'capSnEntry'))
        self.oCANBIND = console.Sensor(cn101, 'CAN_BIND')
        self.oSwVer = console.Sensor(
            cn101, 'SW_VER', rdgtype=sensor.ReadingString)
        self.oBtMac = console.Sensor(
            cn101, 'BT_MAC', rdgtype=sensor.ReadingString)
        self.tank1 = console.Sensor(cn101, 'TANK1')
        self.tank2 = console.Sensor(cn101, 'TANK2')
        self.tank3 = console.Sensor(cn101, 'TANK3')
        self.tank4 = console.Sensor(cn101, 'TANK4')

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensor."""
        self.oMirBT.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.dmm_microsw = Measurement(limits['Part'], sense.microsw)
        self.dmm_sw1 = Measurement(limits['Part'], sense.sw1)
        self.dmm_sw2 = Measurement(limits['Part'], sense.sw2)
        self.detectBT = Measurement(limits['DetectBT'], sense.oMirBT)
        self.dmm_vin = Measurement(limits['Vin'], sense.oVin)
        self.dmm_3v3 = Measurement(limits['3V3'], sense.o3V3)
        self.ui_serialnum = Measurement(limits['SerNum'], sense.oSnEntry)
        self.cn101_swver = Measurement(limits['SwVer'], sense.oSwVer)
        self.cn101_btmac = Measurement(limits['BtMac'], sense.oBtMac)
        self.cn101_s1 = Measurement(limits['Tank'], sense.tank1)
        self.cn101_s2 = Measurement(limits['Tank'], sense.tank2)
        self.cn101_s3 = Measurement(limits['Tank'], sense.tank3)
        self.cn101_s4 = Measurement(limits['Tank'], sense.tank4)
        self.cn101_can_bind = Measurement(limits['CAN_BIND'], sense.oCANBIND)
        self.cn101_rx_can = Measurement(limits['CAN_RX'], sense.oMirCAN)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # PowerReset:
        self.reset = tester.SubStep((
            tester.DcSubStep(setting=((d.dcs_vin, 0.0), ), delay=1.0),
            tester.DcSubStep(setting=((d.dcs_vin, 12.0), ), delay=15.0),
            ))
        # TankSense:
        self.tank = tester.SubStep((
            tester.RelaySubStep(
                relays=((d.rla_s1, True), (d.rla_s2, True),
                        (d.rla_s3, True), (d.rla_s4, True), ), delay=0.2),
            tester.MeasureSubStep(
                (m.cn101_s1, m.cn101_s2, m.cn101_s3, m.cn101_s4), timeout=5),
            ))
