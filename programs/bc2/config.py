#!/usr/bin/env python3
# Copyright 2017 SETEC Pty Ltd
"""BC2 Configuration."""

import logging

from attrs import define, field, validators

import libtester


def get(parameter, uut):
    """Select a configuration based on the parameter.

    @param parameter Type of unit (100/300/PRO)
    @param uut libtester.UUT instance
    @return configuration class

    """
    config = {
        "100": BatteryCheck100,
        "300": BatteryCheck300,
        "PRO": BatteryCheckPRO,
    }[parameter]
    config._configure(uut)  # Adjust for the revision
    return config


@define
class _Values:
    """Adjustable configuration data values."""

    hw_version = field(validator=validators.instance_of(tuple))
    sw_version = field(validator=validators.instance_of(str))


class Config:
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
        libtester.LimitDelta("Vin", vbatt, 0.5, doc="Input voltage present"),
    )
    # Initial Test limits common to all units
    _base_limits_initial = _base_limits + (
        libtester.LimitPercent("3V3", 3.3, 3.0, doc="3V3 present"),
        libtester.LimitRegExp(
            "BtMac", "(?:[0-9A-F]{2}:?){5}[0-9A-F]{2}", doc="Valid MAC address "
        ),
        libtester.LimitBoolean("DetectBT", True, doc="MAC address detected"),
        libtester.LimitRegExp("ARM-CalOk", "cal success:", doc="Calibration success"),
        libtester.LimitBetween(
            "ARM-I_ADCOffset", -3, 3, doc="Current ADC offset calibrated"
        ),
        libtester.LimitBetween(
            "ARM-VbattLSB", 2391, 2489, doc="LSB voltage calibrated"
        ),
        libtester.LimitPercent(
            "ARM-Vbatt", vbatt, 0.5, delta=0.02, doc="Battery voltage calibrated"
        ),
        libtester.LimitHigh("ScanRSSI", -90, doc="BLE signal"),
    )
    # Final Test limits common to all units
    _base_limits_final = _base_limits + (
        libtester.LimitRegExp(
            "ARM-QueryLast", "cal success:", doc="Calibration success"
        ),
    )
    _sw_1_0 = "1.0.16764.1813"
    _sw_1_7 = "1.7.17895.1845"
    _sw_2_0 = "2.0.0.2226"
    _rev_data = {
        None: _Values((7, 0, "A"), _sw_2_0),
        "7": _Values((7, 0, "A"), _sw_2_0),
        "6": _Values((6, 0, "A"), _sw_2_0),
        "5": _Values((5, 0, "A"), _sw_1_7),
        "4": _Values((4, 0, "A"), _sw_1_0),
        "3": _Values((3, 0, "A"), _sw_1_0),
        "2": _Values((2, 0, "A"), _sw_1_0),
        "1": _Values((1, 0, "A"), _sw_1_0),
    }

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut libtester.UUT instance

        """
        rev = uut.revision
        logging.getLogger(__name__).debug("Revision detected as %s", rev)
        values = cls._rev_data[rev]
        cls.hw_version = values.hw_version
        cls.sw_version = values.sw_version
        cls._swver_limit = (
            libtester.LimitRegExp(
                "ARM-SwVer",
                "^{0}$".format(cls.sw_version.replace(".", r"\.")),
                doc="Software version",
            ),
        )


class BatteryCheck100(Config):
    """BatteryCheck100 configuration."""

    model = 0  # Model selector code

    @classmethod
    def limits_initial(cls):
        """Initial test limits.

        @return Tuple(limits)

        """
        return (
            cls._swver_limit
            + cls._base_limits_initial
            + (
                libtester.LimitDelta(
                    "ARM-IbattZero", 0.0, 0.031, doc="Zero battery current calibrated"
                ),
            )
        )

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        return (
            cls._swver_limit
            + cls._base_limits_final
            + (
                libtester.LimitPercent(
                    "ARM-ShuntRes", 800000, 5.0, doc="Shunt resistance calibrated"
                ),
                libtester.LimitPercent(
                    "ARM-Ibatt",
                    cls.ibatt,
                    1,
                    delta=0.031,
                    doc="Battery current calibrated",
                ),
            )
        )


class BatteryCheck300(Config):
    """BatteryCheck300 configuration."""

    model = 1  # Model selector code

    @classmethod
    def limits_initial(cls):
        """Initial test limits.

        @return Tuple(limits)

        """
        return (
            cls._swver_limit
            + cls._base_limits_initial
            + (
                libtester.LimitDelta(
                    "ARM-IbattZero", 0.0, 0.3, doc="Zero battery current calibrated"
                ),
            )
        )

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        return (
            cls._swver_limit
            + cls._base_limits_final
            + (
                libtester.LimitPercent(
                    "ARM-ShuntRes", 90000, 30.0, doc="Shunt resistance calibrated"
                ),
                libtester.LimitPercent(
                    "ARM-Ibatt",
                    cls.ibatt,
                    3,
                    delta=0.3,
                    doc="Battery current calibrated",
                ),
            )
        )


class BatteryCheckPRO(BatteryCheck300):
    """BatteryCheckPRO configuration."""

    model = 2  # Model selector code
