#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2013 SETEC Pty Ltd
"""SX-600 console driver."""

import time

import share


class Console(share.console.Base):

    """Communications to console."""

    banner_lines = 4        # Number of lines in startup banner
    nvwrite_delay = 1.0     # Time delay after NV-WRITE
    parameter = share.console.parameter
    cmd_data = {
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
        'FAN_CHECK_DISABLE': parameter.Boolean(
            'X-SYSTEM-ENABLE',
            read_format='{1} X?',
            writeable=True, write_format='{0} {1} X!'),
        'NVDEFAULT': parameter.Boolean(
            'NV-DEFAULT',
            readable=False,
            writeable=True, write_format='{1}'),
        }
    # Strings to ignore in responses
    ignore = (' ', 'Hz', 'Vrms', 'mV')

    def open(self):
        """Open console."""
        self.port.rtscts = True
        super().open()

    def close(self):
        """Close console."""
        self.port.rtscts = False
        super().close()

    def initialise(self):
        """Initialise a device."""
        self.action(expected=self.banner_lines)
        self['UNLOCK'] = True
        self['NVDEFAULT'] = True
        self['NVWRITE'] = True
        time.sleep(self.nvwrite_delay)