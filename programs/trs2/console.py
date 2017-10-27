#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS2 Console driver."""

import share

# Some easier to use short names
Sensor = share.Sensor
ParameterCalibration = share.ParameterCalibration
ParameterHex = share.ParameterHex
ParameterOverride = share.ParameterOverride


class Console(share.SamB11Console):

    """Communications to TRS2 console."""

    cmd_data = {
        # X-Register values
        'VBATT': ParameterHex('TRS2_BATT_MV', scale=1000),
        'VBRAKE': ParameterHex('TRS2_BRAKE_MV', scale=1000),
        'IBRAKE': ParameterHex('TRS2_BRAKE_MA', scale=1000),
        'VPIN': ParameterHex('TRS2_DROP_ACROSS_PIN_MV', scale=1000),
        'FAULT_CODE': ParameterHex(
            'TRS2_FAULT_CODE_BITS', minimum=0, maximum=0x3),
        # Calibration commands
        'VBRAKE_OFFSET': ParameterCalibration(
            'BRAKEV_OFF_SET', write_expected=2),
        'VBRAKE_GAIN': ParameterCalibration(
            'BRAKEV_GAIN_SET', write_expected=2),
        # Override commands
        'BR_LIGHT': ParameterOverride('TRS2_BRAKE_LIGHT_EN_OVERRIDE'),
        'MONITOR': ParameterOverride('TRS2_MONITOR_EN_OVERRIDE'),
        'RED_LED': ParameterOverride('TRS2_RED_LED_OVERRIDE'),
        'GREEN_LED': ParameterOverride('TRS2_GREEN_LED_OVERRIDE'),
        'BLUE_LED': ParameterOverride('TRS2_BLUE_LED_OVERRIDE'),
        'BLUETOOTH': ParameterOverride('TRS2_BLUETOOTH_EN_OVERRIDE'),
        }
    override_commands = (
        'BR_LIGHT', 'MONITOR', 'RED_LED', 'GREEN_LED', 'BLUE_LED')
