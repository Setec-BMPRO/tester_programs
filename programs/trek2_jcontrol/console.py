#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2/JControl ARM processor console driver."""

import share


class _Console():

    """Base class for a Trek2/JControl console."""

    # Number of lines in startup banner
    banner_lines = 2
    # Test mode controlled by STATUS bit 31
    _test_on = (1 << 31)
    _test_off = ~_test_on & 0xFFFFFFFF
    # "CAN Bound" is STATUS bit 28
    _can_bound = (1 << 28)
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
        'PROMPT': parameter.String(
            'PROMPT', writeable=True, write_format='"{0} {1}'),
        'STATUS': parameter.Hex(
            'STATUS', writeable=True, minimum=0, maximum=0xF0000000),
        'CAN_BIND': parameter.Hex(
            'STATUS', writeable=True,
            minimum=0, maximum=0xF0000000, mask=_can_bound),
        'CAN': parameter.String(
            'CAN', writeable=True, write_format='"{0} {1}'),
        'CAN_STATS': parameter.Hex('CANSTATS', read_format='{0}?'),
        'BACKLIGHT': parameter.Float(
            'BACKLIGHT_INTENSITY', writeable=True,
            minimum=0, maximum=100, scale=1),
        'CONFIG': parameter.Hex(
            'CONFIG', writeable=True, minimum=0, maximum=0xFFFF),
        'TANK_SPEED': parameter.Float(
            'ADC_SCAN_INTERVAL_MSEC', writeable=True,
            minimum=0, maximum=10, scale=1000),
        'TANK1': parameter.Float('TANK_1_LEVEL'),
        'TANK2': parameter.Float('TANK_2_LEVEL'),
        'TANK3': parameter.Float('TANK_3_LEVEL'),
        'TANK4': parameter.Float('TANK_4_LEVEL'),
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

    def testmode(self, state):
        """Enable or disable Test Mode.

        In test mode, all the display segments are on, and the backlight
        will blink when any button is pressed.

        """
        self._logger.debug('Test Mode = %s', state)
        reply = round(self['STATUS'])
        value = self._test_on | reply if state else self._test_off & reply
        self['STATUS'] = value


class DirectConsole(_Console, share.console.BadUart):

    """Console for a direct connection to a Trek2/JControl."""


class TunnelConsole(_Console, share.console.Base):

    """Console for a CAN tunneled connection to a Trek2/JControl.

    The CAN tunnel does not need the BadUartConsole stuff.

    """