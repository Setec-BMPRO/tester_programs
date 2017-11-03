#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CN101 Console driver."""

import share

# Some easier to use short names
Sensor = share.console.Sensor
ParameterString = share.console.ParameterString
ParameterBoolean = share.console.ParameterBoolean
ParameterFloat = share.console.ParameterFloat
ParameterHex = share.console.ParameterHex


class _Console():

    """Base class for a CN101 console."""

    # Number of lines in startup banner
    banner_lines = 0
    cmd_data = {
        'UNLOCK': ParameterBoolean(
            '$DEADBEA7 UNLOCK',
            writeable=True, readable=False, write_format='{1}'),
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
        'STATUS': ParameterHex(
            'STATUS', writeable=True,
            minimum=0, maximum=0xF0000000),
        'CAN_BIND': ParameterHex(
            'STATUS', writeable=True,
            minimum=0, maximum=0xF0000000, mask=(1 << 28)),
        'CAN': ParameterString('CAN',
            writeable=True, write_format='"{0} {1}'),
        'TANK1': ParameterFloat('TANK_1_LEVEL'),
        'TANK2': ParameterFloat('TANK_2_LEVEL'),
        'TANK3': ParameterFloat('TANK_3_LEVEL'),
        'TANK4': ParameterFloat('TANK_4_LEVEL'),
        'ADC_SCAN': ParameterFloat('ADC_SCAN_INTERVAL_MSEC', writeable=True),
        }

    def brand(self, hw_ver, sernum, reset_relay):
        """Brand the unit with Hardware ID & Serial Number."""
        reset_relay.pulse(0.1)
        self.action(None, delay=1.5, expected=self.banner_lines)
        self['UNLOCK'] = True
        self['HW_VER'] = hw_ver
        self['SER_ID'] = sernum
        self['NVDEFAULT'] = True
        self['NVWRITE'] = True


class DirectConsole(_Console, share.console.BadUart):

    """Console for a direct connection."""


class TunnelConsole(_Console, share.console.Base):

    """Console for a CAN tunneled connection.

    The CAN tunnel does not need the BadUartConsole stuff.

    """
