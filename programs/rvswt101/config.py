#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVSWT101 Configuration."""

import tester


class Config():

    """RVSWT101 configuration."""

    # Possible switch variants.
    #   From "033325 RVSWT Series Product Specification -D"
    _types = {
        # For the 3 TMC types: BLE Code is Label Code - 1 ...
        '4gp1': 0, '6gp1': 2, '6gp2': 3,
        'j3-1': 16, 'j3-2': 17, 'j3-3': 18, 'j3-4': 29, 'j3-5': 30,
            'j3-6': 31, 'j3-7': 5, 'j3-8': 47,
        'j4-1': 19, 'j4-2': 20, 'j4-4': 21, 'j4-5': 32, 'j4-6': 6, 'j4-7': 7,
            'j4-8': 48,
        'j5-1': 22, 'j5-2': 23, 'j5-3': 33, 'j5-4': 34, 'j5-5': 49, 'j5-6': 8,
            'j5-7': 9, 'j5-8': 45,
        'j6-1': 25, 'j6-2': 35, 'j6-3': 10, 'j6-4': 11, 'j6-5': 12,
            'j6-6': 50, 'j6-7': 36, 'j6-8': 27, 'j6-9': 46,
        'j7-1': 38,
        'j8-1': 37, 'j8-2': 28, 'j8-3': 39,
        'j9-1': 40,
        'j10-1': 13, 'j10-2': 41,
        'j11-1': 14, 'j11-2': 15, 'j11-3': 42, 'j11-4': 51,
        }
    # Software images
    _software = {   # Rev 2 'gp' units, Rev 3/4 'j' units
        '4gp1': 'rvswt101_4gp1_1.2.hex',
        '6gp1': 'rvswt101_6gp1_1.2.hex',
        '6gp2': 'rvswt101_6gp2_1.2.hex',
        'series': 'rvswt101_series_1.5.hex',
        }
    # Common Test limits
    _common_limits = (
        tester.LimitRegExp('BleMac', '^[0-9a-f]{12}$',
            doc='Valid MAC address'),
        tester.LimitBoolean('ScanMac', True,
            doc='MAC address detected'),
        )
    # Initial Test limits
    _initial_limits = (
        tester.LimitDelta('Vin', 3.3, 0.3,
            doc='Injected power'),
        )
    # Final Test limits
    _final_limits = (
        tester.LimitBoolean('ButtonOk', True,
            doc='Ok entered'),
        tester.LimitDelta('CellVoltage', 3.3, 0.3,
            doc='Button cell charged'),
        )

    @classmethod
    def get(cls, parameter, uut):

        """Get configuration.

        @param parameter String to select the switch type
        @param uut storage.UUT instance
        @return Dictionary of configuration data

        """
        if parameter == 'series':       # Initial builds of Rev 3
            type_lim = tester.LimitBetween(
                'SwitchType', 1, 42, doc='Switch type code')
        else:                           # Later builds of Rev 3+
            switch_type = cls._types[parameter]
            type_lim = tester.LimitInteger(
                'SwitchType', switch_type, doc='Switch type code')
        if parameter in cls._software:  # Rev 2 hard coded switch types
            image = cls._software[parameter]
            banner_lines = 1
        else:                           # Rev 3+ auto-coded switch types
            image = cls._software['series']
            banner_lines = 2
        # Force code the RVSWT101 switch code as required
        forced_code = 0
        if uut:
            lot = uut.lot
            try:
                forced_code = {
                    # PC-5092: Force J11-1 to be J11-3
                    'A193824': cls._types['j11-3'],
                    }[lot]
            except KeyError:
                pass
        return {
            'software': image,
            'limits_ini': cls._common_limits + cls._initial_limits,
            'limits_fin': (
                cls._common_limits + cls._final_limits + (type_lim, )
                ),
            'banner_lines': banner_lines,
            'forced_code': forced_code,
            }
