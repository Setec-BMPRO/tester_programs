#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2013 SETEC Pty Ltd
"""SX-750 Configuration."""

import attr

import tester


@attr.s
class Rail():
    """Rail data values."""
    full = attr.ib(validator=attr.validators.instance_of(float))
    peak = attr.ib(validator=attr.validators.instance_of(float))
    ocp = attr.ib(validator=attr.validators.instance_of(float))


@attr.s
class Ratings():
    """Ratings data values."""
    v12 = attr.ib(validator=attr.validators.instance_of(Rail))
    v24 = attr.ib(validator=attr.validators.instance_of(Rail))


class Config():

    """Configuration."""

    # General parameters used in testing the units
    #  Injected voltages
    _5vsb_ext = 6.3
    prictl_ext = 13.0
    #  Post-adjustment PFC voltage
    pfc_target = 435.0
    #  Reading to reading difference for PFC voltage stability
    pfc_stable = 0.05
    # Final Test parameters
    #  Injected voltage at PS_ON via diode and 100R to prevent startup.
    disable_pwr = 5.5
    #  Injected voltage for fan and bracket detect circuits
    part_detect = 12.0
    fixture_fan = 12.0
    # Initial Test parameters
    #  Software version
    _bin_version = '3.1.2118'
    #  Software image filenames
    arm_bin = 'sx750_arm_{0}.bin'.format(_bin_version)
    #  Fan ON threshold temperature (C)
    fan_threshold = 55.0
    # 12V & 24V output ratings (A)
    ratings = Ratings(
        v12=Rail(full=32.0, peak=36.0, ocp=36.6),
        v24=Rail(full=15.0, peak=18.0, ocp=18.3)
        )
    # Common Test limits common to both test types & units
    _limits_common = (
        # Outputs off
        tester.LimitLow('5Voff', 0.5),
        tester.LimitLow('12Voff', 0.5),
        tester.LimitLow('24Voff', 0.5),
        # Full Load
        tester.LimitPercent('5Vfl', 5.0, 4.5),
        tester.LimitPercent('12Vfl', 12.0, 6.5),
        tester.LimitPercent('24Vfl', 24.0, 9.0),
        # Signals
        tester.LimitDelta('ACFAIL', 5.0, 0.5),
        tester.LimitLow('ACOK', 0.5),
        tester.LimitLow('PGOOD', 0.5),
        # Voltages
        tester.LimitPercent('5Vnl', 5.10, 1.5),
        tester.LimitPercent('12Vnl', 12.25, 2.0),
        tester.LimitPercent('24Vnl', 24.13, 2.0),
        # Load regulation (values in %)
        tester.LimitBetween('Reg12V', 0.2, 5.0),
        tester.LimitBetween('Reg24V', 0.2, 7.5),
        )
    # Initial Test limits common to both units
    limits_initial = _limits_common + (
        # Load regulation (values in %)
        tester.LimitLow('Reg5V', 3.0),
        tester.LimitDelta('8.5V Arduino', 8.5, 0.4),
        tester.LimitLow('FixtureLock', 200),
        tester.LimitLow('PartCheck', 1.0),          # Photo sensor on D404
        tester.LimitBetween('Snubber', 1000, 3000), # Snubbing resistors
        tester.LimitRegExp('Reply', '^OK$'),
        tester.LimitInteger('Program', 0),
        tester.LimitDelta('3V3', 3.3, 0.1),
        tester.LimitDelta('ACin', 240, 10),
        tester.LimitLow('ARM-AcFreq', 999),
        tester.LimitLow('ARM-AcVolt', 999),
        tester.LimitLow('ARM-12V', 999),
        tester.LimitLow('ARM-24V', 999),
        tester.LimitDelta('5Vext', _5vsb_ext - 0.8, 1.0),
        tester.LimitDelta('5Vunsw', _5vsb_ext - 0.8 - 0.7, 1.0),
        tester.LimitHigh('12V_inOCP', 4.0),    # Detect OCP when TP405>4V
        tester.LimitHigh('24V_inOCP', 4.0),    # Detect OCP when TP404>4V
        tester.LimitBetween('12V_ocp', 4, 63), # Digital Pot setting
        tester.LimitBetween('24V_ocp', 4, 63), # Digital Pot setting
        tester.LimitBetween('PriCtl', 11.40, 17.0),
        tester.LimitDelta('PFCpre', 420, 20),
        tester.LimitDelta('PFCpost', pfc_target, 1.0),
        tester.LimitDelta('12V_OCPchk', ratings.v12.ocp, 0.4),
        tester.LimitDelta('24V_OCPchk', ratings.v24.ocp, 0.2),
        tester.LimitRegExp(
            'ARM-SwVer',
            '^{0}$'.format(r'\.'.join(_bin_version.split('.')[:2]))),
        tester.LimitRegExp(
            'ARM-SwBld',
            '^{0}$'.format(_bin_version.split('.')[2])),
        )
    # Final Test limits common to both units
    limits_final = _limits_common + (
        tester.LimitLow('IECoff', 0.5),
        tester.LimitDelta('IEC', 240, 5),
        tester.LimitDelta('InRes', 70000, 10000),
        tester.LimitHigh('FanOff', 3.0),
        tester.LimitLow('FanOn', 2.0),
        tester.LimitLow('BracketDetect', 1.0),
        )