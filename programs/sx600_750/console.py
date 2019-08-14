#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 - 2019 SETEC Pty Ltd
"""SX-600/750 console driver."""

import share


class _Console(share.console.Base):

    """Communications to SX-600/750 console."""

    # Number of lines in startup banner
    banner_lines = 4
    parameter = share.console.parameter
    # Common commands
    common_commands = {
        'ARM-AcFreq': parameter.Float(
            'X-AC-LINE-FREQUENCY', read_format='{0} X?'),
        'ARM-AcVolt': parameter.Float(
            'X-AC-LINE-VOLTS', read_format='{0} X?'),
        'ARM-12V': parameter.Float(
            'X-RAIL-VOLTAGE-12V', scale=1000, read_format='{0} X?'),
        'ARM-24V': parameter.Float(
            'X-RAIL-VOLTAGE-24V', scale=1000, read_format='{0} X?'),
        'ARM_SwVer': parameter.String(
            'X-SOFTWARE-VERSION', read_format='{0} X?'),
        'ARM_SwBld': parameter.String(
            'X-BUILD-NUMBER', read_format='{0} X?'),
        'UNLOCK': parameter.Boolean(
            '$DEADBEA7 UNLOCK',
            writeable=True, readable=False, write_format='{1}'),
        }
    # Strings to ignore in responses
    ignore = (' ', 'Hz', 'Vrms', 'mV')

    def __init__(self, port):
        """Add common commands into cmd_data.

        @param port Serial instance to use

        """
        super().__init__(port)
        for cmd in self.common_commands:
            self.cmd_data[cmd] = self.common_commands[cmd]


class Console600(_Console):

    """Communications to SX-600 console."""

    parameter = share.console.parameter
    cmd_data = {
        'FAN_CHECK_DISABLE': parameter.Boolean(
            'X-SYSTEM-ENABLE', read_format='{1} X?',
            writeable=True, write_format='{0} {1} X!'),
        'NVDEFAULT': parameter.Boolean(
            'NV-DEFAULT',
            writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': parameter.Boolean(
            'NV-WRITE', writeable=True, readable=False, write_format='{1}'),
        }

    def open(self):
        """Open console."""
        self.port.rtscts = True
        super().open()

    def close(self):
        """Close console."""
        self.port.rtscts = False
        super().close()


class Console750(_Console):

    """Communications to SX-750 console."""

    parameter = share.console.parameter
    cmd_data = {
        'CAL_PFC': parameter.Float(
            'CAL-PFC-BUS-VOLTS',
            writeable=True, readable=False, scale=1000,
            write_format='{0} {1}'),
        'FAN_SET': parameter.Float(
            'X-TEMPERATURE-CONTROLLER-SETPOINT',
            writeable=True,
            write_format='{0} {1} X!'),
# FIXME: Why have we been seeing startup banners after the 1st NV-WRITE ?
        'NVWRITE': parameter.Boolean(
            'NV-WRITE', writeable=True, readable=False, write_format='{1}',
            write_expected=0),
        }

    def open(self):
        """Open console."""
        self.port.baudrate = 57600
        super().open()

    def close(self):
        """Close console."""
        self.port.baudrate = 115200
        super().close()

    def calpfc(self, voltage):
        """Issue PFC calibration commands."""
        self['CAL_PFC'] = voltage
        self['NVWRITE'] = True
