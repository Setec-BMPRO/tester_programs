#!/usr/bin/env python3
# Copyright 2022 SETEC Pty Ltd
"""ODL104 Configuration."""

import logging

import libtester
import share


def get(parameter, uut):
    """Get configuration based on UUT Lot Number.

    @param parameter Type of unit
    @param uut libtester.UUT instance
    @return configuration class

    """
    ODL104._configure(uut)  # Adjust for the revision
    return ODL104.parameters


class ODL10xParameters:
    """ODL10x model specific parameters."""

    # Initial test limits
    limits_common = (
        libtester.LimitRegExp("BleMac", share.MAC.regex, doc="Valid MAC address"),
    )
    # Initial test limits
    limits_initial = limits_common + (
        libtester.LimitLow("Part", 500.0),
        libtester.LimitDelta("Vin", 8.0, 0.5),
        libtester.LimitPercent("3V3", 3.30, 3.0),
        libtester.LimitInteger("Tank", 5),
        libtester.LimitBoolean("CANok", True, doc="CAN bus active"),
    )
    # Final test limits
    limits_final = limits_common + (
        libtester.LimitBoolean("ScanMac", True, doc="MAC address detected"),
        libtester.LimitHigh("ScanRSSI", float("NaN"), doc="Strong BLE signal"),
    )

    def __init__(self, sw_nordic_image, hw_version, banner_lines):
        """Create instance.

        @param sw_nordic_image Nordic image
        @param hw_version Hardware version
        @param banner_lines Number of startup banner lines

        """
        self.sw_nordic_image = sw_nordic_image
        self.hw_version = hw_version
        self.banner_lines = banner_lines


class ODL104:
    """Configuration for ODL104."""

    parameters = None  # Instance of ODL10xParameters

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut libtester.UUT instance

        """
        rev = uut.revision
        logging.getLogger(__name__).debug("Revision detected as %s", rev)
        cls.parameters = cls._rev_data[rev]

    _nordic_107 = "odl104_v1.0.7-0-g2c7123e-signed-mcuboot-factory.hex"
    _rev3_values = ODL10xParameters(
        sw_nordic_image=_nordic_107, hw_version=("03A", "01A"), banner_lines=1
    )
    _rev_data = {  # Revision data dictionary
        None: _rev3_values,
        "3": _rev3_values,
        "2": ODL10xParameters(
            sw_nordic_image=_nordic_107, hw_version=("02B", "01A"), banner_lines=1
        ),
        "1": ODL10xParameters(
            sw_nordic_image=_nordic_107, hw_version=("01C", "01A"), banner_lines=1
        ),
    }
