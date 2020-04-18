#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""BC2 Configuration."""

import tester
import share


class Config():

    """Base configuration for BatteryCheck."""

    #  Software version
    sw_version = '2.0.0.2226'
    # Hardware version (Major [1-255], Minor [1-255], Mod [character])
    hw_version = (6, 0, 'A')
    #  Injected values
    vbatt = 15.0
    ibatt = 10.0
    # Test limits common to all units and test types
    _base_limits = (
        tester.LimitDelta('Vin', vbatt, 0.5,
            doc='Input voltage present'),
        tester.LimitRegExp('ARM-SwVer',
            '^{0}$'.format(sw_version.replace('.', r'\.')),
            doc='Software version'),
        )
    # Initial Test limits common to all units
    _base_limits_initial = _base_limits + (
        tester.LimitPercent('3V3', 3.3, 3.0,
            doc='3V3 present'),
        tester.LimitRegExp('BtMac', share.bluetooth.MAC.line_regex,
            doc='Valid MAC address '),
        tester.LimitBoolean('DetectBT', True,
            doc='MAC address detected'),
        tester.LimitRegExp('ARM-CalOk', 'cal success:',
            doc='Calibration success'),
        tester.LimitBetween('ARM-I_ADCOffset', -3, 3,
            doc='Current ADC offset calibrated'),
        tester.LimitBetween('ARM-VbattLSB', 2391, 2489,
            doc='LSB voltage calibrated'),
        tester.LimitPercent('ARM-Vbatt', vbatt, 0.5, delta=0.02,
            doc='Battery voltage calibrated'),
        )
    # Final Test limits common to all units
    _base_limits_final = _base_limits + (
        tester.LimitRegExp('ARM-QueryLast', 'cal success:',
            doc='Calibration success'),
        )

    @staticmethod
    def get(parameter):
        """Select a configuration based on the parameter.

        @param parameter Type of unit (100/300/PRO)
        @return configuration class

        """
        return {
            '100': BatteryCheck100,
            '300': BatteryCheck300,
            'PRO': BatteryCheckPRO,
            }[parameter]


class BatteryCheck100(Config):

    """BatteryCheck100 configuration."""

    model = 0       # Model selector code

    @classmethod
    def limits_initial(cls):
        """Initial test limits.

        @return Tuple(limits)

        """
        return cls._base_limits_initial + (
            tester.LimitDelta('ARM-IbattZero', 0.0, 0.031,
                doc='Zero battery current calibrated'),
                )

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        return cls._base_limits_final + (
            tester.LimitPercent('ARM-ShuntRes', 800000, 5.0,
                doc='Shunt resistance calibrated'),
            tester.LimitPercent('ARM-Ibatt', cls.ibatt, 1, delta=0.031,
                doc='Battery current calibrated'),
            )


class BatteryCheck300(Config):

    """BatteryCheck300 configuration."""

    model = 1       # Model selector code

    @classmethod
    def limits_initial(cls):
        """Initial test limits.

        @return Tuple(limits)

        """
        return cls._base_limits_initial + (
            tester.LimitDelta('ARM-IbattZero', 0.0, 0.3,
                doc='Zero battery current calibrated'),
                )

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        return cls._base_limits_final + (
            tester.LimitPercent('ARM-ShuntRes', 90000, 30.0,
                doc='Shunt resistance calibrated'),
            tester.LimitPercent('ARM-Ibatt', cls.ibatt, 3, delta=0.3,
                doc='Battery current calibrated'),
            )


class BatteryCheckPRO(BatteryCheck300):

    """BatteryCheckPRO configuration."""

    model = 2       # Model selector code
