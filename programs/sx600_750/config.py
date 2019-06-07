#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-600/750 Configuration."""

import collections

import tester


class Config():

    """Base configuration for SX-600/750."""

    # General parameters used in testing the units
    #  Injected voltages
    _5vsb_ext = 6.3
    prictl_ext = 13.0
    #  Reading to reading difference for PFC voltage stability
    pfc_stable = 0.05
    # Final Test parameters
    #  Injected voltage at PS_ON via diode and 100R to prevent startup.
    disable_pwr = 5.5
    # Common Test limits common to both test types & units
    _base_limits_common = (
        # Outputs off
        tester.LimitLow('5Voff', 0.5),
        tester.LimitLow('12Voff', 0.5),
        tester.LimitLow('24Voff', 0.5),
        # No Load set points
        tester.LimitPercent('5Vnl', 5.10, 1.5),
        tester.LimitPercent('12Vnl', 12.25, 2.0),
        tester.LimitPercent('24Vnl', 24.13, 2.0),
        # Full Load
        tester.LimitPercent('5Vfl', 5.0, 4.5),
        tester.LimitPercent('12Vfl', 12.0, 6.5),
        tester.LimitPercent('24Vfl', 24.0, 9.5),
        # Load regulation (values in %)
        tester.LimitLow('Reg5V', 3.0),
        tester.LimitBetween('Reg12V', 0.2, 5.0),
        tester.LimitBetween('Reg24V', 0.2, 7.5),
        # Signals
        tester.LimitDelta('ACFAIL', 5.0, 0.5),
        tester.LimitLow('ACOK', 0.5),
        tester.LimitLow('PGOOD', 0.5),
        )
    # Initial Test limits common to both units
    _base_limits_initial = _base_limits_common + (
        tester.LimitDelta('8.5V Arduino', 8.5, 0.4),
        tester.LimitLow('FixtureLock', 200),
        tester.LimitRegExp('Reply', '^OK$'),
        tester.LimitInteger('Program', 0),
        tester.LimitDelta('3V3', 3.3, 0.1),
        tester.LimitDelta('ACin', 240, 10),
        tester.LimitLow('ARM-AcFreq', 999),
        tester.LimitLow('ARM-AcVolt', 999),
        tester.LimitLow('ARM-12V', 999),
        tester.LimitLow('ARM-24V', 999),
        tester.LimitBetween('PriCtl', 11.40, 17.0),
        tester.LimitDelta('PFCpre', 420, 20),
        tester.LimitDelta('PFCpost', 435, 1.0),
        tester.LimitDelta('5Vext', cls._5vsb_ext - 0.8, 1.0),
        tester.LimitDelta('5Vunsw', cls._5vsb_ext - 0.8 - 0.7, 1.0),
        )
    # Final Test limits common to both units
    _base_limits_final = _base_limits_common + (
        tester.LimitLow('IECoff', 0.5),
        tester.LimitDelta('IEC', 240, 5),
        tester.LimitDelta('InRes', 70000, 10000),
        )

    @staticmethod
    def get(parameter):
        """Select a configuration based on the parameter.

        @param parameter Type of unit (600/750)
        @return configuration class

        """
        return {'600': SX600, '750': SX750}[parameter]

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        return cls._base_limits_final


Rail = collections.namedtuple('Rail', 'full, peak, ocp')
Ratings = collections.namedtuple('Ratings', 'v12, v24')


class SX600(Config):

    """SX-600 configuration."""

    # Initial Test parameters
    #  Software version
# FIXME: We need software version
    _bin_version = 'a.b.ccc'
    #  Software image filenames
# FIXME: We need the software filename
    arm_bin = 'sx600_arm_{0}.bin'.format(_bin_version)
    # 12V & 24V output ratings (A)
    ratings = Ratings(
# FIXME: We need 12V OCP set point defined
        v12=Rail(full=30.0, peak=32.0, ocp='value'),
        v24=Rail(full=10.0, peak=12.0, ocp=None)
        )

    @classmethod
    def limits_initial(cls):
        """Initial test limits.

        @return Tuple(limits)

        """
        return super()._base_limits_initial + (
            tester.LimitBetween('12V_ocp', 4, 63), # Digital Pot setting
            tester.LimitHigh('12V_inOCP', 4.0),    # Detect OCP when TP405>4V
            tester.LimitDelta('12V_OCPchk', cls.ratings.v12.ocp, 0.4),
            tester.LimitDelta('OCP12pre', cls.ratings.v12.ocp, 2),
# FIXME: Check operation of 24V OCP detect
            tester.LimitHigh('24V_inOCP', 4.0),    # Detect OCP when TP404>4V
            tester.LimitDelta('24V_OCPchk', cls.ratings.v24.ocp, 0.2),
            tester.LimitDelta('OCP24pre', cls.ratings.v24.ocp, 1),
# FIXME: Add the rest of the SX-600 limits
            tester.LimitRegExp(
                'ARM-SwVer',
                '^{0}$'.format(cls._bin_version[:3].replace('.', r'\.'))),
            tester.LimitRegExp(
                'ARM-SwBld', '^{0}$'.format(cls._bin_version[4:])),
            )


class SX750(Config):

    """SX-750 configuration."""

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

    @classmethod
    def limits_initial(cls):
        """Initial test limits.

        @return Tuple(limits)

        """
        return super()._base_limits_initial + (
            tester.LimitBetween('12V_ocp', 4, 63), # Digital Pot setting
            tester.LimitHigh('12V_inOCP', 4.0),    # Detect OCP when TP405>4V
            tester.LimitDelta('12V_OCPchk', cls.ratings.v12.ocp, 0.4),
            tester.LimitDelta('OCP12pre', cls.ratings.v12.ocp, 2),
            tester.LimitBetween('24V_ocp', 4, 63), # Digital Pot setting
            tester.LimitHigh('24V_inOCP', 4.0),    # Detect OCP when TP404>4V
            tester.LimitDelta('24V_OCPchk', cls.ratings.v24.ocp, 0.2),
            tester.LimitDelta('OCP24pre', cls.ratings.v24.ocp, 1),
            tester.LimitRegExp(
                'ARM-SwVer',
                '^{0}$'.format(cls._bin_version[:3].replace('.', r'\.'))),
            tester.LimitRegExp(
                'ARM-SwBld', '^{0}$'.format(cls._bin_version[4:])),
            tester.LimitLow('PartCheck', 1.0),          # Photo sensor on D404
            tester.LimitBetween('Snubber', 1000, 3000), # Snubbing resistors
            )
