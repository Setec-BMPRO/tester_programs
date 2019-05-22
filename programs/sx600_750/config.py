#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-600/750 Configuration."""

import tester


class SXxxx():

    """Base configuration for SX-600/750."""

    # General parameters used in testing the units

    # Initial Test limits common to both versions
    _base_limits_initial = (
        )
    # Final Test limits common to both versions
    _base_limits_final = (
        )

    @staticmethod
    def configure(parameter):
        """Select a configuration based on the parameter.

        @param parameter Type of unit (600/750)
        @return configuration class

        """
        return {
            '600': SX600,
            '750': SX750,
            }[parameter]


class SX600(SXxxx):

    """SX-600 configuration."""

    @classmethod
    def limits_initial(cls):
        """Initial test limits.

        @return Tuple(limits)

        """
        return super()._base_limits_initial + (
            )

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        return super()._base_limits_final + (
            )


class SX750(SXxxx):

    """SX-750 configuration."""

    # Initial Test parameters
    #  Software version
    _bin_version = '3.1.2118'
    #  Software image filenames
    arm_bin = 'sx750_arm_{0}.bin'.format(_bin_version)
    #  Reading to reading difference for PFC voltage stability
    pfc_stable = 0.05
    #  Fan ON threshold temperature (C)
    fan_threshold = 55.0
    #  Injected voltages
    _5vsb_ext = 6.3
    prictl_ext = 13.0
    # Final Test parameters
    #  Injected voltage at PS_ON via diode and 100R to prevent startup.
    disable_pwr = 5.5

    @classmethod
    def limits_initial(cls):
        """Initial test limits.

        @return Tuple(limits)

        """
        return super()._base_limits_initial + (
            tester.LimitDelta('8.5V Arduino', 8.5, 0.4),
            tester.LimitLow('5Voff', 0.5),
            tester.LimitDelta('5Vext', cls._5vsb_ext - 0.8, 1.0),
            tester.LimitDelta('5Vunsw', cls._5vsb_ext - 0.8 - 0.7, 1.0),
            tester.LimitPercent('5Vsb_set', 5.10, 1.5),
            tester.LimitPercent('5Vsb', 5.10, 5.5),
            tester.LimitLow('5Vsb_reg', 3.0),      # Load Reg < 3.0%
            tester.LimitLow('12Voff', 0.5),
            tester.LimitPercent('12V_set', 12.25, 2.0),
            tester.LimitPercent('12V', 12.25, 8.0),
            tester.LimitLow('12V_reg', 3.0),       # Load Reg < 3.0%
            tester.LimitBetween('12V_ocp', 4, 63), # Digital Pot setting
            tester.LimitHigh('12V_inOCP', 4.0),    # Detect OCP when TP405>4V
            tester.LimitBetween('12V_OCPchk', 36.2, 37.0),
            tester.LimitLow('24Voff', 0.5),
            tester.LimitPercent('24V_set', 24.13, 2.0),
            tester.LimitPercent('24V', 24.13, 10.5),
            tester.LimitLow('24V_reg', 7.5),       # Load Reg < 7.5%
            tester.LimitBetween('24V_ocp', 4, 63), # Digital Pot setting
            tester.LimitHigh('24V_inOCP', 4.0),    # Detect OCP when TP404>4V
            tester.LimitBetween('24V_OCPchk', 18.1, 18.5),
            tester.LimitBetween('PriCtl', 11.40, 17.0),
            tester.LimitLow('PGOOD', 0.5),
            tester.LimitDelta('ACFAIL', 5.0, 0.5),
            tester.LimitLow('ACOK', 0.5),
            tester.LimitDelta('3V3', 3.3, 0.1),
            tester.LimitDelta('ACin', 240, 10),
            tester.LimitDelta('PFCpre', 420, 20),
            tester.LimitDelta('PFCpost', 435, 1.0),
            tester.LimitDelta('OCP12pre', 36, 2),
            tester.LimitBetween('OCP12post', 35.7, 36.5),
            tester.LimitLow('OCP12step', 0.116),
            tester.LimitDelta('OCP24pre', 18, 1),
            tester.LimitDelta('OCP24post', 18.2, 0.1),
            tester.LimitLow('OCP24step', 0.058),
            tester.LimitLow('ARM-AcFreq', 999),
            tester.LimitLow('ARM-AcVolt', 999),
            tester.LimitLow('ARM-12V', 999),
            tester.LimitLow('ARM-24V', 999),
            tester.LimitRegExp(
                'ARM-SwVer',
                '^{0}$'.format(cls._bin_version[:3].replace('.', r'\.'))),
            tester.LimitRegExp(
                'ARM-SwBld', '^{0}$'.format(cls._bin_version[4:])),
            tester.LimitLow('FixtureLock', 200),
            tester.LimitLow('PartCheck', 1.0),          # Photo sensor on D404
            tester.LimitBetween('Snubber', 1000, 3000), # Snubbing resistors
            tester.LimitRegExp('Reply', '^OK$'),
            tester.LimitInteger('Program', 0)
            )

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        return super()._base_limits_final + (
            tester.LimitDelta('InRes', 70000, 10000),
            tester.LimitLow('IECoff', 0.5),
            tester.LimitDelta('IEC', 240, 5),
            tester.LimitBetween('5V', 5.034, 5.177),
            tester.LimitLow('12Voff', 0.5),
            tester.LimitBetween('12Von', 12.005, 12.495),
            tester.LimitBetween('24Von', 23.647, 24.613),
            tester.LimitBetween('5Vfl', 4.820, 5.380),
            tester.LimitBetween('12Vfl', 11.270, 13.230),
            tester.LimitBetween('24Vfl', 21.596, 26.663),
            tester.LimitLow('PwrGood', 0.5),
            tester.LimitDelta('AcFail', 5.0, 0.5),
            tester.LimitBetween('Reg12V', 0.2, 5.0),
            tester.LimitBetween('Reg24V', 0.2, 5.0),
            )
