#!/usr/bin/env python3
# Copyright 2015 SETEC Pty Ltd.
"""JControl/Trek2/Trek3/TrekX Configuration."""

import libtester


def get(parameter):
    """Get a configuration based on the parameter.

    @param parameter Type of unit
    @return configuration class

    """
    return {
        "JC": JControl,
        "TK2": Trek2,
        "TK3": Trek3,
        "TKX": TrekX,
    }[parameter]


class _Limits:
    """Test limits."""

    vin_start = 8.0  # Startup voltage
    vin_set = 12.0  # Input voltage to power the unit
    initial = (
        libtester.LimitDelta("Vin", vin_start - 0.75, 0.5, doc="Input voltage present"),
        libtester.LimitPercent("3V3", 3.3, 3.0, doc="3V3 present"),
        # CAN Bus is operational if status bit 28 is set
        libtester.LimitInteger("CAN_BIND", 1 << 28, doc="CAN bus bound"),
    )
    final = (
        libtester.LimitInteger("ARM-level1", 1),
        libtester.LimitInteger("ARM-level2", 2),
        libtester.LimitInteger("ARM-level3", 3),
        libtester.LimitInteger("ARM-level4", 4),
    )


class JControl(_Limits):
    """JControl configuration."""

    sw_version = "1.7.20388.329"  # 035826 Rev 2      PC-24868
    sw_image = "jcontrol_{0}.bin".format(sw_version)
    hw_version = (4, 2, "B")
    _sw_lim = libtester.LimitRegExp(
        "SwVer", r"^{0}$".format(sw_version.replace(".", r"\.")))

    @classmethod
    def initial_limits(cls):
       """Initial test limits."""
       return cls.initial + (cls._sw_lim, )

    @classmethod
    def final_limits(cls):
       """Final test limits."""
       return cls.final + (cls._sw_lim, )


class Trek2(_Limits):
    """Trek2 configuration."""

    sw_version = "1.7.20512.331"  # 035862 Rev 2      MA-378
    sw_image = "trek3_{0}.bin".format(sw_version)
    hw_version = (7, 0, "C")
    _sw_lim = libtester.LimitRegExp(
        "SwVer", r"^{0}$".format(sw_version.replace(".", r"\.")))

    @classmethod
    def initial_limits(cls):
       """Initial test limits."""
       return cls.initial + (cls._sw_lim, )

    @classmethod
    def final_limits(cls):
       """Final test limits."""
       return cls.final + (cls._sw_lim, )


class Trek3(_Limits):
    """Trek3 configuration."""

    sw_version = "1.7.20512.331"  # 035862 Rev 2      PC-25163
    sw_image = "trek3_{0}.bin".format(sw_version)
    hw_version = (1, 0, "B")
    _sw_lim = libtester.LimitRegExp(
        "SwVer", r"^{0}$".format(sw_version.replace(".", r"\.")))

    @classmethod
    def initial_limits(cls):
       """Initial test limits."""
       return cls.initial + (cls._sw_lim, )

    @classmethod
    def final_limits(cls):
       """Final test limits."""
       return cls.final + (cls._sw_lim, )


class TrekX(_Limits):
    """TrekX configuration."""

    sw_version = "1.0.17722284.12"  # Pilot run
    sw_image = "trekx_{0}.bin".format(sw_version)
    hw_version = (1, 0, "B")
    _sw_lim = libtester.LimitRegExp(
        "SwVer", r"^{0}$".format(sw_version.replace(".", r"\.")))

    @classmethod
    def initial_limits(cls):
       """Initial test limits."""
       return cls.initial + (cls._sw_lim, )

    @classmethod
    def final_limits(cls):
       """Final test limits."""
       return cls.final + (cls._sw_lim, )
