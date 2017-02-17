#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""J35 Initial Test Program."""

import os
import math
import inspect
import time
import tester
from tester import (
    TestStep,
    LimitLo, LimitBoolean, LimitString,
    LimitHiLo, LimitHiLoDelta, LimitHiLoPercent, LimitHiLoInt
    )
import share
from . import console

ARM_VERSION = '1.1.14080.920'      # ARM versions
# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM16'}[os.name]
# ARM software image file
ARM_FILE = 'j35_{}.bin'.format(ARM_VERSION)
# CAN echo request messages
CAN_ECHO = 'TQQ,36,0'
# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28
# Number of outputs of each product version
OUTPUT_COUNT_A = 7
OUTPUT_COUNT_BC = 14
# Injected voltages
VBAT_INJECT = 12.6          # Battery bus
AUX_SOLAR_INJECT = 13.5     # Aux or Solar inputs
# AC voltage powering the unit
AC_VOLT = 240.0
AC_FREQ = 50.0
# Output set points when running in manual mode
VOUT_SET = 12.8
OCP_SET = 35.0
# Battery load current
BATT_CURRENT = 4.0
# Load on each output channel
LOAD_PER_OUTPUT = 2.0


_COMMON = (
    LimitHiLoDelta('ACin', (AC_VOLT, 5.0)),
    LimitHiLoDelta('Vbus', (AC_VOLT * math.sqrt(2), 10.0)),  # Peak of ACin
    LimitHiLo('12Vpri', (11.5, 13.0)),
    LimitHiLoPercent('Vload', (VOUT_SET, 3.0)), # AC-DC voltage setpoint
    LimitLo('VloadOff', 0.5),
    LimitHiLoDelta('VbatIn', (VBAT_INJECT, 1.0)),
    LimitHiLoDelta('VbatOut', (AUX_SOLAR_INJECT, 0.5)),
    LimitHiLoDelta('Vbat', (VOUT_SET, 0.2)),
    LimitHiLoPercent('VbatLoad', (VOUT_SET, 5.0)),
    LimitHiLoDelta('Vaux', (AUX_SOLAR_INJECT, 0.5)),
    LimitHiLoDelta('Vair', (AUX_SOLAR_INJECT, 0.5)),
    LimitHiLoPercent('3V3U', (3.30, 1.5)),
    LimitHiLoPercent('3V3', (3.30, 1.5)),
    LimitHiLo('15Vs', (11.5, 13.0)),
    LimitHiLoDelta('FanOn', (VOUT_SET, 1.0)),
    LimitLo('FanOff', 0.5),
    LimitString('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    LimitString('ARM-SwVer', '^{}$'.format(ARM_VERSION.replace('.', r'\.'))),
    LimitHiLoDelta(
        'ARM-AuxV', (AUX_SOLAR_INJECT, AUX_SOLAR_INJECT * 0.02 + 0.1)),
    LimitHiLo('ARM-AuxI', (0.0, 1.5)),
    LimitHiLoInt('Vout_OV', 0),     # Over-voltage not triggered
    LimitHiLoDelta('ARM-AcV', (AC_VOLT, AC_VOLT * 0.04 + 1.0)),
    LimitHiLoDelta('ARM-AcF', (AC_FREQ, AC_FREQ * 0.04 + 1.0)),
    LimitHiLo('ARM-SecT', (8.0, 70.0)),
    LimitHiLoDelta('ARM-Vout', (VOUT_SET, VOUT_SET * 0.02 + 0.1)),
    LimitHiLo('ARM-Fan', (0, 100)),
    LimitHiLoDelta('ARM-BattI', (BATT_CURRENT, BATT_CURRENT * 0.017 + 1.0)),
    LimitHiLoDelta('ARM-LoadI', (LOAD_PER_OUTPUT, 0.9)),
    LimitHiLoDelta('CanPwr', (VOUT_SET, 1.8)),
    LimitHiLoInt('LOAD_SET', 0x5555555),
    LimitString('CAN_RX', r'^RRQ,36,0'),
    LimitHiLoInt('CAN_BIND', _CAN_BIND),
    LimitLo('InOCP', VOUT_SET - 1.2),
    LimitLo('FixtureLock', 20),
    LimitBoolean('Notify', True),
    )

LIMITS_A = _COMMON + (
    LimitLo('LOAD_COUNT', OUTPUT_COUNT_A),
    LimitHiLo('OCP', (20.0, 25.0)),
    )

LIMITS_B = _COMMON + (
    LimitLo('LOAD_COUNT', OUTPUT_COUNT_BC),
    LimitHiLo('OCP', (OCP_SET, OCP_SET + 7.0)),
    )

LIMITS_C = _COMMON + (
    LimitLo('LOAD_COUNT', OUTPUT_COUNT_BC),
    LimitHiLo('OCP', (OCP_SET, OCP_SET + 7.0)),
    )

# Variant specific configuration data. Indexed by test program parameter.
#   'Limits': Test limits.
#   'HwVer': Hardware version data.
#   'SolarCan': Enable Solar input & CAN bus tests.
#   'Derate': Derate output current.
CONFIG = {
    'A': {
        'Limits': LIMITS_A,
        'LoadCount': 7,
        'HwVer': (2, 1, 'A'),
        'SolarCan': False,
        'Derate': True,
        },
    'B': {
        'Limits': LIMITS_B,
        'LoadCount': 14,
        'HwVer': (2, 2, 'A'),
        'SolarCan': False,
        'Derate': False,
        },
    'C': {
        'Limits': LIMITS_C,
        'LoadCount': 14,
        'HwVer': (6, 3, 'A'),
        'SolarCan': True,
        'Derate': False,
        },
    }


class Initial(share.TestSequence):

    """J35 Initial Test Program."""

    def open(self):
        """Prepare for testing."""
        self.config = CONFIG[self.parameter]
        super().open(
            self.config['Limits'], LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep(
                'ProgramARM',
                self.devices['program_arm'].program, not self.fifo),
            TestStep('Initialise', self._step_initialise_arm),
            TestStep('Aux', self._step_aux),
            TestStep('Solar', self._step_solar, self.config['SolarCan']),
            TestStep('PowerUp', self._step_powerup),
            TestStep('Output', self._step_output),
            TestStep('RemoteSw', self._step_remote_sw),
            TestStep('Load', self._step_load),
            TestStep('OCP', self._step_ocp),
            TestStep('CanBus', self._step_canbus, self.config['SolarCan']),
            )
        self.sernum = None

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare to run a test.

        Measure fixture lock and part detection micro-switch.
        Apply power to the unit's Battery terminals to power up the micro.

        """
        mes['dmm_lock'](timeout=5)
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        # Apply DC Source to Battery terminals
        dev['dcs_vbat'].output(VBAT_INJECT, True)
        self.measure(('dmm_vbatin', 'dmm_3v3u'), timeout=5)

    @share.teststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device.

        Device is powered by injected Battery voltage.
        Reset the device, set HW & SW versions & Serial number.
        Put device into manual control mode.

        """
        j35 = dev['j35']
        j35.open()
        j35.brand(self.config['HwVer'], self.sernum, dev['rla_reset'])
        j35.manual_mode(start=True) # Start the change to manual mode
        mes['arm_swver']()

    @share.teststep
    def _step_aux(self, dev, mes):
        """Test Auxiliary input."""
        dev['dcs_vaux'].output(AUX_SOLAR_INJECT, True)
        mes['dmm_vaux'](timeout=5)
        dev['dcl_bat'].output(0.5, True)
        j35 = dev['j35']
        j35['AUX_RELAY'] = True
        self.measure(('dmm_vbatout', 'arm_auxv', 'arm_auxi'), timeout=5)
        j35['AUX_RELAY'] = False
        dev['dcs_vaux'].output(0.0, False)
        dev['dcl_bat'].output(0.0)

    @share.teststep
    def _step_solar(self, dev, mes):
        """Test Solar input."""
        dev['dcs_solar'].output(AUX_SOLAR_INJECT, True)
        j35 = dev['j35']
        j35['SOLAR'] = True
        self.measure(('dmm_vbatout', 'dmm_vair'), timeout=5)
        j35['SOLAR'] = False
        dev['dcs_solar'].output(0.0, False)

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit with 240Vac."""
        j35 = dev['j35']
        # Complete the change to manual mode
        j35.manual_mode(vout=VOUT_SET, iout=OCP_SET)
        if self.config['Derate']:
            j35.derate()      # Derate for lower output current
        dev['acsource'].output(voltage=AC_VOLT, output=True)
        self.measure(
            ('dmm_acin', 'dmm_vbus', 'dmm_12vpri', 'arm_vout_ov'),
            timeout=5)
        j35.dcdc_on()
        mes['dmm_vbat'](timeout=5)
        dev['dcs_vbat'].output(0.0, False)
        self.measure(
            ('arm_vout_ov', 'dmm_3v3', 'dmm_15vs', 'dmm_vbat', 'dmm_fanOff',
             'arm_acv', 'arm_acf', 'arm_secT', 'arm_vout', 'arm_fan'),
            timeout=5)
        j35['FAN'] = 100
        mes['dmm_fanOn'](timeout=5)

    @share.teststep
    def _step_output(self, dev, mes):
        """Test the output switches.

        Each output is turned ON in turn.
        All outputs are then left ON.

        """
        j35 = dev['j35']
        j35.load_set(set_on=True, loads=())   # All outputs OFF
        dev['dcl_out'].output(1.0, True)  # A little load on the output
        mes['dmm_vloadoff'](timeout=2)
        for load in range(self.config['LoadCount']):  # One at a time ON
            with tester.PathName('L{0}'.format(load + 1)):
                j35.load_set(set_on=True, loads=(load, ))
                mes['dmm_vload'](timeout=2)
        j35.load_set(set_on=False, loads=())  # All outputs ON

    @share.teststep
    def _step_remote_sw(self, dev, mes):
        """Test the remote switch."""
        dev['rla_loadsw'].set_on()
        mes['dmm_vloadoff'](timeout=5)
        dev['rla_loadsw'].set_off()
        mes['dmm_vload'](timeout=5)

    @share.teststep
    def _step_load(self, dev, mes):
        """Test with load."""
        val = mes['arm_loadset']().reading1
        self._logger.debug('0x{:08X}'.format(int(val)))
        load_count = self.config['LoadCount']
        dev['dcl_out'].binary(1.0, load_count * LOAD_PER_OUTPUT, 5.0)
        for load in range(load_count):
            with tester.PathName('L{0}'.format(load + 1)):
                mes['arm_loads'][load](timeout=5)
        dev['dcl_bat'].output(BATT_CURRENT, True)
        self.measure(('dmm_vbatload', 'arm_battI', ), timeout=5)

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Test OCP."""
        mes['ramp_ocp'](timeout=5)
        dev['dcl_out'].output(0.0)
        dev['dcl_bat'].output(0.0)

    @share.teststep
    def _step_canbus(self, dev, mes):
        """Test the Can Bus."""
        self.measure(('dmm_canpwr', 'arm_can_bind', ), timeout=10)
        j35 = dev['j35']
        j35.can_testmode(True)
        # From here, Command-Response mode is broken by the CAN debug messages!
        j35['CAN'] = CAN_ECHO
        echo_reply = dev['j35_ser'].readline().decode(errors='ignore')
        echo_reply = echo_reply.replace('\r\n', '')
        rx_can = mes['rx_can']
        rx_can.sensor.store(echo_reply)
        rx_can.measure()


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('discharge', tester.Discharge, 'DIS'),
                ('dcs_vcom', tester.DCSource, 'DCS1'),
                ('dcs_vbat', tester.DCSource, 'DCS2'),
                ('dcs_vaux', tester.DCSource, 'DCS3'),
                ('dcs_solar', tester.DCSource, 'DCS4'),
                ('dcl_out', tester.DCLoad, 'DCL1'),
                ('dcl_bat', tester.DCLoad, 'DCL5'),
                ('rla_reset', tester.Relay, 'RLA1'),
                ('rla_boot', tester.Relay, 'RLA2'),
                ('rla_loadsw', tester.Relay, 'RLA3'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['program_arm'] = share.ProgramARM(
            ARM_PORT, os.path.join(folder, ARM_FILE), crpmode=False,
            boot_relay=self['rla_boot'], reset_relay=self['rla_reset'])
        # Serial connection to the console
        self['j35_ser'] = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self['j35_ser'].port = ARM_PORT
        # J35 Console driver
        self['j35'] = console.Console(self['j35_ser'], self.fifo)
        # Apply power to fixture circuits.
        self['dcs_vcom'].output(9.0, True)

    def reset(self):
        """Reset instruments."""
        self['j35'].close()
        # Switch off AC Source & discharge the unit
        self['acsource'].output(voltage=0.0, output=False)
        self['dcl_out'].output(2.0)
        time.sleep(1)
        self['discharge'].pulse()
        for dev in ('dcs_vbat', 'dcs_vaux', 'dcs_solar', 'dcl_out', 'dcl_bat'):
            self[dev].output(0.0, False)
        for rla in ('rla_reset', 'rla_boot', 'rla_loadsw'):
            self[rla].set_off()

    def close(self):
        """Finished testing."""
        self['dcs_vcom'].output(0, False)
        super().close()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensor instances."""
        dmm = self.devices['dmm']
        j35 = self.devices['j35']
        sensor = tester.sensor
        self['mir_can'] = sensor.Mirror(rdgtype=sensor.ReadingString)
        self['olock'] = sensor.Res(dmm, high=17, low=8, rng=10000, res=0.1)
        self['oacin'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.1)
        self['ovbus'] = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.1)
        self['o12Vpri'] = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.01)
        self['ovbat'] = sensor.Vdc(dmm, high=4, low=4, rng=100, res=0.001)
        self['ovload'] = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self['oaux'] = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.001)
        self['oair'] = sensor.Vdc(dmm, high=7, low=3, rng=100, res=0.001)
        self['o3V3U'] = sensor.Vdc(dmm, high=8, low=3, rng=10, res=0.001)
        self['o3V3'] = sensor.Vdc(dmm, high=9, low=3, rng=10, res=0.001)
        self['o15Vs'] = sensor.Vdc(dmm, high=10, low=3, rng=100, res=0.01)
        self['ofan'] = sensor.Vdc(dmm, high=12, low=5, rng=100, res=0.01)
        self['ocanpwr'] = sensor.Vdc(dmm, high=13, low=3, rng=100, res=0.01)
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('j35_initial', 'msgSnEntry'),
            caption=tester.translate('j35_initial', 'capSnEntry'))
        # Console sensors
        j35 = self.devices['j35']
        for name, cmdkey in (
                ('arm_auxv', 'AUX_V'),
                ('arm_auxi', 'AUX_I'),
                ('arm_vout_ov', 'VOUT_OV'),
                ('arm_acv', 'AC_V'),
                ('arm_acf', 'AC_F'),
                ('arm_sect', 'SEC_T'),
                ('arm_vout', 'BUS_V'),
                ('arm_fan', 'FAN'),
                ('arm_bati', 'BATT_I'),
                ('arm_canbind', 'CAN_BIND'),
                ('arm_loadset', 'LOAD_SET'),
            ):
            self[name] = console.Sensor(j35, cmdkey)
        self['arm_swver'] = console.Sensor(
            j35, 'SW_VER', rdgtype=sensor.ReadingString)
        # Generate load current sensors
        load_count = self.limits['LOAD_COUNT'].limit
        self['arm_loads'] = []
        for i in range(load_count):
            sen = console.Sensor(j35, 'LOAD_{0}'.format(i + 1))
            self['arm_loads'].append(sen)
        load_current = load_count * LOAD_PER_OUTPUT
        low, high = self.limits['OCP'].limit
        self['ocp'] = sensor.Ramp(
            stimulus=self.devices['dcl_bat'],
            sensor=self['ovbat'],
            detect_limit=(self.limits['InOCP'], ),
            start=low - load_current - 1,
            stop=high - load_current + 1,
            step=0.5, delay=0.2)
        self['ocp'].on_read = lambda value: value + load_current


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurement instances."""
        self.create_from_names((
            ('dmm_lock', 'FixtureLock', 'olock'),
            ('dmm_acin', 'ACin', 'oacin'),
            ('dmm_vbus', 'Vbus', 'ovbus'),
            ('dmm_12vpri', '12Vpri', 'o12Vpri'),
            ('dmm_vload', 'Vload', 'ovload'),
            ('dmm_vloadoff', 'VloadOff', 'ovload'),
            ('dmm_vbatin', 'VbatIn', 'ovbat'),
            ('dmm_vbatout', 'VbatOut', 'ovbat'),
            ('dmm_vbat', 'Vbat', 'ovbat'),
            ('dmm_vbatload', 'VbatLoad', 'ovbat'),
            ('dmm_vair', 'Vair', 'oair'),
            ('dmm_vaux', 'Vaux', 'oaux'),
            ('dmm_3v3u', '3V3U', 'o3V3U'),
            ('dmm_3v3', '3V3', 'o3V3'),
            ('dmm_15vs', '15Vs', 'o15Vs'),
            ('dmm_fanOn', 'FanOn', 'ofan'),
            ('dmm_fanOff', 'FanOff', 'ofan'),
            ('ramp_ocp', 'OCP', 'ocp'),
            ('ui_sernum', 'SerNum', 'sernum'),
            ('arm_swver', 'ARM-SwVer', 'arm_swver'),
            ('arm_auxv', 'ARM-AuxV', 'arm_auxv'),
            ('arm_auxi', 'ARM-AuxI', 'arm_auxi'),
            ('arm_vout_ov', 'Vout_OV', 'arm_vout_ov'),
            ('arm_acv', 'ARM-AcV', 'arm_acv'),
            ('arm_acf', 'ARM-AcF', 'arm_acf'),
            ('arm_secT', 'ARM-SecT', 'arm_sect'),
            ('arm_vout', 'ARM-Vout', 'arm_vout'),
            ('arm_fan', 'ARM-Fan', 'arm_fan'),
            ('arm_battI', 'ARM-BattI', 'arm_bati'),
            ('dmm_canpwr', 'CanPwr', 'ocanpwr'),
            ('rx_can', 'CAN_RX', 'mir_can'),
            ('arm_can_bind', 'CAN_BIND', 'arm_canbind'),
            ('arm_loadset', 'LOAD_SET', 'arm_loadset'),
            ))
        # Generate load current measurements
        loads = []
        for sen in self.sensors['arm_loads']:
            loads.append(tester.Measurement(self.limits['ARM-LoadI'], sen))
        self['arm_loads'] = loads
