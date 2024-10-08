#!/usr/bin/env python3
# Copyright 2018 SETEC Pty Ltd
"""CN102/3 Configuration."""

import logging

import libtester


def get(parameter, uut):
    """Get configuration based on UUT Lot Number.

    @param parameter Type of unit
    @param uut libtester.UUT instance
    @return configuration class

    """
    config = {
        "102": CN102,
        "103": CN103,
    }[parameter]
    config._configure(uut)  # Adjust for the revision
    return config.parameters


class CN10xParameters:
    """CN10x model specific parameters."""

    limits_initial = (
        libtester.LimitRegExp(
            "SwArmVer", "None", doc="ARM Software version"  # Adjusted during open()
        ),
        libtester.LimitRegExp(
            "SwNrfVer", "None", doc="Nordic Software version"  # Adjusted during open()
        ),
        libtester.LimitLow("Part", 500.0),
        libtester.LimitDelta("Vin", 8.0, 0.5),
        libtester.LimitPercent("3V3", 3.30, 3.0),
        libtester.LimitInteger("CAN_BIND", 1 << 28),
        libtester.LimitBoolean("ScanSer", True, doc="Serial number detected"),
        libtester.LimitInteger("Tank", 5),
        libtester.LimitBoolean("CANok", True, doc="CAN bus active"),
    )
    limits_final = (
        libtester.LimitHigh("ScanRSSI", float("NaN"), doc="Strong BLE signal"),
    )

    def __init__(
        self, prefix, sw_nxp_version, sw_nordic_version, hw_version, banner_lines
    ):
        """Create instance.

        @param prefix Filename prefix ('cn102' or 'cn103')
        @param sw_nxp_version NXP version
        @param sw_nordic_version Nordic version
        @param hw_version Hardware version
        @param banner_lines Number of startup banner lines

        """
        self.sw_nxp_image = "{0}_nxp_{1}.bin".format(prefix, sw_nxp_version)
        self.sw_nordic_image = "{0}_nordic_{1}.hex".format(prefix, sw_nordic_version)
        self.hw_version = hw_version
        self.banner_lines = banner_lines


class CN10x:
    """Configuration for CN10x."""

    # These values get overriden by child classes
    _rev_data = None
    # Instance of CN10xParameters
    parameters = None

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut libtester.UUT instance

        """
        rev = uut.revision
        logging.getLogger(__name__).debug("Revision detected as %s", rev)
        cls.parameters = cls._rev_data[rev]


class CN102(CN10x):
    """Configuration for CN102."""

    _prefix = "cn102"
    # Software versions
    _values = CN10xParameters(
        prefix=_prefix,
        sw_nxp_version="1.2.18218.1627",
        sw_nordic_version="1.0.18106.1260",
        hw_version=(1, 0, "A"),
        banner_lines=2,
    )
    # Revision data dictionary:
    _rev_data = {
        None: _values,
        "1": _values,
    }


class CN103(CN10x):
    """Configuration for CN103."""

    _prefix = "cn103"
    # Software versions
    _nxp_1_2 = "1.2.111.2008"
    _nxp_3 = "1.3.111.2013"
    _nordic = "1.0.19700.1352"
    _rev3_values = CN10xParameters(
        prefix=_prefix,
        sw_nxp_version=_nxp_3,
        sw_nordic_version=_nordic,
        hw_version=(3, 0, "A"),
        banner_lines=2,
    )
    # Revision data dictionary:
    _rev_data = {
        None: _rev3_values,
        "3": _rev3_values,
        "2": CN10xParameters(
            prefix=_prefix,
            sw_nxp_version=_nxp_1_2,
            sw_nordic_version=_nordic,
            hw_version=(2, 0, "A"),
            banner_lines=2,
        ),
        "1": CN10xParameters(
            prefix=_prefix,
            sw_nxp_version=_nxp_1_2,
            sw_nordic_version=_nordic,
            hw_version=(1, 0, "A"),
            banner_lines=2,
        ),
    }
