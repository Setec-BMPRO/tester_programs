#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CN101 Initial Test Program."""

import os
import inspect
import time
from pydispatch import dispatcher
import tester
from tester.testlimit import (
    lim_hilo_delta, lim_hilo_percent, lim_hilo_int,
    lim_lo, lim_string, lim_boolean)
import share
from . import console

BIN_VERSION = '1.1.13665.176'      # Software binary version
HW_VER = (4, 0, 'A')

# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB1', 'nt': 'COM15'}[os.name]
# ARM software image file
ARM_BIN = 'cn101_{}.bin'.format(BIN_VERSION)
# Serial port for the Bluetooth module.
BLE_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM14'}[os.name]
# CAN echo request messages
CAN_ECHO = 'TQQ,32,0'

# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28

LIMITS = tester.testlimit.limitset((
    lim_lo('Part', 20.0),
    lim_hilo_delta('Vin', 8.0, 0.5),
    lim_hilo_percent('3V3', 3.30, 3.0),
    lim_string('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    lim_string('CAN_RX', r'^RRQ,32,0'),
    lim_hilo_int('CAN_BIND', _CAN_BIND),
    lim_string('SwVer', '^{}$'.format(BIN_VERSION.replace('.', r'\.'))),
    lim_string('BtMac', r'^[0-F]{12}$'),
    lim_boolean('DetectBT', True),
    lim_hilo_int('Tank', 5),
    lim_boolean('Notify', True),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.TestSequence):

    """CN101 Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PartCheck', self._step_part_check),
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('Program', self._step_program, not self.fifo),
            tester.TestStep('TestArm', self._step_test_arm),
            tester.TestStep('TankSense', self._step_tank_sense),
            tester.TestStep('Bluetooth', self._step_bluetooth),
            tester.TestStep('CanBus', self._step_canbus),
            )
        self._limits = LIMITS
        self._sernum = None
        global d, s, m, t
        d = LogicalDevices(self.physical_devices, self.fifo)
        s = Sensors(d, self._limits)
        m = Measurements(s, self._limits)
        t = SubTests(d, m)
        d.dcs_vcom.output(12.0, output=True)
        time.sleep(5)   # Allow OS to detect the new ports

    def close(self):
        """Finished testing."""
        global m, d, s, t
        d.dcs_vcom.output(0.0, output=False)
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _step_part_check(self):
        """Measure Part detection microswitches."""
        self.fifo_push(((s.microsw, 10.0), (s.sw1, 10.0), (s.sw2, 10.0), ))

        tester.MeasureGroup((m.dmm_microsw, m.dmm_sw1, m.dmm_sw2), 5)

    def _step_power_up(self):
        """Apply input 12Vdc and measure voltages."""
        self.fifo_push(
            ((s.oSnEntry, ('A1526040123', )), (s.oVin, 8.0), (s.o3V3, 3.3), ))

        self._sernum = share.get_sernum(
            self.uuts, self._limits['SerNum'], m.ui_serialnum)
        d.dcs_vin.output(8.6, output=True)
        tester.MeasureGroup((m.dmm_vin, m.dmm_3v3, ), timeout=5)

    def _step_program(self):
        """Program the ARM device."""
        d.programmer.program()

    def _step_test_arm(self):
        """Test the ARM device."""
        for str in (('Banner1\r\nBanner2', ) +
                    ('', ) * 5 ):
            d.cn101.puts(str)
        d.cn101.puts(BIN_VERSION, postflush=0)

        d.cn101.open()
        d.rla_reset.pulse(0.1)
        d.cn101.action(None, delay=1.5, expected=0)   # Flush banner
        d.cn101['UNLOCK'] = True
        d.cn101['HW_VER'] = HW_VER
        d.cn101['SER_ID'] = self._sernum
        d.cn101['NVDEFAULT'] = True
        d.cn101['NVWRITE'] = True
        m.cn101_swver.measure()

    def _step_tank_sense(self):
        """Activate tank sensors and read."""
        for str in (('', ) + ('5', ) * 4):
            d.cn101.puts(str)

        d.cn101['ADC_SCAN'] = 100
        t.tank.run()

    def _step_bluetooth(self):
        """Test the Bluetooth interface."""
        d.cn101.puts('001EC030BC15')

        t.reset.run()
        _btmac = m.cn101_btmac.measure().reading1
        self._logger.debug('Scanning for Bluetooth MAC: "%s"', _btmac)
        if self.fifo:
            reply = True
        else:
            d.ble.open()
            reply = d.ble.scan(_btmac)
            d.ble.close()
        self._logger.debug('Bluetooth MAC detected: %s', reply)
        s.oMirBT.store(reply)
        m.detectBT.measure()

    def _step_canbus(self):
        """Test the CAN interface."""
        for str in ('0x10000000', '', '0x10000000', '', ''):
            d.cn101.puts(str)
        d.cn101.puts('RRQ,32,0,7,0,0,0,0,0,0,0\r\n', addprompt=False)

        m.cn101_can_bind.measure(timeout=10)
        d.cn101.can_testmode(True)
        # From here on, Command-Response mode is broken by the CAN debug messages!
        self._logger.debug('CAN Echo Request --> %s', repr(CAN_ECHO))
        d.cn101['CAN'] = CAN_ECHO
        echo_reply = d.cn101_ser.readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        self._logger.debug('CAN Reply <-- %s', repr(echo_reply))
        s.oMirCAN.store(echo_reply)
        m.cn101_rx_can.measure()


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
            ARM_BIN)
        self.programmer = share.ProgramARM(
            ARM_PORT, file, crpmode=False,
            boot_relay=self.rla_boot, reset_relay=self.rla_reset)
        # Serial connection to the CN101 console
        self.cn101_ser = tester.SimSerial(
            simulation=self._fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self.cn101_ser.port = ARM_PORT
        # CN101 Console driver
        self.cn101 = console.Console(self.cn101_ser)
        # Serial connection to the BLE module
        ble_ser = tester.SimSerial(
            simulation=self._fifo, baudrate=115200, timeout=0.1, rtscts=True)
        # Set port separately, as we don't want it opened yet
        ble_ser.port = BLE_PORT
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