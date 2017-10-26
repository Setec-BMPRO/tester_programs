#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRSRFM Console driver."""

import enum
import share

Sensor = share.console.Sensor
# Some easier to use short names
ParameterString = share.console.ParameterString
ParameterBoolean = share.console.ParameterBoolean
ParameterFloat = share.console.ParameterFloat
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

    """Communications to TRSRFM console."""

    # Number of lines in startup banner
    banner_lines = 2
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
        'SW_VER': ParameterString(
            'SW-VERSION', read_format='{0}?'),
        'BT_MAC': ParameterString(
            'BLE-MAC', read_format='{0}?'),
        # X-Register values
        'FAULT_CODE': ParameterHex(
            'TRSRFM_FAULT_CODE_BITS', minimum=0, maximum=0x3),
        # Override commands
        'RED_LED': ParameterOverride('TRSRFM_RED_LED_OVERRIDE'),
        'GREEN_LED': ParameterOverride('TRSRFM_GREEN_LED_OVERRIDE'),
        'BLUE_LED': ParameterOverride('TRSRFM_BLUE_LED_OVERRIDE'),
        'BLUETOOTH': ParameterOverride('TRSRFM_BLUETOOTH_EN_OVERRIDE'),
        }

    def brand(self, hw_ver, sernum):
        """Brand the unit with Hardware ID & Serial Number."""
        self.action(None, delay=5.0, expected=self.banner_lines)
        self['HW_VER'] = hw_ver
        self['SER_ID'] = sernum
        self['NVDEFAULT'] = True
        self['NVWRITE'] = True

    def override(self, state=Override.normal):
        """Manually override functions of the unit.

        @param state Override enumeration

        """
        for func in ('RED_LED', 'GREEN_LED', 'BLUE_LED'):
            self[func] = state
