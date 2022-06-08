#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2022 SETEC Pty Ltd
"""ODL104 Configuration."""

import logging

import tester
import share


def get(parameter, uut):
    """Get configuration based on UUT Lot Number.

    @param parameter Type of unit
    @param uut setec.UUT instance
    @return configuration class

    """
    ODL104._configure(uut)    # Adjust for the revision
    return ODL104.parameters


class ODL10xParameters():

    """ODL10x model specific parameters."""

    # Initial test limits
    limits_common = (
        tester.LimitRegExp('BleMac', '^[0-9a-f]{12}$',
            doc='Valid MAC address'),
        )
    # Initial test limits
    limits_initial = limits_common + (
        tester.LimitLow('Part', 500.0),
        tester.LimitDelta('Vin', 8.0, 0.5),
        tester.LimitPercent('3V3', 3.30, 3.0),
        tester.LimitInteger('Tank', 5),
        tester.LimitBoolean('CANok', True, doc='CAN bus active'),
        )
    # Final test limits
    limits_final = limits_common + (
        tester.LimitBoolean('ScanMac', True, doc='MAC address detected'),
        tester.LimitHigh(
            'ScanRSSI',
            -70 if share.config.System.tester_type in (
                'ATE4', 'ATE5') else -85,
            doc='Strong BLE signal'),
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


class ODL104():

    """Configuration for ODL104."""

    # Instance of ODL10xParameters
    parameters = None

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut setec.UUT instance

        """
        try:
            rev = uut.lot.item.revision
        except AttributeError:
            rev = None
        logging.getLogger(__name__).debug('Revision detected as %s', rev)
        cls.parameters = cls._rev_data[rev]

    _nordic_104 = 'odl104_nordic_1.0.4-0-g539e803.hex'
    _rev1_values = ODL10xParameters(
            sw_nordic_image=_nordic_104,
            hw_version=('01A', '01A'),
            banner_lines=1
            )
    # Revision data dictionary:
    _rev_data = {
        None: _rev1_values,
        '1': _rev1_values,
        }
