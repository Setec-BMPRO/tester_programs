#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRSRFM Console driver."""

import share

# Some easier to use short names
Sensor = share.Sensor
ParameterHex = share.ParameterHex
ParameterOverride = share.ParameterOverride


class Console(share.SamB11Console):

    """Communications to TRSRFM console."""

    cmd_data = {
        # X-Register values
        'FAULT_CODE': ParameterHex(
            'TRSRFM_FAULT_CODE_BITS', minimum=0, maximum=0x3),
        # Override commands
        'RED_LED': ParameterOverride('TRSRFM_RED_LED_OVERRIDE'),
        'GREEN_LED': ParameterOverride('TRSRFM_GREEN_LED_OVERRIDE'),
        'BLUE_LED': ParameterOverride('TRSRFM_BLUE_LED_OVERRIDE'),
        'BLUETOOTH': ParameterOverride('TRSRFM_BLUETOOTH_EN_OVERRIDE'),
        }
    override_commands = ('RED_LED', 'GREEN_LED', 'BLUE_LED')
