#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CN102 Console driver."""

import share


class _Console():

    """Base class for a CN102 console."""

    parameter = share.console.parameter
    cmd_data = {
        'UNLOCK': parameter.Boolean(
            '$DEADBEA7 UNLOCK',
            writeable=True, readable=False, write_format='{1}'),
        'NVDEFAULT': parameter.Boolean(
            'NV-DEFAULT', writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': parameter.Boolean(
            'NV-WRITE', writeable=True, readable=False, write_format='{1}'),
        'SER_ID': parameter.String(
            'SET-SERIAL-ID', writeable=True, readable=False,
            write_format='"{0} {1}'),
        'HW_VER': parameter.String(
            'SET-HW-VER', writeable=True, readable=False,
            write_format='{0[0]} {0[1]} "{0[2]} {1}'),
        'SW_VER': parameter.String('SW-VERSION', read_format='{0}?'),
        'STATUS': parameter.Hex(
            'STATUS', writeable=True,
            minimum=0, maximum=0xF0000000),
        'CAN_BIND': parameter.Hex(
            'STATUS', writeable=True,
            minimum=0, maximum=0xF0000000, mask=(1 << 28)),
        'CAN': parameter.String('CAN',
            writeable=True, write_format='"{0} {1}'),
        'TANK1': parameter.Float('TANK_1_LEVEL'),
        'TANK2': parameter.Float('TANK_2_LEVEL'),
        'TANK3': parameter.Float('TANK_3_LEVEL'),
        'TANK4': parameter.Float('TANK_4_LEVEL'),
        'ADC_SCAN': parameter.Float('ADC_SCAN_INTERVAL_MSEC', writeable=True),
        }

    def brand(self, hw_ver, sernum, reset_relay, banner_lines):
        """Brand the unit with Hardware ID & Serial Number."""
        reset_relay.pulse(0.1)
        self.action(None, delay=1.5, expected=banner_lines)
        self['UNLOCK'] = True
        self['HW_VER'] = hw_ver
        self['SER_ID'] = sernum
        self['NVDEFAULT'] = True
        self['NVWRITE'] = True


class DirectConsole(_Console, share.console.BadUart):

    """Console for a direct connection."""


class TunnelConsole(_Console, share.console.CANTunnel):

    """Console for a CAN tunneled connection."""