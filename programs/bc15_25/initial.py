#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15/25 Initial Test Program."""

import os
import inspect
import time
import math
import serial
import tester
from tester import (
    LimitLow, LimitHigh, LimitBetween, LimitDelta, LimitPercent,
    LimitInteger, LimitRegExp)
import share
from . import console


class Initial(share.TestSequence):

    """BC15/25 Initial Test Program."""

    bin_version_15 = '2.0.16258.2002'
    bin_version_25 = '1.0.16489.137'
    # Setpoints
    vac = 240.0
    vout_set = 14.40
    ocp_nominal_15 = 15.0
    ocp_nominal_25 = 25.0
    ocp_load_factor = 0.8
    # Common limits
    _common = (
        LimitLow('FixtureLock', 20),
        LimitHigh('FanShort', 100),
        LimitDelta('ACin', vac, 5.0),
        LimitDelta('Vbus', math.sqrt(2) * vac, 10.0),
        LimitDelta('14Vpri', 14.0, 1.0),
        LimitBetween('12Vs', 11.7, 13.0),
        LimitBetween('3V3', 3.20, 3.35),
        LimitLow('FanOn', 0.5),
        LimitHigh('FanOff', 11.0),
        LimitDelta('15Vs', 15.5, 1.0),
        LimitPercent('Vout', vout_set, 4.0),
        LimitPercent('VoutCal', vout_set, 1.0),
        LimitLow('VoutOff', 2.0),
        LimitLow('InOCP', 13.5),
        LimitPercent('ARM-Vout', vout_set, 5.0),
        LimitPercent('ARM-2amp', 2.0, percent=1.7, delta=1.0),
        LimitInteger('ARM-switch', 3),
        )
    # Variant specific configuration data. Indexed by test program parameter.
    limitdata = {
        '15': {
            'ARMfile': 'bc15_{0}.bin'.format(bin_version_15),
            'ARMport': share.fixture.port('028467', 'ARM'),
            'BinVersion': bin_version_15,
            'OCP_Nominal': ocp_nominal_15,
            'Limits': _common + (
                LimitLow('5Vs', 99.0),  # No test point
                LimitRegExp('ARM-SwVer', '^{0}$'.format(
                    bin_version_15.replace('.', r'\.'))),
                LimitPercent('OCP_pre', ocp_nominal_15, 15),
                LimitPercent('OCP_post', ocp_nominal_15, 2.0),
                LimitPercent(
                    'ARM-HIamp',
                    ocp_nominal_15 * ocp_load_factor,
                    percent=1.7, delta=1.0),
                ),
            },
        '25': {
            'ARMfile': 'bc25_{0}.bin'.format(bin_version_25),
            'ARMport': share.fixture.port('031032', 'ARM'),
            'BinVersion': bin_version_25,
            'OCP_Nominal': ocp_nominal_25,
            'Limits': _common + (
                LimitDelta('5Vs', 4.95, 0.15),
                LimitRegExp('ARM-SwVer', '^{0}$'.format(
                    bin_version_25.replace('.', r'\.'))),
                LimitPercent('OCP_pre', ocp_nominal_25, 15),
                LimitPercent('OCP_post', ocp_nominal_25, 2.0),
                LimitPercent(
                    'ARM-HIamp',
                    ocp_nominal_25 * ocp_load_factor,
                    percent=1.7, delta=1.0),
                ),
            },
        }

    def open(self):
        """Create the test program as a linear sequence."""
        self.config = self.limitdata[self.parameter]
        Devices.arm_file = self.config['ARMfile']
        Devices.arm_port = self.config['ARMport']
        Sensors.ocp_nominal = self.config['OCP_Nominal']
        super().open(
            self.config['Limits'], Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('PartDetect', self._step_part_detect),
            tester.TestStep('Program', self._step_program),
            tester.TestStep('Initialise', self._step_initialise_arm),
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('Output', self._step_output),
            tester.TestStep('OCP', self._step_ocp),
            )

    @share.teststep
    def _step_part_detect(self, dev, mes):
        """Measure fixture lock and part detection microswitches."""
        self.measure(('dmm_lock', 'dmm_fanshort', ), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the ARM device."""
        dev['dcs_3v3'].output(9.0, True)
        mes['dmm_3V3'](timeout=5)
        time.sleep(2)
        dev['programmer'].program()

    @share.teststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device."""
        arm = dev['arm']
        arm.open()
        arm.initialise(dev['rla_reset'])
        mes['arm_SwVer']()
        dev['dcs_3v3'].output(0.0, False)

    @share.teststep
    def _step_powerup(self, dev, mes):
        """Power up the Unit."""
        dev['acsource'].output(voltage=self.vac, output=True)
        self.measure(
            ('dmm_acin', 'dmm_vbus', 'dmm_12Vs', 'dmm_5Vs', 'dmm_3V3',
             'dmm_15Vs', 'dmm_voutoff', ),
            timeout=5)
        arm = dev['arm']
        arm.banner()
        arm.ps_mode(self.vout_set, self.config['OCP_Nominal'])

    @share.teststep
    def _step_output(self, dev, mes):
        """Tests of the output."""
        arm = dev['arm']
        dev['dcl'].output(2.0, True, delay=0.5)
        arm.stat()
        vout = self.measure(
            ('dmm_vout', 'arm_vout', 'arm_2amp', 'arm_switch', )).reading1
        arm.cal_vout(vout)
        mes['dmm_vout_cal']()

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Output current reading and OCP calibration."""
        arm = dev['arm']
        dcload = dev['dcl']
        ocp_nominal = self.config['OCP_Nominal']
        current = ocp_nominal * 0.8
        # Measure actual OCP setting
        dcload.output(current, True, delay=0.5)
        ocp_actual = mes['ramp_ocp_pre']().reading1
        ocp_factor = ocp_nominal / ocp_actual
        # Shutdown and startup
        dev['acsource'].output(voltage=0, delay=1)
        dev['discharge'].pulse(delay=5)
        dcload.output(0)
        dev['acsource'].output(voltage=self.vac)
        arm.banner()
        arm.ps_mode(self.vout_set, ocp_nominal)
        # Set load for output current reading calibration
        dcload.linear(2.0, current, step=5.0)
        arm.cal_iout(current, ocp_factor)
        arm.stat()
        self.measure(('dmm_vout', 'arm_vout', 'arm_Hiamp', 'ramp_ocp_post', ))
        arm.powersupply()


class Devices(share.Devices):

    """Devices."""

    arm_file = None     # Firmware image filename
    arm_port = None     # Serial port for ARM programming & console

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
            ('dmm', tester.DMM, 'DMM'),
            ('acsource', tester.ACSource, 'ACS'),
            ('discharge', tester.Discharge, 'DIS'),
            ('dcs_3v3', tester.DCSource, 'DCS2'),
            ('dcl', tester.DCLoad, 'DCL1'),
            ('rla_reset', tester.Relay, 'RLA1'),
            ('rla_boot', tester.Relay, 'RLA2'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['programmer'] = share.programmer.ARM(
            self.arm_port,
            os.path.join(folder, self.arm_file),
            crpmode=False,
            boot_relay=self['rla_boot'],
            reset_relay=self['rla_reset'])
        # Serial connection to the console
        arm_ser = serial.Serial(baudrate=115200, timeout=2.0)
        # Set port separately, as we don't want it opened yet
        arm_ser.port = self.arm_port
        # Console driver
        self['arm'] = console.Console(arm_ser)
        self['arm'].parameter = self.parameter

    def reset(self):
        """Reset instruments."""
        self['arm'].close()
        self['acsource'].reset()
        self['dcl'].output(2.0, delay=1)
        self['discharge'].pulse()
        self['dcs_3v3'].output(0.0, output=False)
        self['dcl'].output(0.0, False)
        for rla in ('rla_reset', 'rla_boot', ):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    ocp_nominal = None      # Nominal OCP point of unit

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['lock'] = sensor.Res(dmm, high=12, low=5, rng=10000, res=1)
        self['fanshort'] = sensor.Res(dmm, high=13, low=6, rng=10000, res=1)
        self['ACin'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self['Vbus'] = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self['14Vpri'] = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.001)
        self['12Vs'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self['5Vs'] = sensor.Vdc(dmm, high=5, low=3, rng=10, res=0.001)
        self['3V3'] = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self['fan'] = sensor.Vdc(dmm, high=7, low=3, rng=100, res=0.001)
        self['15Vs'] = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self['Vout'] = sensor.Vdc(dmm, high=9, low=4, rng=100, res=0.001)
        self['ocp'] = sensor.Ramp(
            stimulus=self.devices['dcl'],
            sensor=self['Vout'],
            detect_limit=(self.limits['InOCP'], ),
            start=self.ocp_nominal * 0.85,  # ±15% ramping range
            stop=self.ocp_nominal * 1.15,
            step=0.1,
            delay=0.2)
        # Console sensors
        arm = self.devices['arm']
        self['arm_vout'] = share.console.Sensor(
            arm, 'not-pulsing-volts', scale=0.001)
        self['arm_iout'] = share.console.Sensor(
            arm, 'not-pulsing-current', scale=0.001)
        self['arm_switch'] = share.console.Sensor(arm, 'SWITCH')
        self['arm_swver'] = share.console.Sensor(
            arm, 'SW_VER', rdgtype=sensor.ReadingString)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_lock', 'FixtureLock', 'lock', ''),
            ('dmm_fanshort', 'FanShort', 'fanshort', ''),
            ('dmm_acin', 'ACin', 'ACin', ''),
            ('dmm_vbus', 'Vbus', 'Vbus', ''),
            ('dmm_14Vpri', '14Vpri', '14Vpri', ''),
            ('dmm_12Vs', '12Vs', '12Vs', ''),
            ('dmm_5Vs', '5Vs', '5Vs', ''),
            ('dmm_3V3', '3V3', '3V3', ''),
            ('dmm_fanon', 'FanOn', 'fan', ''),
            ('dmm_fanoff', 'FanOff', 'fan', ''),
            ('dmm_15Vs', '15Vs', '15Vs', ''),
            ('dmm_vout', 'Vout', 'Vout', ''),
            ('dmm_vout_cal', 'VoutCal', 'Vout', ''),
            ('dmm_voutoff', 'VoutOff', 'Vout', ''),
            ('ramp_ocp_pre', 'OCP_pre', 'ocp', ''),
            ('ramp_ocp_post', 'OCP_post', 'ocp', ''),
            ('arm_SwVer', 'ARM-SwVer', 'arm_swver', ''),
            ('arm_vout', 'ARM-Vout', 'arm_vout', ''),
            ('arm_2amp', 'ARM-2amp', 'arm_iout', ''),
            ('arm_switch', 'ARM-switch', 'arm_switch', ''),
            ('arm_Hiamp', 'ARM-HIamp', 'arm_iout', ''),
            ))
