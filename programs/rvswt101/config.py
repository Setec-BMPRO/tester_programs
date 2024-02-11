#!/usr/bin/env python3
# Copyright 2019 SETEC Pty Ltd.
"""RVSWT101 Configuration."""

import tester


class Config:

    """RVSWT101 configuration."""

    # Possible switch variants tuple(switch_type,  button_count)
    #   switch_type from "RVSWT Series Product Specification"
    #   button_count from "RVSWT Series Production Notes"
    _types = {
        # For the 3 TMC types: BLE Code is Label Code - 1 ...
        "4gp1": (0, 4),
        "6gp1": (2, 6),
        "6gp2": (3, 6),
        "j3-1": (16, 6),
        "j3-2": (17, 6),
        "j3-3": (18, 6),
        "j3-4": (29, 6),
        "j3-5": (30, 6),
        "j3-6": (31, 6),
        "j3-7": (5, 4),
        "j3-8": (47, 4),
        "j3-9": (52, 4),
        "j4-1": (19, 6),
        "j4-2": (20, 6),
        "j4-4": (21, 6),
        "j4-5": (32, 6),
        "j4-6": (6, 4),
        "j4-7": (7, 4),
        "j4-8": (48, 4),
        "j4-9": (53, 4),
        "j5-1": (22, 6),
        "j5-2": (23, 6),
        "j5-3": (33, 6),
        "j5-4": (34, 6),
        "j5-5": (49, 4),
        "j5-6": (8, 4),
        "j5-7": (9, 4),
        "j5-8": (45, 6),
        "j5-9": (56, 6),
        "j6-1": (25, 6),
        "j6-2": (35, 6),
        "j6-3": (10, 4),
        "j6-4": (11, 4),
        "j6-5": (12, 4),
        "j6-6": (50, 4),
        "j6-7": (36, 6),
        "j6-8": (27, 6),
        "j6-9": (46, 6),
        "j7-1": (38, 4),
        "j8-1": (37, 6),
        "j8-2": (28, 6),
        "j8-3": (39, 4),
        "j8-4": (57, 6),
        "j9-1": (40, 4),
        "j10-1": (13, 4),
        "j10-2": (41, 4),
        "j11-1": (14, 4),
        "j11-2": (15, 4),
        "j11-3": (42, 4),
        "j11-4": (51, 4),
        "j11-5": (54, 4),
        "j11-6": (55, 4),
        "jm-01": (66, 4),
        "jm-02": (67, 6),
        "jm-03": (68, 6),
        "jm-04": (69, 6),
        "jm-05": (70, 6),
        "od6g-01": (60, 6),
        "od4g-02": (61, 4),
        "bc-05": (71, 4),
        "bc-06": (72, 4),
        "bc-07": (73, 6),
        "bc-08": (74, 6),
        "tm4g-02": (75, 4),
        "tm4g-03": (76, 4),
        "tm6g-03": (77, 6),
        "tm6g-04": (78, 6),
        "tm6g-05": (79, 6),
        "tm6g-06": (80, 6),
        "tm6g-07": (81, 6),
    }
    # Series software images per revision
    _rev_software = dict.fromkeys(
        [None, "5"], "rvswt101_nrf52810_pca10040_v1.6.1-0-g459fa86.hex"
    )
    _rev_software.update(dict.fromkeys(["4", "3"], "rvswt101_series_1.5.hex"))
    # Software images
    _software = {  # Rev 2 'gp' units, Rev 3/4 'j' units
        "4gp1": "rvswt101_4gp1_1.2.hex",
        "6gp1": "rvswt101_6gp1_1.2.hex",
        "6gp2": "rvswt101_6gp2_1.2.hex",
        "series": _rev_software,
    }
    # Common Test limits
    _common_limits = (
        tester.LimitRegExp("BleMac", "^[0-9a-f]{12}$", doc="Valid MAC address"),
        tester.LimitBoolean("ScanMac", True, doc="MAC address detected"),
    )
    # Initial Test limits
    _initial_limits = (tester.LimitDelta("Vin", 3.3, 0.3, doc="Injected power"),)
    # Final Test limits
    _final_limits = (
        tester.LimitBoolean("ButtonOk", True, doc="Ok entered"),
        tester.LimitDelta("CellVoltage", 3.3, 0.3, doc="Button cell charged"),
        tester.LimitRegExp("Reply", "^OK$"),
        tester.LimitHigh("RSSI Level", -55, doc="Bluetooth RSSI Level"),
    )

    """
    Add expected results for 6 and 4 button models.
    The switch code within the payload for buttons 1-6 is:
    128, 64, 32, 16, 8, 4

    Button testing order each model:
    6 button   4 button   switch code
    1-2        ---        4-3
    3-4        1-2        5-2
    4-6        3-4        6-1
    """
    _limits_4_button = (
        tester.LimitInteger(
            "switch_1_pressed", 8, doc="Expected switch code for button 1"
        ),
        tester.LimitInteger(
            "switch_2_pressed", 64, doc="Expected switch code for button 2"
        ),
        tester.LimitInteger(
            "switch_3_pressed", 4, doc="Expected switch code for button 3"
        ),
        tester.LimitInteger(
            "switch_4_pressed", 128, doc="Expected switch code for button 4"
        ),
        tester.LimitInteger(
            "switch_5_pressed", -1, doc="Expected switch code for button 5"
        ),
        tester.LimitInteger(
            "switch_6_pressed", -1, doc="Expected switch code for button 6"
        ),
    )

    _limits_6_button = (
        tester.LimitInteger(
            "switch_1_pressed", 16, doc="Expected switch code for button 1"
        ),
        tester.LimitInteger(
            "switch_2_pressed", 32, doc="Expected switch code for button 2"
        ),
        tester.LimitInteger(
            "switch_3_pressed", 8, doc="Expected switch code for button 3"
        ),
        tester.LimitInteger(
            "switch_4_pressed", 64, doc="Expected switch code for button 4"
        ),
        tester.LimitInteger(
            "switch_5_pressed", 4, doc="Expected switch code for button 5"
        ),
        tester.LimitInteger(
            "switch_6_pressed", 128, doc="Expected switch code for button 6"
        ),
    )

    @classmethod
    def get(cls, parameter, uut):

        """Get configuration.

        @param parameter String to select the switch type
        @param uut libtester.UUT instance
        @return Dictionary of configuration data

        """
        rev = uut.revision
        if parameter == "series":  # Initial builds of Rev 3
            type_lim = tester.LimitBetween("SwitchType", 1, 42, doc="Switch type code")
        else:  # Later builds of Rev 3+
            switch_type, button_count = cls._types[parameter]
            type_lim = tester.LimitInteger(
                "SwitchType", switch_type, doc="Switch type code"
            )
        if parameter in cls._software:  # Rev 2 hard coded switch types
            image = cls._software[parameter]
            banner_lines = 1
        else:  # Rev 3+ auto-coded switch types
            image = cls._software["series"][rev]
            banner_lines = 2
        fixture_num = "033030"  # RVSWT101 Final Fixture
        return {
            "software": image,
            "limits_ini": cls._common_limits + cls._initial_limits,
            "limits_fin": (cls._common_limits + cls._final_limits + (type_lim,)),
            "limits_fin_4_button": (
                cls._common_limits
                + cls._final_limits
                + cls._limits_4_button
                + (type_lim,)
            ),
            "limits_fin_6_button": (
                cls._common_limits
                + cls._final_limits
                + cls._limits_6_button
                + (type_lim,)
            ),
            "banner_lines": banner_lines,
            "fixture_num": fixture_num,
            "button_count": button_count,
        }
