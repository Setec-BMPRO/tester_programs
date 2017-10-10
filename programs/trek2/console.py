#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 ARM processor console driver."""

from share import console

# Some easier to use short names
Sensor = console.Sensor
ParameterString = console.ParameterString
ParameterBoolean = console.ParameterBoolean
ParameterFloat = console.ParameterFloat
ParameterHex = console.ParameterHex


class _Console():

    """Base class for a Trek2 console."""

    # Test mode controlled by STATUS bit 31
    _test_on = (1 << 31)
    _test_off = ~_test_on & 0xFFFFFFFF
    # CAN Test mode controlled by STATUS bit 29
    _can_on = (1 << 29)
    _can_off = ~_can_on & 0xFFFFFFFF
    # "CAN Bound" is STATUS bit 28
    _can_bound = (1 << 28)

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
        'PROMPT': ParameterString(
            'PROMPT', writeable=True, write_format='"{0} {1}'),
        'STATUS': ParameterHex(
            'STATUS', writeable=True, minimum=0, maximum=0xF0000000),
        'CAN_BIND': ParameterHex(
            'STATUS', writeable=True,
            minimum=0, maximum=0xF0000000, mask=_can_bound),
        'CAN': ParameterString(
            'CAN', writeable=True, write_format='"{0} {1}'),
        'CAN_STATS': ParameterHex('CANSTATS', read_format='{0}?'),
        'BACKLIGHT': ParameterFloat(
            'BACKLIGHT_INTENSITY', writeable=True,
            minimum=0, maximum=100, scale=1),
        'CONFIG': ParameterHex(
            'CONFIG', writeable=True, minimum=0, maximum=0xFFFF),
        'TANK_SPEED': ParameterFloat(
            'ADC_SCAN_INTERVAL_MSEC', writeable=True,
            minimum=0, maximum=10, scale=1000),
        'TANK1': ParameterFloat('TANK_1_LEVEL'),
        'TANK2': ParameterFloat('TANK_2_LEVEL'),
        'TANK3': ParameterFloat('TANK_3_LEVEL'),
        'TANK4': ParameterFloat('TANK_4_LEVEL'),
        }

    def testmode(self, state):
        """Enable or disable Test Mode.

        In test mode, all the display segments are on, and the backlight
        will blink when any button is pressed.

        """
        self._logger.debug('Test Mode = %s', state)
        reply = self['STATUS']
        if state:
            value = self._test_on | reply
        else:
            value = self._test_off & reply
        self['STATUS'] = value

    def can_testmode(self, state):
        """Enable or disable CAN Test Mode.

        Once test mode is active, all CAN packets received will display onto
        the console. This means that the Command-Response protocol cannot
        be used any more as it breaks with the extra asynchronous messages.

        """
        self._logger.debug('CAN Mode Enabled> %s', state)
        self.action('"RF,ALL CAN')
        reply = self['STATUS']
        if state:
            value = self._can_on | reply
        else:
            value = self._can_off & reply
        self['STATUS'] = value


class DirectConsole(_Console, console.BadUartConsole):

    """Console for a direct connection to a Trek2."""


class TunnelConsole(_Console, console.BaseConsole):

    """Console for a CAN tunneled connection to a Trek2.

    The CAN tunnel does not need the BadUartConsole stuff.

    """
