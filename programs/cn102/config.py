#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2018 SETEC Pty Ltd
"""CN102/3 Configuration."""

import logging

import tester
import share


def get(parameter, uut):
    """Get configuration based on UUT Lot Number.

    @param parameter Type of unit
    @param uut setec.UUT instance
    @return configuration class

    """
    config = {
        '102': CN102,
        '103': CN103,
        '104': ODL104,
        }[parameter]
    config._configure(uut)    # Adjust for the revision
    return config.parameters


class CN10xParameters():

    """CN10x model specific parameters."""

    # Initial test limits
    limits_initial = (
        tester.LimitRegExp('SwArmVer', '',      # Adjusted during open()
            doc='ARM Software version'),
        tester.LimitRegExp('SwNrfVer', '',      # Adjusted during open()
            doc='Nordic Software version'),
        tester.LimitLow('Part', 500.0),
        tester.LimitDelta('Vin', 8.0, 0.5),
        tester.LimitPercent('3V3', 3.30, 3.0),
        tester.LimitInteger('CAN_BIND', 1 << 28),
        tester.LimitBoolean('ScanSer', True,
            doc='Serial number detected'),
        tester.LimitInteger('Tank', 5),
        tester.LimitBoolean('CANok', True, doc='CAN bus active'),
        )

    # Final test limits
    limits_final = (
        tester.LimitHigh(
            'ScanRSSI',
            -70 if share.config.System.tester_type in (
                'ATE4', 'ATE5') else -85,
            doc='Strong BLE signal'),
        )

    def __init__(self,
            prefix,
            sw_nxp_version, sw_nordic_version,
            hw_version, banner_lines):
        """Create instance.

        @param prefix Filename prefix ('cn102' or 'cn103')
        @param sw_nxp_version NXP version
        @param sw_nordic_version Nordic version
        @param hw_version Hardware version
        @param banner_lines Number of startup banner lines

        """
        self.sw_nxp_image = '{0}_nxp_{1}.bin'.format(
            prefix, sw_nxp_version)
        self.sw_nordic_image = '{0}_nordic_{1}.hex'.format(
            prefix, sw_nordic_version)
        self.hw_version = hw_version
        self.banner_lines = banner_lines


class CN10x():

    """Configuration for CN10x."""

    # These values get overriden by child classes
    _rev_data = None
    # Instance of CN10xParameters
    parameters = None

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut setec.UUT instance

        """
        rev = uut.revision
        logging.getLogger(__name__).debug('Revision detected as %s', rev)
        cls.parameters = cls._rev_data[rev]


class CN102(CN10x):

    """Configuration for CN102."""

    _prefix = 'cn102'
    # Software versions
    _values = CN10xParameters(
            prefix=_prefix,
            sw_nxp_version='1.2.18218.1627',
            sw_nordic_version='1.0.18106.1260',
            hw_version=(1, 0, 'A'),
            banner_lines=2
            )
    # Revision data dictionary:
    _rev_data = {
        None: _values,
        '1': _values,
        }


class CN103(CN10x):

    """Configuration for CN103."""

    _prefix = 'cn103'
    # Software versions
    _nxp_1_2 = '1.2.111.2008'
    _nxp_3 = '1.3.111.2013'
    _nordic = '1.0.19700.1352'
    _rev3_values = CN10xParameters(
            prefix=_prefix,
            sw_nxp_version=_nxp_3,
            sw_nordic_version=_nordic,
            hw_version=(3, 0, 'A'),
            banner_lines=2
            )
    # Revision data dictionary:
    _rev_data = {
        None: _rev3_values,
        '3': _rev3_values,
        '2': CN10xParameters(
            prefix=_prefix,
            sw_nxp_version=_nxp_1_2,
            sw_nordic_version=_nordic,
            hw_version=(2, 0, 'A'),
            banner_lines=2
            ),
        '1': CN10xParameters(
            prefix=_prefix,
            sw_nxp_version=_nxp_1_2,
            sw_nordic_version=_nordic,
            hw_version=(1, 0, 'A'),
            banner_lines=2
            ),
        }

class ODL104(CN10x):

    """Configuration for ODL104."""

    _prefix = 'odl104'
    _nordic_104 = '1.0.4-0-g539e803'
    _rev1_values = CN10xParameters(
            prefix=_prefix,
            sw_nxp_version=None,
            sw_nordic_version=_nordic_104,
            hw_version=('01A', '01A'),
            banner_lines=1
            )
    # Revision data dictionary:
    _rev_data = {
        None: _rev1_values,
        '1': _rev1_values,
        }
