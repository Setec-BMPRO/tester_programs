#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRSRFM Console driver."""

import share

# Some easier to use short names
Sensor = share.console.Sensor
ParameterOverride = share.console.ParameterOverride


class Console(share.console.SamB11):

    """Communications to TRSRFM console."""

    cmd_data = {
        # Override commands
        'RED_LED': ParameterOverride('TRS_RFM_RED_LED_OVERRIDE'),
        'GREEN_LED': ParameterOverride('TRS_RFM_GREEN_LED_OVERRIDE'),
        'BLUE_LED': ParameterOverride('TRS_RFM_BLUE_LED_OVERRIDE'),
        }
    override_commands = ('RED_LED', 'GREEN_LED', 'BLUE_LED')
