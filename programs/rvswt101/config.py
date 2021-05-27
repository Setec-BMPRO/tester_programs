#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVSWT101 Configuration."""

import tester


class Config():

    """RVSWT101 configuration."""

    # Possible switch variants tuple(switch_type,  button_count)
    #   switch_type from "034800 RVSWT Series Product Specification -F"
    #   button_count from "035557 RVSWT Series Production Notes -G.pdf"
    _types = {
        # For the 3 TMC types: BLE Code is Label Code - 1 ...
        '4gp1': (0, 4), '6gp1': (2, 6), '6gp2': (3, 6),
         'j3-1': (16, 6), 'j3-2': (17, 6), 'j3-3': (18, 6),
         'j3-4': (29, 6), 'j3-5': (30, 6),
         'j3-6': (31, 6), 'j3-7': (5, 4), 'j3-8': (47, 4), 'j3-9': (52, 4),
         'j4-1': (19, 6), 'j4-2': (20, 6), 'j4-4': (21, 6), 'j4-5': (32, 6),
         'j4-6': (6, 4), 'j4-7': (7, 4),
         'j4-8': (48, 4), 'j4-9': (53, 4),
         'j5-1': (22, 6), 'j5-2': (23, 6), 'j5-3': (33, 6), 'j5-4': (34, 6),
         'j5-5': (49, 4), 'j5-6': (8, 4),
         'j5-7': (9, 4), 'j5-8': (45, 6), 'j5-9': (56, 6),
         'j6-1': (25, 6), 'j6-2': (35, 6), 'j6-3': (10, 4), 'j6-4': (11, 4),
         'j6-5': (12, 4),
         'j6-6': (50, 4), 'j6-7': (36, 6), 'j6-8': (27, 6), 'j6-9': (46, 6),
         'j7-1': (38, 4),
         'j8-1': (37, 6), 'j8-2': (28, 6), 'j8-3': (39, 4), 'j8-4': (57, 6),
         'j9-1': (40, 4),
         'j10-1': (13, 4), 'j10-2': (41, 4),
         'j11-1': (14, 4), 'j11-2': (15, 4), 'j11-3': (42, 4), 'j11-4': (51, 4),
         'j11-5': (54, 4), 'j11-6': (55, 4)}
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
        tester.LimitRegExp('Reply', '^OK$'),
        tester.LimitInteger('no_button_expected', 0,
            doc='No button pressed'),
        tester.LimitInteger('switch_1_expected', 128,
            doc='Correct switch pressed'),
        tester.LimitInteger('switch_2_expected', 64,
            doc='Correct switch pressed'),
        tester.LimitInteger('switch_3_expected', 32,
            doc='Correct switch pressed'),
        tester.LimitInteger('switch_4_expected', 16,
            doc='Correct switch pressed'),
        tester.LimitInteger('switch_5_expected', 8,
            doc='Correct switch pressed'),
        tester.LimitInteger('switch_6_expected', 4,
            doc='Correct switch pressed'),
        )

    @classmethod
    def get(cls, parameter, uut):

        """Get configuration.

        @param parameter String to select the switch type
        @param uut setec.UUT instance
        @return Dictionary of configuration data

        """
        if parameter == 'series':       # Initial builds of Rev 3
            type_lim = tester.LimitBetween(
                'SwitchType', 1, 42, doc='Switch type code')
        else:                           # Later builds of Rev 3+
            switch_type,  button_count = cls._types[parameter]
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
        fixture_num = '033030'          # RVSWT101 Final Fixture
        if uut:
            try:
                forced_code = {
                    # PC-5092: Force J11-1 to be J11-3
                    'A193824': cls._types['j11-3'],
                    }[uut.lot.number]
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
            'fixture_num': fixture_num,
            'button_count': button_count, 
            }
