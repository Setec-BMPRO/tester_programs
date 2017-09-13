#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Initial Test Program."""

import os
import inspect
import time
import tester
from tester import (
    TestStep,
    LimitLow, LimitRegExp, LimitDelta,
    LimitPercent, LimitInteger
    )
import share
from . import console


BIN_VERSION = '1.5.15833.150'   # Software binary version

# Hardware version (Major [1-255], Minor [1-255], Mod [character])
HW_VER = (5, 0, 'B')

# Serial port for the Trek2 in the fixture. Used for the CAN Tunnel port
CAN_PORT = share.port('027420', 'CAN')
# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = share.port('027420', 'ARM')
# Software image filename
ARM_FILE = 'Trek2_{0}.bin'.format(BIN_VERSION)
# CAN echo request messages
CAN_ECHO = 'TQQ,16,0'
# Input voltage to power the unit
VIN_SET = 12.75

# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28


class Initial(share.TestSequence):

    """Trek2 Initial Test Program."""

    limitdata = (
        LimitDelta('Vin', VIN_SET - 0.75, 0.5),
        LimitPercent('3V3', 3.3, 3.0),
        LimitLow('BkLghtOff', 0.5),
        LimitDelta('BkLghtOn', 4.0, 0.55),      # 40mA = 4V with 100R (1%)
        LimitRegExp('CAN_RX', r'^RRQ,16,0'),
        LimitInteger('CAN_BIND', _CAN_BIND),
        LimitRegExp('SwVer', '^{0}$'.format(BIN_VERSION.replace('.', r'\.'))),
        )

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerUp', self._step_power_up),
            TestStep('Program', self._step_program, not self.fifo),
            TestStep('TestArm', self._step_test_arm),
            TestStep('CanBus', self._step_canbus),
            )
        self.sernum = None

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Apply input 12Vdc and measure voltages."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_SnEntry')
        dev['dcs_Vin'].output(VIN_SET, output=True)
        self.measure(('dmm_Vin', 'dmm_3V3'), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the ARM device."""
        dev['programmer'].program()

    @share.teststep
    def _step_test_arm(self, dev, mes):
        """Test the ARM device."""
        trek2 = dev['trek2']
        trek2.open()
        dev['rla_reset'].pulse(0.1)
        trek2.action(None, delay=1.5, expected=2)  # Flush banner
        trek2['UNLOCK'] = True
        trek2['HW_VER'] = HW_VER
        trek2['SER_ID'] = self.sernum
        trek2['NVDEFAULT'] = True
        trek2['NVWRITE'] = True
        mes['trek2_SwVer']()

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        mes['trek2_can_bind'](timeout=10)
        trek2 = dev['trek2']
        trek2.can_testmode(True)
        time.sleep(2)   # Let other CAN messages come in...
        # From here, Command-Response mode is broken by the CAN debug messages!
        trek2['CAN'] = CAN_ECHO
        echo_reply = trek2.port.readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        mes['rx_can'].sensor.store(echo_reply)
        mes['rx_can']()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_Vcom', tester.DCSource, 'DCS2'),
                ('dcs_Vin', tester.DCSource, 'DCS3'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_boot', tester.Relay, 'RLA2'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['programmer'] = share.ProgramARM(
            ARM_PORT, os.path.join(folder, ARM_FILE), crpmode=False,
            boot_relay=self['rla_boot'], reset_relay=self['rla_reset'])
        # Serial connection to the console
        trek2_ser = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        trek2_ser.port = ARM_PORT
        # Console driver
        self['trek2'] = console.DirectConsole(trek2_ser)
        # Apply power to fixture circuits.
        self['dcs_Vcom'].output(12.0, output=True, delay=2)
        self.add_closer(lambda: self['dcs_Vcom'].output(0.0, False))

    def reset(self):
        """Reset instruments."""
        self['trek2'].close()
        self['dcs_Vin'].output(0.0, output=False)
        for rla in ('rla_reset', 'rla_boot'):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        trek2 = self.devices['trek2']
        sensor = tester.sensor
        self['oMirCAN'] = sensor.Mirror(rdgtype=sensor.ReadingString)
        self['oVin'] = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.01)
        self['o3V3'] = sensor.Vdc(dmm, high=2, low=1, rng=10, res=0.01)
        self['oBkLght'] = sensor.Vdc(dmm, high=1, low=4, rng=10, res=0.01)
        self['oSnEntry'] = sensor.DataEntry(
            message=tester.translate('trek2_initial', 'msgSnEntry'),
            caption=tester.translate('trek2_initial', 'capSnEntry'),
            timeout=300)
        # Console sensors
        self['oCANBIND'] = console.Sensor(trek2, 'CAN_BIND')
        self['oSwVer'] = console.Sensor(
            trek2, 'SW_VER', rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('rx_can', 'CAN_RX', 'oMirCAN', ''),
            ('dmm_Vin', 'Vin', 'oVin', ''),
            ('dmm_3V3', '3V3', 'o3V3', ''),
            ('dmm_BkLghtOff', 'BkLghtOff', 'oBkLght', ''),
            ('dmm_BkLghtOn', 'BkLghtOn', 'oBkLght', ''),
            ('ui_SnEntry', 'SerNum', 'oSnEntry', ''),
            ('trek2_can_bind', 'CAN_BIND', 'oCANBIND', ''),
            ('trek2_SwVer', 'SwVer', 'oSwVer', ''),
            ))
