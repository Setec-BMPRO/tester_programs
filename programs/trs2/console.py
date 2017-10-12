#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS2 Console driver."""

import enum
import share

# Some easier to use short names
Sensor = share.console.Sensor
ParameterString = share.console.ParameterString
ParameterBoolean = share.console.ParameterBoolean
ParameterFloat = share.console.ParameterFloat
ParameterCalibration = share.console.ParameterCalibration
ParameterHex = share.console.ParameterHex


@enum.unique
class Override(enum.IntEnum):

    """Console manual override constants."""

    normal = 0
    force_off = 1
    force_on = 2


class ParameterOverride(ParameterFloat):

    """A parameter for overriding unit operation."""

    def __init__(self, command):
        super().__init__(
            command,
            writeable=True,
            minimum=min(Override),
            maximum=max(Override)
            )


class Console(share.console.BaseConsole):

    """Communications to TRS2 console."""

    # Auto add prompt to puts strings
    puts_prompt = '\r\n> '
    # Number of lines in startup banner
    banner_lines = 3
    cmd_data = {
        # Commands
        'NVDEFAULT': ParameterBoolean(
            'NV-DEFAULT', writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': ParameterBoolean(
            'NV-WRITE', writeable=True, readable=False, write_format='{1}'),
        'SER_ID': ParameterString(
            'SET-SERIAL-ID', writeable=True, readable=False,
            write_format='"{0} {1}'),
        'HW_VER': ParameterString(
            'SET-HW-VER', writeable=True, readable=False,
            write_format='{0[0]} {0[1]} "{0[2]} {1}'),
        'SW_VER': ParameterString('SW-VERSION', read_format='{0}?'),
        'BT_MAC': ParameterString('BLE-MAC', read_format='{0}?'),
        # X-Register values
        'VBATT': ParameterHex('TRS2_BATT_MV', scale=1000),
        'VBRAKE': ParameterHex('TRS2_BRAKE_MV', scale=1000),
        'IBRAKE': ParameterHex('TRS2_BRAKE_MA', scale=1000),
        'VPIN': ParameterHex('TRS2_DROP_ACROSS_PIN_MV', scale=1000),
        'FAULT_CODE': ParameterHex(
            'TRS2_FAULT_CODE_BITS', minimum=0, maximum=0x3),
        # Calibration commands
        'VBRAKE_OFFSET': ParameterCalibration('BRAKEV_OFF_SET', write_expected=2),
        'VBRAKE_GAIN': ParameterCalibration('BRAKEV_GAIN_SET', write_expected=2),
        # Override commands
        'BR_LIGHT': ParameterOverride('TRS2_BRAKE_LIGHT_EN_OVERRIDE'),
        'MONITOR': ParameterOverride('TRS2_MONITOR_EN_OVERRIDE'),
        'RED_LED': ParameterOverride('TRS2_RED_LED_OVERRIDE'),
        'GREEN_LED': ParameterOverride('TRS2_GREEN_LED_OVERRIDE'),
        'BLUE_LED': ParameterOverride('TRS2_BLUE_LED_OVERRIDE'),
        'BLUETOOTH': ParameterOverride('TRS2_BLUETOOTH_EN_OVERRIDE'),
        }

    def brand(self, hw_ver, sernum):
        """Brand the unit with Hardware ID & Serial Number."""
        self['HW_VER'] = hw_ver
        self['SER_ID'] = sernum
        self['NVDEFAULT'] = True
        self['NVWRITE'] = True

    def override(self, state=Override.normal):
        """Manually override functions of the unit.

        @param state Override enumeration

        """
        for func in (
                'BR_LIGHT', 'MONITOR', 'RED_LED', 'GREEN_LED', 'BLUE_LED'):
            self[func] = state
