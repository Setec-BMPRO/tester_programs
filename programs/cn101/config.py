#!/usr/bin/env python3
# Copyright 2021 SETEC Pty Ltd
"""CN101 Configuration."""

import logging

import libtester


def get(parameter, uut):
    """Get configuration based on UUT Lot Number.

    @param parameter Type of unit
    @param uut libtester.UUT instance
    @return configuration class

    """
    CN101._configure(uut)  # Adjust for the revision
    return CN101


class CN101:
    """CN101 parameters."""

    # Initial test limits
    limits_initial = (
        libtester.LimitRegExp(
            "SwVer", "None", doc="Software version"  # Adjusted during _configure()
        ),
        libtester.LimitLow("Part", 100.0),
        libtester.LimitDelta("Vin", 8.0, 0.5),
        libtester.LimitPercent("3V3", 3.30, 3.0),
        libtester.LimitInteger("CAN_BIND", 1 << 28),
        libtester.LimitRegExp("BtMac", r"(?:[0-9A-F]{2}:?){5}[0-9A-F]{2}"),
        libtester.LimitBoolean("DetectBT", True),
        libtester.LimitInteger("Tank", 5),
    )
    # These values get set per revision
    sw_version = None
    hw_version = None
    banner_lines = None
    # Revision data dictionary:
    _rev6_values = (
        "1.2.17835.298",
        (6, 0, "A"),
        2,
    )
    _rev_data = {
        None: _rev6_values,
        "6": _rev6_values,
        "5": (
            "1.1.13665.176",
            (5, 0, "A"),
            0,
        ),
    }

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut libtester.UUT instance

        """
        rev = uut.revision
        logging.getLogger(__name__).debug("Revision detected as %s", rev)
        cls.sw_version, cls.hw_version, cls.banner_lines = cls._rev_data[rev]
