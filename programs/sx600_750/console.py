#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 - 2019 SETEC Pty Ltd
"""SX-600/750 console driver."""

import share


class Console(share.console.Base):

    """Communications to SX-600/750 console."""

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
        'FAN_SET': parameter.Float(         # SX-750 only
            'X-TEMPERATURE-CONTROLLER-SETPOINT',
            writeable=True,
            write_format='{0} {1} X!'),
        'FAN_CHECK_DISABLE': parameter.Boolean( # SX-600 only
            'X-SYSTEM-ENABLE', read_format='{1} X?',
            writeable=True, write_format='{0} {1} X!'),
        'CAL_PFC': parameter.Float(
            'CAL-PFC-BUS-VOLTS',
            writeable=True, readable=False, scale=1000,
            write_format='{0} {1}'),
        'UNLOCK': parameter.Boolean(
            '$DEADBEA7 UNLOCK',
            writeable=True, readable=False, write_format='{1}'),
        'NVDEFAULT': parameter.Boolean(     # SX-600 only
            'NV-DEFAULT',
            writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': parameter.Boolean(
            'NV-WRITE', writeable=True, readable=False, write_format='{1}'),
        }
    # Strings to ignore in responses
    ignore = (' ', 'Hz', 'Vrms', 'mV')

    def calpfc(self, voltage):
        """Issue PFC calibration commands."""
        self['CAL_PFC'] = voltage
        self['NVWRITE'] = True
