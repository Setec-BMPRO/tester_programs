#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RVVIEW ARM processor console driver."""

from share import console

Sensor = console.Sensor

# Some easier to use short names
ParameterString = console.ParameterString
ParameterBoolean = console.ParameterBoolean
ParameterFloat = console.ParameterFloat
ParameterHex = console.ParameterHex

# "Test" mode controlled by STATUS bit 31
_TEST_ON = (1 << 31)
_TEST_OFF = ~_TEST_ON & 0xFFFFFFFF
# "CAN Print Packets" mode controlled by STATUS bit 29
_CAN_ON = (1 << 29)
_CAN_OFF = ~_CAN_ON & 0xFFFFFFFF
# "CAN Bound" is STATUS bit 28
_CAN_BOUND = (1 << 28)


class _Console():

    """Base class for a RVVIEW console."""

    def __init__(self):
        """Create console instance."""
        self.cmd_data = {
            'NVDEFAULT': ParameterBoolean('NV-DEFAULT',
                writeable=True, readable=False, write_format='{1}'),
            'NVWRITE': ParameterBoolean('NV-WRITE',
                writeable=True, readable=False, write_format='{1}'),
            'SER_ID': ParameterString(
                'SET-SERIAL-ID', writeable=True, readable=False,
                write_format='"{} {}'),
            'HW_VER': ParameterString(
                'SET-HW-VER', writeable=True, readable=False,
                write_format='{0[0]} {0[1]} "{0[2]} {1}'),
            'SW_VER': ParameterString('SW-VERSION', read_format='{}?'),
            'STATUS': ParameterHex(
                'STATUS', writeable=True, minimum=0, maximum=0xF0000000),
            'CAN_BIND': ParameterHex(
                'STATUS', writeable=True,
                minimum=0, maximum=0xF0000000, mask=_CAN_BOUND),
            'CAN': ParameterString(
                'CAN', writeable=True, write_format='"{} {}'),
            'CAN_STATS': ParameterHex('CANSTATS', read_format='{}?'),
            }

    def brand(self, hw_ver, sernum, reset_relay):
        """Brand the unit with Hardware ID & Serial Number."""
        reset_relay.pulse(0.1)
        self.action(None, delay=1.5, expected=2)  # Flush banner
        self['HW_VER'] = hw_ver
        self['SER_ID'] = sernum
        self['NVDEFAULT'] = True
        self['NVWRITE'] = True
        # Restart required because of HW_VER setting
        reset_relay.pulse(0.1)
        self.action(None, delay=1.5, expected=2)  # Flush banner

    def testmode(self, state):
        """Enable or disable Test Mode.

        In test mode, pushing the button will turn on all display segments
        and the backlight. Pushing the button again turns them all off.

        """
        self._logger.debug('Test Mode = %s', state)
        reply = self['STATUS']
        if state:
            value = _TEST_ON | reply
        else:
            value = _TEST_OFF & reply
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
            value = _CAN_ON | reply
        else:
            value = _CAN_OFF & reply
        self['STATUS'] = value


class DirectConsole(console.Variable, _Console, console.BadUartConsole):

    """Console for a direct connection to a RVVIEW."""

    def __init__(self, port, verbose=False):
        """Create console instance."""
        # Call __init__() methods directly, since we cannot use super() as
        # the arguments don't match
        console.Variable.__init__(self)
        _Console.__init__(self)
        console.BadUartConsole.__init__(self, port, verbose)


class TunnelConsole(console.Variable, _Console, console.BaseConsole):

    """Console for a CAN tunneled connection to a RVVIEW.

    The CAN tunnel does not need the BadUartConsole stuff.

    """

    def __init__(self, port, verbose=False):
        """Create console instance."""
        # Call __init__() methods directly, since we cannot use super() as
        # the arguments don't match
        console.Variable.__init__(self)
        _Console.__init__(self)
        console.BaseConsole.__init__(self, port, verbose)
