#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2013 - 2020 SETEC Pty Ltd.
"""BC15/BC25 Configuration."""

import logging
import math

import attr
import tester

import share


@attr.s
class _Values():

    """Adjustable configuration data values."""

    arm_file = attr.ib(validator=attr.validators.instance_of(str))
    arm_port = attr.ib(validator=attr.validators.instance_of(str))
    sw_version = attr.ib(validator=attr.validators.instance_of(str))
    cal_linecount = attr.ib(validator=attr.validators.instance_of(int))


class BCx5():

    """Base configuration for BC15/25."""

    # These values get set per Product type & revision
    arm_file = None         # Software image filename
    arm_port = None         # ARM console serial port
    sw_version = None       # Software version number
    cal_linecount = None    # Number of lines to a CAL? command
    # General parameters used in testing the units
    #  AC voltage powering the unit
    vac = 240.0
    #  Output set point
    vout_set = 14.40
    # Initial Test limits common to both versions
    _base_limits_initial = (
        tester.LimitLow('FixtureLock', 20),
        tester.LimitHigh('FanShort', 100),
        tester.LimitDelta('ACin', vac, 5.0),
        tester.LimitDelta('Vbus', math.sqrt(2) * vac, 10.0),
        tester.LimitDelta('14Vpri', 14.0, 1.0),
        tester.LimitBetween('12Vs', 11.7, 13.0),
        tester.LimitBetween('3V3', 3.20, 3.35),
        tester.LimitLow('FanOn', 0.5),
        tester.LimitHigh('FanOff', 11.0),
        tester.LimitDelta('15Vs', 15.5, 1.0),
        tester.LimitPercent('Vout', vout_set, 4.0),
        tester.LimitPercent('VoutCal', vout_set, 1.0),
        tester.LimitLow('VoutOff', 2.0),
        tester.LimitLow('InOCP', 13.5),
        tester.LimitPercent('ARM-Vout', vout_set, 5.0),
        tester.LimitPercent('ARM-2amp', 2.0, percent=1.7, delta=1.0),
        tester.LimitInteger('ARM-switch', 3),
        )
    # Final Test limits common to both versions
    _base_limits_final = (
        tester.LimitDelta('VoutNL', 13.6, 0.3),
        tester.LimitDelta('Vout', 13.6, 0.7),
        tester.LimitLow('InOCP', 12.5),
        )
    # Internal data storage
    _lot_rev = None         # Lot Number to Revision data
    _rev_data = None        # Revision data dictionary

    @staticmethod
    def select(parameter, uut):
        """Select a configuration based on the parameter and lot.

        @param parameter Type of unit (15/25)
        @param uut UUT to get Lot Number from
        @return configuration class

        """
        config = {
            '15': BC15,
            '25': BC25,
            }[parameter]
        config._configure(uut)    # Adjust for the Lot Number
        return config

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut storage.UUT instance

        """
        rev = None
        if uut:
            lot = uut.lot
            try:
                rev = cls._lot_rev.find(lot)
            except share.lots.LotError:
                pass
        logging.getLogger(__name__).debug('Revision detected as %s', rev)
        values = cls._rev_data[rev]
        cls.arm_file = values.arm_file
        cls.arm_port = values.arm_port
        cls.sw_version = values.sw_version
        cls.cal_linecount = values.cal_linecount


class BC15(BCx5):

    """BC15 configuration."""

    sw_version_a = '2.0.16258.2002'
    sw_version_b = '2.0.18498.2003'
    arm_file_pattern = 'bc15_{0}.bin'
    arm_port = share.config.Fixture.port('028467', 'ARM')
    _lot_rev = share.lots.Revision((
        (share.lots.Range('A100101', 'A190101'), 0),    # Rev 1 - 5
        # Rev 6...
        ))
    _rev_data = {
        None: _Values(
            arm_file=arm_file_pattern.format(sw_version_b),
            arm_port=arm_port,
            sw_version=sw_version_b,
            cal_linecount=43,
            ),
        0: _Values(
            arm_file=arm_file_pattern.format(sw_version_a),
            arm_port=arm_port,
            sw_version=sw_version_a,
            cal_linecount=39,
            ),
        }

    @classmethod
    def limits_initial(cls):
        """BC15 initial test limits.

        @return Tuple(Nominal OCP, Tuple(limits))

        """
        ocp_nominal = 15.0
        ocp_load_factor = 0.8
        return (
            ocp_nominal,
            super()._base_limits_initial + (
                tester.LimitLow('5Vs', 99.0),  # No test point
                tester.LimitRegExp('ARM-SwVer', '^{0}$'.format(
                    cls.sw_version.replace('.', r'\.'))),
                tester.LimitPercent('OCP_pre', ocp_nominal, 15),
                tester.LimitPercent('OCP_post', ocp_nominal, 2.0),
                tester.LimitPercent(
                    'ARM-HIamp',
                    ocp_nominal * ocp_load_factor,
                    percent=1.7, delta=1.0),
                ),
            )

    @classmethod
    def limits_final(cls):
        """BC15 final test limits.

        @return Tuple(Nominal OCP, Tuple(limits))

        """
        ocp_nominal = 11.0
        return (
            ocp_nominal,
            super()._base_limits_final + (
                tester.LimitPercent('OCP', ocp_nominal, (4.0, 7.0)),
                ),
            )


class BC25(BCx5):

    """BC25 configuration."""

    sw_version_a = '1.0.16489.137'
    sw_version_b = '2.0.18498.2003'
    arm_file_pattern = 'bc25_{0}.bin'
    arm_port = share.config.Fixture.port('031032', 'ARM')
    _lot_rev = share.lots.Revision((
        (share.lots.Range('A100101', 'A190101'), 0),    # Rev 1 - 3
        # Rev 4...
        ))
    _rev_data = {
        None: _Values(
            arm_file=arm_file_pattern.format(sw_version_b),
            arm_port=arm_port,
            sw_version=sw_version_b,
            cal_linecount=43,
            ),
        0: _Values(
            arm_file=arm_file_pattern.format(sw_version_a),
            arm_port=arm_port,
            sw_version=sw_version_a,
            cal_linecount=43,   # Yes - this is different to the old BC15
            ),
        }

    @classmethod
    def limits_initial(cls):
        """BC25 initial test limits.

        @return Tuple(Nominal OCP, Tuple(limits))

        """
        ocp_nominal = 25.0
        ocp_load_factor = 0.8
        return (
            ocp_nominal,
            super()._base_limits_initial + (
                tester.LimitDelta('5Vs', 4.95, 0.15),
                tester.LimitRegExp('ARM-SwVer', '^{0}$'.format(
                    cls.sw_version.replace('.', r'\.'))),
                tester.LimitPercent('OCP_pre', ocp_nominal, 15),
                tester.LimitPercent('OCP_post', ocp_nominal, 2.0),
                tester.LimitPercent(
                    'ARM-HIamp',
                    ocp_nominal * ocp_load_factor,
                    percent=1.7, delta=1.0),
                ),
            )

    @classmethod
    def limits_final(cls):
        """BC25 final test limits.

        @return Tuple(Nominal OCP, Tuple(limits))

        """
        ocp_nominal = 20.0
        return (
            ocp_nominal,
            super()._base_limits_final + (
                tester.LimitPercent('OCP', ocp_nominal, (4.0, 7.0)),
                ),
            )
