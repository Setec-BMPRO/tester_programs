#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2015 SETEC Pty Ltd.
"""BC15/BC25 Configuration."""

import logging
import math

import attr
import tester

import share


def get(parameter, uut):
    """Get a configuration based on the parameter and lot.

    @param parameter Type of unit
    @param uut setec.UUT instance
    @return configuration class

    """
    config = {
        "15": BC15,
        "25": BC25,
    }[parameter]
    config._configure(uut)  # Adjust for the Lot Number
    return config


@attr.s
class _Values:

    """Adjustable configuration data values."""

    arm_file = attr.ib(validator=attr.validators.instance_of(str))
    arm_port = attr.ib(validator=attr.validators.instance_of(str))
    sw_version = attr.ib(validator=attr.validators.instance_of(str))
    cal_linecount = attr.ib(validator=attr.validators.instance_of(int))


class BCx5:

    """Base configuration for BC15/25."""

    # These values get set per Product type & revision
    arm_file = None  # Software image filename
    arm_port = None  # ARM console serial port
    sw_version = None  # Software version number
    cal_linecount = None  # Number of lines to a CAL? command
    # General parameters used in testing the units
    #  AC voltage powering the unit
    vac = 240.0
    #  Output set point
    vout_set = 14.40
    # Initial Test limits common to both versions
    _base_limits_initial = (
        tester.LimitLow("FixtureLock", 20),
        tester.LimitHigh("FanShort", 100),
        tester.LimitDelta("ACin", vac, 5.0),
        tester.LimitDelta("Vbus", math.sqrt(2) * vac, 10.0),
        tester.LimitDelta("14Vpri", 14.0, 1.0),
        tester.LimitBetween("12Vs", 11.7, 13.0),
        tester.LimitBetween("3V3", 3.20, 3.35),
        tester.LimitLow("FanOn", 0.5),
        tester.LimitHigh("FanOff", 11.0),
        tester.LimitDelta("15Vs", 15.5, 1.0),
        tester.LimitPercent("Vout", vout_set, 4.0),
        tester.LimitPercent("VoutCal", vout_set, 1.0),
        tester.LimitLow("VoutOff", 2.0),
        tester.LimitLow("InOCP", 13.5),
        tester.LimitPercent("ARM-Vout", vout_set, 5.0),
        tester.LimitPercent("ARM-2amp", 2.0, percent=1.7, delta=1.0),
        tester.LimitInteger("ARM-switch", 3),
    )
    # Final Test limits common to both versions
    _base_limits_final = (
        tester.LimitDelta("VoutNL", 13.6, 0.3),
        tester.LimitDelta("Vout", 13.6, 0.7),
        tester.LimitLow("InOCP", 12.5),
    )
    # Internal data storage
    _rev_data = None  # Revision data dictionary

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut setec.UUT instance

        """
        rev = uut.revision
        logging.getLogger(__name__).debug("Revision detected as %s", rev)
        values = cls._rev_data[rev]
        cls.arm_file = values.arm_file
        cls.arm_port = values.arm_port
        cls.sw_version = values.sw_version
        cls.cal_linecount = values.cal_linecount


class BC15(BCx5):

    """BC15 configuration."""

    sw_version = "2.0.18498.2003"
    arm_file_pattern = "bc15_{0}.bin"
    arm_port = share.config.Fixture.port("028467", "ARM")
    _rev8_values = _Values(
        arm_file=arm_file_pattern.format(sw_version),
        arm_port=arm_port,
        sw_version=sw_version,
        cal_linecount=43,
    )
    _rev_data = {
        None: _rev8_values,
        "8": _rev8_values,
        "7": _rev8_values,
        "6": _rev8_values,
        "5": _rev8_values,
        "4": _rev8_values,
        # Rev 1-3 Scrap
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
            super()._base_limits_initial
            + (
                tester.LimitLow("5Vs", 99.0),  # No test point
                tester.LimitRegExp(
                    "ARM-SwVer", "^{0}$".format(cls.sw_version.replace(".", r"\."))
                ),
                tester.LimitPercent("OCP_pre", ocp_nominal, 15),
                tester.LimitPercent("OCP_post", ocp_nominal, 2.0),
                tester.LimitPercent(
                    "ARM-HIamp", ocp_nominal * ocp_load_factor, percent=1.7, delta=1.0
                ),
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
            super()._base_limits_final
            + (tester.LimitPercent("OCP", ocp_nominal, (4.0, 7.0)),),
        )


class BC25(BCx5):

    """BC25 configuration."""

    sw_version = "2.0.20136.2004"
    arm_file_pattern = "bc25_{0}.bin"
    arm_port = share.config.Fixture.port("031032", "ARM")
    _rev5_values = _Values(
        arm_file=arm_file_pattern.format(sw_version),
        arm_port=arm_port,
        sw_version=sw_version,
        cal_linecount=43,
    )
    _rev_data = {
        None: _rev5_values,
        "5": _rev5_values,
        "4": _rev5_values,
        "3": _rev5_values,
        # Rev 1,2 Scrap
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
            super()._base_limits_initial
            + (
                tester.LimitDelta("5Vs", 4.95, 0.15),
                tester.LimitRegExp(
                    "ARM-SwVer", "^{0}$".format(cls.sw_version.replace(".", r"\."))
                ),
                tester.LimitPercent("OCP_pre", ocp_nominal, 15),
                tester.LimitPercent("OCP_post", ocp_nominal, 2.0),
                tester.LimitPercent(
                    "ARM-HIamp", ocp_nominal * ocp_load_factor, percent=1.7, delta=1.0
                ),
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
            super()._base_limits_final
            + (tester.LimitPercent("OCP", ocp_nominal, (4.0, 7.0)),),
        )
