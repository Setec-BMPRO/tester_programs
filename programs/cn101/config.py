#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2015 SETEC Pty Ltd.
"""CN101 Configuration."""

import tester

import share


class CN101():

    """Configuration for CN101."""

    # Initial test limits
    limits_initial = (
            tester.LimitRegExp('SwVer', '',            # Adjusted during open()
                doc='Software version'),
            tester.LimitLow('Part', 100.0),
            tester.LimitDelta('Vin', 8.0, 0.5),
            tester.LimitPercent('3V3', 3.30, 3.0),
            tester.LimitInteger('CAN_BIND', 1 << 28),
            tester.LimitRegExp('BtMac', share.bluetooth.MAC.line_regex),
            tester.LimitBoolean('DetectBT', True),
            tester.LimitInteger('Tank', 5),
            )
    # MA-239: Upgrade all units to CN101T, so treat them as Rev 6
    sw_version = '1.2.17835.298'
    hw_version = (6, 0, 'A')
    banner_lines = 2
