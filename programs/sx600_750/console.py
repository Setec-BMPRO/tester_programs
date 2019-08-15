#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 - 2019 SETEC Pty Ltd
"""SX-600/750 console driver."""

import time

import share


class _Console(share.console.Base):

    """Communications to SX-600/750 console."""

    # Number of lines in startup banner
    banner_lines = 4
    cmd_data = {}
    # Time delay after NV-WRITE
    nvwrite_delay = 1.0
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
        'NVWRITE': parameter.Boolean(
            'NV-WRITE',
            writeable=True, readable=False, write_format='{1}'),
        }
    # Strings to ignore in responses
    ignore = (' ', 'Hz', 'Vrms', 'mV')

    def __init__(self, port):
        """Add common commands into cmd_data.

        @param port Serial instance to use

        """
        super().__init__(port)
        for acmd in self.common_commands:
            self.cmd_data[acmd] = self.common_commands[acmd]


class Console600(_Console):

    """Communications to SX-600 console."""

    parameter = share.console.parameter
    cmd_data = {
        'FAN_CHECK_DISABLE': parameter.Boolean(
            'X-SYSTEM-ENABLE',
            read_format='{1} X?',
            writeable=True, write_format='{0} {1} X!'),
        'NVDEFAULT': parameter.Boolean(
            'NV-DEFAULT',
            readable=False,
            writeable=True, write_format='{1}'),
        }

    def open(self):
        """Open console."""
        self.port.rtscts = True
        super().open()

    def close(self):
        """Close console."""
        self.port.rtscts = False
        super().close()

    def initialise(self, fan_threshold=None):
        """Initialise a device."""
        self.action(expected=self.banner_lines)
        self['UNLOCK'] = True
        self['NVDEFAULT'] = True
        self['NVWRITE'] = True
        time.sleep(self.nvwrite_delay)


class Console750(_Console):

    """Communications to SX-750 console."""

    parameter = share.console.parameter
    cmd_data = {
        'CAL_PFC': parameter.Float(
            'CAL-PFC-BUS-VOLTS',
            scale=1000,
            readable=False,
            writeable=True, write_format='{0} {1}'),
        'FAN_SET': parameter.Float(
            'X-TEMPERATURE-CONTROLLER-SETPOINT',
            writeable=True, write_format='{0} {1} X!'),
        }

    def open(self):
        """Open console."""
        self.port.baudrate = 57600
        super().open()

    def close(self):
        """Close console."""
        self.port.baudrate = 115200
        super().close()

    def initialise(self, fan_threshold):
        """Initialise a device."""
        self.action(expected=self.banner_lines)
        self['UNLOCK'] = True
        self['FAN_SET'] = fan_threshold
        self['NVWRITE'] = True
        time.sleep(self.nvwrite_delay)

    def calpfc(self, voltage):
        """Issue PFC calibration commands."""
        self['CAL_PFC'] = voltage
        self['NVWRITE'] = True
