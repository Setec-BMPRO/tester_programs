#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""BC2 Configuration."""

import logging

import attr

import tester
import share


def get(parameter, uut):
    """Select a configuration based on the parameter.

    @param parameter Type of unit (100/300/PRO)
    @param uut setec.UUT instance
    @return configuration class

    """
    config = {
        '100': BatteryCheck100,
        '300': BatteryCheck300,
        'PRO': BatteryCheckPRO,
        }[parameter]
    config._configure(uut)    # Adjust for the revision
    return config


@attr.s
class _Values():

    """Adjustable configuration data values."""

    hw_version = attr.ib(validator=attr.validators.instance_of(tuple))
    sw_version = attr.ib(validator=attr.validators.instance_of(str))


class Config():

    """Base configuration for BatteryCheck."""

    # These values are set per Product revision
    sw_version = None
    hw_version = None
    _swver_limit = None
    #  Injected values
    vbatt = 15.0
    ibatt = 10.0
    # Test limits common to all units and test types
    _base_limits = (
        tester.LimitDelta('Vin', vbatt, 0.5,
            doc='Input voltage present'),
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
    _sw_1_0 = '1.0.16764.1813'
    _sw_1_7 = '1.7.17895.1845'
    _sw_2_0 = '2.0.0.2226'
    _rev_data = {
        None: _Values((7, 0, 'A'), _sw_2_0),
        '7': _Values((7, 0, 'A'), _sw_2_0),
        '6': _Values((6, 0, 'A'), _sw_2_0),
        '5': _Values((5, 0, 'A'), _sw_1_7),
        '4': _Values((4, 0, 'A'), _sw_1_0),
        '3': _Values((3, 0, 'A'), _sw_1_0),
        '2': _Values((2, 0, 'A'), _sw_1_0),
        '1': _Values((1, 0, 'A'), _sw_1_0),
        }

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut setec.UUT instance

        """
        try:
            cls._rev = uut.lot.item.revision
        except AttributeError:
            cls._rev = None
        logging.getLogger(__name__).debug('Revision detected as %s', cls._rev)
        values = cls._rev_data[cls._rev]
        cls.hw_version = values.hw_version
        cls.sw_version = values.sw_version
        cls._swver_limit = (
            tester.LimitRegExp('ARM-SwVer',
                '^{0}$'.format(cls.sw_version.replace('.', r'\.')),
                doc='Software version'),
            )


class BatteryCheck100(Config):

    """BatteryCheck100 configuration."""

    model = 0       # Model selector code

    @classmethod
    def limits_initial(cls):
        """Initial test limits.

        @return Tuple(limits)

        """
        return (
            cls._swver_limit +
            cls._base_limits_initial + (
                tester.LimitDelta('ARM-IbattZero', 0.0, 0.031,
                    doc='Zero battery current calibrated'),
                )
            )

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        return (
            cls._swver_limit +
            cls._base_limits_final + (
                tester.LimitPercent('ARM-ShuntRes', 800000, 5.0,
                    doc='Shunt resistance calibrated'),
                tester.LimitPercent('ARM-Ibatt', cls.ibatt, 1, delta=0.031,
                    doc='Battery current calibrated'),
                )
            )


class BatteryCheck300(Config):

    """BatteryCheck300 configuration."""

    model = 1       # Model selector code

    @classmethod
    def limits_initial(cls):
        """Initial test limits.

        @return Tuple(limits)

        """
        return (
            cls._swver_limit +
            cls._base_limits_initial + (
                tester.LimitDelta('ARM-IbattZero', 0.0, 0.3,
                    doc='Zero battery current calibrated'),
                )
            )

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        return (
            cls._swver_limit +
            cls._base_limits_final + (
                tester.LimitPercent('ARM-ShuntRes', 90000, 30.0,
                    doc='Shunt resistance calibrated'),
                tester.LimitPercent('ARM-Ibatt', cls.ibatt, 3, delta=0.3,
                    doc='Battery current calibrated'),
                )
            )


class BatteryCheckPRO(BatteryCheck300):

    """BatteryCheckPRO configuration."""

    model = 2       # Model selector code
