#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SamB11 device Base console driver."""

import enum
from . import _base
from . import protocol


@enum.unique
class Override(enum.IntEnum):

    """Console manual override constants."""

    normal = 0
    force_off = 1
    force_on = 2


class ParameterOverride(_base.ParameterFloat):

    """A parameter for overriding unit operation."""

    def __init__(self, command):
        super().__init__(
            command,
            writeable=True,
            minimum=min(Override),
            maximum=max(Override)
            )


class SamB11(protocol.Base):

    """Communications to SamB11 based console."""

    # Number of lines in startup banner
    banner_lines = 3
    # Common commands
    common_commands = {
        'NVDEFAULT': _base.ParameterBoolean(
            'NV-DEFAULT', writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': _base.ParameterBoolean(
            'NV-WRITE', writeable=True, readable=False, write_format='{1}'),
        'SER_ID': _base.ParameterString(
            'SET-SERIAL-ID', writeable=True, readable=False,
            write_format='"{0} {1}'),
        'HW_VER': _base.ParameterString(
            'SET-HW-VER', writeable=True, readable=False,
            write_format='{0[0]} {0[1]} "{0[2]} {1}'),
        'SW_VER': _base.ParameterString('SW-VERSION', read_format='{0}?'),
        'BT_MAC': _base.ParameterString('BLE-MAC', read_format='{0}?'),
        }

    def __init__(self, port):
        """Add common commands into cmd_data.

        @param port Serial instance to use

        """
        super().__init__(port)
        for cmd in self.common_commands:
            self.cmd_data[cmd] = self.common_commands[cmd]

    def brand(self, hw_ver, sernum):
        """Brand the unit with Hardware ID & Serial Number."""
        self.action(None, expected=self.banner_lines)
        self['HW_VER'] = hw_ver
        self['SER_ID'] = sernum
        self['NVDEFAULT'] = True
        self['NVWRITE'] = True

    def override(self, state=Override.normal):
        """Manually override functions of the unit.

        @param state Override enumeration

        """
        for func in self.override_commands:
            self[func] = state
