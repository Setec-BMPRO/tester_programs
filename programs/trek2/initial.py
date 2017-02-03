#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Initial Test Program."""

import os
import inspect
import time
import tester
from tester.testlimit import (
    lim_hilo_delta, lim_hilo_percent, lim_hilo_int, lim_hilo,
    lim_lo, lim_string, lim_boolean)
import share
from . import console

BIN_VERSION = '1.4.13801.139'   # Software binary version

# Hardware version (Major [1-255], Minor [1-255], Mod [character])
HW_VER = (4, 0, 'A')

# Serial port for the Trek2 in the fixture. Used for the CAN Tunnel port
CAN_PORT = {'posix': '/dev/ttyUSB1', 'nt': 'COM11'}[os.name]
# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM10'}[os.name]
# Software image filename
ARM_BIN = 'Trek2_{}.bin'.format(BIN_VERSION)
# CAN echo request messages
CAN_ECHO = 'TQQ,16,0'
# Input voltage to power the unit
VIN_SET = 12.75

# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28

LIMITS = tester.testlimit.limitset((
    lim_hilo_delta('Vin', 12.0, 0.5),
    lim_hilo_percent('3V3', 3.3, 3.0),
    lim_lo('BkLghtOff', 0.5),
    lim_hilo('BkLghtOn', 3.465, 4.545),     # 40mA = 4V with 100R (1%)
    lim_string('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    lim_string('CAN_RX', r'^RRQ,16,0'),
    lim_hilo_int('CAN_BIND', _CAN_BIND),
    lim_string('SwVer', '^{}$'.format(BIN_VERSION.replace('.', r'\.'))),
    lim_boolean('Notify', True),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None


class Initial(tester.TestSequence):

    """Trek2 Initial Test Program."""

    def __init__(self, physical_devices):
        """Create the test program as a linear sequence.

           @param physical_devices Physical instruments of the Tester

        """
        super().__init__()
        self._devices = physical_devices
        self._limits = LIMITS
        self.sernum = None

    def open(self, parameter):
        """Prepare for testing."""
        sequence = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('Program', self._step_program, not self.fifo),
            tester.TestStep('TestArm', self._step_test_arm),
            tester.TestStep('CanBus', self._step_canbus),
            )
        super().open(sequence)
        global d, s, m
        d = LogicalDevices(self._devices, self.fifo)
        s = Sensors(d, self._limits)
        m = Measurements(s, self._limits)
        d.dcs_Vcom.output(12.0, output=True)
        time.sleep(2)   # Allow OS to detect the new ports

    def close(self):
        """Finished testing."""
        global m, d, s
        d.dcs_Vcom.output(0.0, output=False)
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _step_power_up(self):
        """Apply input 12Vdc and measure voltages."""
        self.fifo_push(
            ((s.oSnEntry, ('A1526040123', )), (s.oVin, 12.0), (s.o3V3, 3.3), ))

        self._sernum = share.get_sernum(
            self.uuts, self._limits['SerNum'], m.ui_SnEntry)
        d.dcs_Vin.output(VIN_SET, output=True)
        tester.MeasureGroup((m.dmm_Vin, m.dmm_3V3), timeout=5)

    def _step_program(self):
        """Program the ARM device."""
        d.programmer.program()

    def _step_test_arm(self):
        """Test the ARM device."""
        for str in (
                ('Banner1\r\nBanner2', ) +  # Banner lines
                ('', ) + ('success', ) * 2 + ('', ) * 2 +
                (BIN_VERSION, )
                ):
            d.trek2.puts(str)

        d.trek2.open()
        d.rla_reset.pulse(0.1)
        d.trek2.action(None, delay=1.5, expected=2)  # Flush banner
        d.trek2['UNLOCK'] = True
        d.trek2['HW_VER'] = HW_VER
        d.trek2['SER_ID'] = self.sernum
        d.trek2['NVDEFAULT'] = True
        d.trek2['NVWRITE'] = True
        m.trek2_SwVer.measure()

    def _step_canbus(self):
        """Test the Can Bus."""
        for str in ('0x10000000', '', '0x10000000', '', ''):
            d.trek2.puts(str)
        d.trek2.puts('RRQ,16,0,7,0,0,0,0,0,0,0\r\n', addprompt=False)

        m.trek2_can_bind.measure(timeout=10)
        d.trek2.can_testmode(True)
        time.sleep(2)   # Let other CAN messages come in...
        # From here, Command-Response mode is broken by the CAN debug messages!
        d.trek2['CAN'] = CAN_ECHO
        echo_reply = d.trek2_ser.readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        s.oMirCAN.store(echo_reply)
        m.rx_can.measure()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        # Power RS232 + Fixture Trek2.
        self.dcs_Vcom = tester.DCSource(devices['DCS1'])
        self.dcs_Vin = tester.DCSource(devices['DCS2'])
        self.rla_reset = tester.Relay(devices['RLA1'])
        self.rla_boot = tester.Relay(devices['RLA2'])
        # ARM device programmer
        file = os.path.join(os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe()))),
            ARM_BIN)
        self.programmer = share.ProgramARM(
            ARM_PORT, file, crpmode=False,
            boot_relay=self.rla_boot, reset_relay=self.rla_reset)
        # Serial connection to the Trek2 console
        self.trek2_ser = tester.SimSerial(
            simulation=fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self.trek2_ser.port = ARM_PORT
        # Trek2 Console driver
        self.trek2 = console.DirectConsole(self.trek2_ser)

    def reset(self):
        """Reset instruments."""
        self.trek2.close()
        self.dcs_Vin.output(0.0, False)
        for rla in (self.rla_reset, self.rla_boot):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        trek2 = logical_devices.trek2
        sensor = tester.sensor
        self.oMirCAN = sensor.Mirror(rdgtype=sensor.ReadingString)
        self.oVin = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self.o3V3 = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self.oBkLght = sensor.Vdc(dmm, high=1, low=4, rng=10, res=0.01)
        self.oSnEntry = sensor.DataEntry(
            message=tester.translate('trek2_initial', 'msgSnEntry'),
            caption=tester.translate('trek2_initial', 'capSnEntry'),
            timeout=300)
        self.oCANBIND = console.Sensor(trek2, 'CAN_BIND')
        self.oSwVer = console.Sensor(
            trek2, 'SW_VER', rdgtype=sensor.ReadingString)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.rx_can = Measurement(limits['CAN_RX'], sense.oMirCAN)
        self.dmm_Vin = Measurement(limits['Vin'], sense.oVin)
        self.dmm_3V3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_BkLghtOff = Measurement(limits['BkLghtOff'], sense.oBkLght)
        self.dmm_BkLghtOn = Measurement(limits['BkLghtOn'], sense.oBkLght)
        self.ui_SnEntry = Measurement(limits['SerNum'], sense.oSnEntry)
        self.trek2_can_bind = Measurement(limits['CAN_BIND'], sense.oCANBIND)
        self.trek2_SwVer = Measurement(limits['SwVer'], sense.oSwVer)
