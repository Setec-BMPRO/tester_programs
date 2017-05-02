#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 Initial Test Program."""

import os
import inspect
import time
import tester
from tester import (
    LimitLow, LimitHigh, LimitBetween, LimitDelta, LimitPercent,
    LimitInteger, LimitRegExp)
import share
from . import console

BIN_VERSION = '2.0.14782.1943'      # Software binary version

# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM16'}[os.name]
# ARM software image file
ARM_FILE = 'bc15_{}.bin'.format(BIN_VERSION)

LIMITS = (
    LimitDelta('ACin', 240.0, 5.0),
    LimitDelta('Vbus', 335.0, 10.0),
    LimitDelta('14Vpri', 14.0, 1.0),
    LimitBetween('12Vs', 11.7, 13.0),
    LimitDelta('5Vs', 5.0, 0.1),
    LimitBetween('3V3', 3.20, 3.35),
    LimitLow('FanOn', 0.5),
    LimitHigh('FanOff', 11.0),
    LimitDelta('15Vs', 15.5, 1.0),
    LimitPercent('Vout', 14.40, 5.0),
    LimitPercent('VoutCal', 14.40, 1.0),
    LimitLow('VoutOff', 2.0),
    LimitPercent('OCP', 15.0, 5.0),
    LimitLow('InOCP', 12.0),
    LimitLow('FixtureLock', 20),
    LimitHigh('FanShort', 100),
    # Data reported by the ARM
    LimitRegExp('ARM-SwVer', '^{}$'.format(BIN_VERSION.replace('.', r'\.'))),
    LimitPercent('ARM-Vout', 14.40, 5.0),
    LimitBetween('ARM-2amp', 0.5, 3.5),
    # Why 'Lucky'?
    #   The circuit specs are +/- 1.5A, and we hope to be lucky
    #   and get units within +/- 1.0A ...
    LimitDelta('ARM-2amp-Lucky', 2.0, 1.0),
    LimitDelta('ARM-14amp', 14.0, 2.0),
    LimitInteger('ARM-switch', 3),
    )


class Initial(share.TestSequence):

    """BC15 Initial Test Program."""

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(LIMITS, LogicalDevices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PartDetect', self._step_part_detect),
            tester.TestStep('Program', self._step_program, not self.fifo),
            tester.TestStep('Initialise', self._step_initialise_arm),
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('Output', self._step_output),
            tester.TestStep('Loaded', self._step_loaded),
            )

    @share.teststep
    def _step_part_detect(self, dev, mes):
        """Measure fixture lock and part detection microswitches."""
        self.measure(('dmm_lock', 'dmm_fanshort', ), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the ARM device."""
        dev['dcs_3v3'].output(9.0, True)
        mes['dmm_3V3'].measure(timeout=5)
        time.sleep(2)
        dev['programmer'].program()

    @share.teststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device."""
        dev['dcs_3v3'].output(9.0, True)
        bc15 = dev['bc15']
        bc15.open()
        dev['rla_reset'].pulse(0.1)
        time.sleep(0.5)
        bc15.action(None, delay=1.5, expected=10)  # Flush banner
        bc15['UNLOCK'] = True
        bc15['NVDEFAULT'] = True
        bc15['NVWRITE'] = True
        mes['arm_SwVer'].measure()
        bc15.close()
        dev['dcs_3v3'].output(0.0, False)

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power up the Unit."""
        dev['acsource'].output(voltage=240.0, output=True)
        self.measure(
            ('dmm_acin', 'dmm_vbus', 'dmm_12Vs', 'dmm_3V3',
             'dmm_15Vs', 'dmm_voutoff', ), timeout=5)
        bc15 = dev['bc15']
        bc15.open()
        bc15.action(None, delay=1.5, expected=10)  # Flush banner
        bc15.ps_mode()

    @share.teststep
    def _step_output(self, dev, mes):
        """Tests of the output."""
        bc15 = dev['bc15']
        dev['dcl'].output(2.0, True)
        time.sleep(0.5)
        bc15.stat()
        vout = self.measure(
            ('dmm_vout', 'arm_vout', 'arm_2amp', 'arm_2amp_lucky',
             'arm_switch', )).reading1
        bc15.cal_vout(vout)
        mes['dmm_vout_cal'].measure()

    @share.teststep
    def _step_loaded(self, dev, mes):
        """Tests of the output."""
        dev['dcl'].output(14.0, True)
        time.sleep(0.5)
        bc15 = dev['bc15']
        bc15.stat()
        self.measure(
            ('dmm_vout', 'arm_vout', 'arm_14amp', 'ramp_ocp', ))
        bc15.powersupply()


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
            ('dcs_3v3', tester.DCSource, 'DCS2'),
            ('dcs_out', tester.DCSource, 'DCS3'),
            ('dcl', tester.DCLoad, 'DCL1'),
            ('rla_reset', tester.Relay, 'RLA1'),
            ('rla_boot', tester.Relay, 'RLA2'),
            ('rla_outrev', tester.Relay, 'RLA3'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['programmer'] = share.ProgramARM(
            ARM_PORT, os.path.join(folder, ARM_FILE), crpmode=False,
            boot_relay=self['rla_boot'], reset_relay=self['rla_reset'])
        # Serial connection to the console
        self['bc15_ser'] = tester.SimSerial(
            simulation=self.fifo, baudrate=115200, timeout=2.0)
        # Set port separately, as we don't want it opened yet
        self['bc15_ser'].port = ARM_PORT
        # Console driver
        self['bc15'] = console.Console(self['bc15_ser'], verbose=False)
        # Apply power to fixture Comms circuit.
        self['dcs_vcom'].output(12.0, True)
        time.sleep(2)       # Allow OS to detect USB serial port

    def reset(self):
        """Reset instruments."""
        self['bc15'].close()
        self['acsource'].reset()
        self['dcl'].output(2.0)
        time.sleep(1)
        self['discharge'].pulse()
        self['dcl'].output(0.0, False)
        for dcs in ('dcs_3v3', 'dcs_out'):
            self[dcs].output(0.0, output=False)
        for rla in ('rla_reset', 'rla_boot', 'rla_outrev'):
            self[rla].set_off()

    def close(self):
        """Close logical devices."""
        self['dcs_vcom'].output(0, False)
        super().close()


class Sensors(share.Sensors):

    """Sensors."""


    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['olock'] = sensor.Res(dmm, high=12, low=5, rng=10000, res=1)
        self['ofanshort'] = sensor.Res(dmm, high=13, low=6, rng=10000, res=1)
        self['oACin'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self['oVbus'] = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self['o14Vpri'] = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.001)
        self['o12Vs'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self['o5Vs'] = sensor.Vdc(dmm, high=5, low=3, rng=10, res=0.001)
        self['o3V3'] = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self['ofan'] = sensor.Vdc(dmm, high=7, low=3, rng=100, res=0.001)
        self['o15Vs'] = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self['oVout'] = sensor.Vdc(dmm, high=9, low=4, rng=100, res=0.001)
        self['ocp'] = sensor.Ramp(
            stimulus=self.devices['dcl'],
            sensor=self['oVout'],
            detect_limit=(self.limits['InOCP'], ),
            start=14.0, stop=17.0, step=0.25, delay=0.1)
        # Console sensors
        bc15 = self.devices['bc15']
        self['arm_vout'] = console.Sensor(
            bc15, 'not-pulsing-volts', scale=0.001)
        self['arm_iout'] = console.Sensor(
            bc15, 'not-pulsing-current', scale=0.001)
        self['arm_switch'] = console.Sensor(bc15, 'SWITCH')
        self['arm_swver'] = console.Sensor(
            bc15, 'SW_VER', rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_lock', 'FixtureLock', 'olock', ''),
            ('dmm_fanshort', 'FanShort', 'ofanshort', ''),
            ('dmm_acin', 'ACin', 'oACin', ''),
            ('dmm_vbus', 'Vbus', 'oVbus', ''),
            ('dmm_14Vpri', '14Vpri', 'o14Vpri', ''),
            ('dmm_12Vs', '12Vs', 'o12Vs', ''),
            ('dmm_5Vs', '5Vs', 'o5Vs', ''),
            ('dmm_3V3', '3V3', 'o3V3', ''),
            ('dmm_fanon', 'FanOn', 'ofan', ''),
            ('dmm_fanoff', 'FanOff', 'ofan', ''),
            ('dmm_15Vs', '15Vs', 'o15Vs', ''),
            ('dmm_vout', 'Vout', 'oVout', ''),
            ('dmm_vout_cal', 'VoutCal', 'oVout', ''),
            ('dmm_voutoff', 'VoutOff', 'oVout', ''),
            ('ramp_ocp', 'OCP', 'ocp', ''),
            ('arm_SwVer', 'ARM-SwVer', 'arm_swver', ''),
            ('arm_vout', 'ARM-Vout', 'arm_vout', ''),
            ('arm_2amp', 'ARM-2amp', 'arm_iout', ''),
            ('arm_2amp_lucky', 'ARM-2amp-Lucky', 'arm_iout', ''),
            ('arm_switch', 'ARM-switch', 'arm_switch', ''),
            ('arm_14amp', 'ARM-14amp', 'arm_iout', ''),
            ))
