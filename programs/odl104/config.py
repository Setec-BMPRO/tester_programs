#!/usr/bin/env python3
# Copyright 2022 SETEC Pty Ltd
"""ODL104/5 Configuration."""

import logging

import libtester
import share


def get(parameter, uut):
    """Get configuration based on UUT Lot Number.

    @param parameter Type of unit
    @param uut libtester.UUT instance
    @return configuration class

    """
    cfg = {
        "104": ODL104,
        "105": ODL105,
    }[parameter]
    cfg._configure(uut)  # Adjust for the revision
    return cfg.parameters


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

    def __init__(self, sw_nordic_image, hw_version):
        """Create instance.

        @param sw_nordic_image Nordic image
        @param hw_version Hardware version

        """
        self.sw_nordic_image = sw_nordic_image
        self.hw_version = hw_version


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

    _nordic_115 = "odl104_v2.0.0-0-g5f506a0-signed-mcuboot-factory.hex"
    _rev5_values = ODL10xParameters(
        sw_nordic_image=_nordic_115, hw_version=("05A", "01A"))
    _rev_data = {
        None: _rev5_values,
        "5": _rev5_values,
        "4": ODL10xParameters(
            sw_nordic_image=_nordic_115, hw_version=("04A", "01A")),
        "3": ODL10xParameters(
            sw_nordic_image=_nordic_115, hw_version=("03A", "01A")),
        "2": ODL10xParameters(
            sw_nordic_image=_nordic_115, hw_version=("02B", "01A")),
        "1": ODL10xParameters(
            sw_nordic_image=_nordic_115, hw_version=("01C", "01A")),
    }


class ODL105:
    """Configuration for ODL105."""

    parameters = None  # Instance of ODL10xParameters

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut libtester.UUT instance

        """
        rev = uut.revision
        logging.getLogger(__name__).debug("Revision detected as %s", rev)
        cls.parameters = cls._rev_data[rev]

    _nordic_115 = "odl104_v1.1.5-0-gd1a790f-signed-mcuboot-factory.hex"
    _rev1_values = ODL10xParameters(
        sw_nordic_image=_nordic_115, hw_version=("01A", "01A"))
    _rev_data = {
        None: _rev1_values,
        "1": _rev1_values,
    }
