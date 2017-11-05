#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RVVIEW ARM processor console driver."""

import share

# Some easier to use short names
ParameterString = share.console.ParameterString
ParameterBoolean = share.console.ParameterBoolean
ParameterHex = share.console.ParameterHex


class _Console():

    """Base class for a RVVIEW console."""

    # Test mode controlled by STATUS bit 31
    _test_on = (1 << 31)
    _test_off = ~_test_on & 0xFFFFFFFF
    # CAN Test mode controlled by STATUS bit 29
    _can_on = (1 << 29)
    _can_off = ~_can_on & 0xFFFFFFFF
    # "CAN Bound" is STATUS bit 28
    _can_bound = (1 << 28)

    cmd_data = {
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
        'STATUS': ParameterHex(
            'STATUS', writeable=True, minimum=0, maximum=0xF0000000),
        'CAN_BIND': ParameterHex(
            'STATUS', writeable=True,
            minimum=0, maximum=0xF0000000, mask=_can_bound),
        'CAN': ParameterString(
            'CAN', writeable=True, write_format='"{0} {1}'),
        'CAN_STATS': ParameterHex('CANSTATS', read_format='{0}?'),
        }

    def brand(self, hw_ver, sernum, reset_relay):
        """Brand the unit with Hardware ID & Serial Number."""
        reset_relay.pulse(0.1)
        self.action(None, delay=2.0, expected=2)  # Flush banner
        self['HW_VER'] = hw_ver
        self['SER_ID'] = sernum
        self['NVDEFAULT'] = True
        self['NVWRITE'] = True
        # Restart required because of HW_VER setting
        reset_relay.pulse(0.1)
        self.action(None, delay=2.0, expected=2)  # Flush banner

    def testmode(self, state):
        """Enable or disable Test Mode.

        In test mode, pushing the button will turn on all display segments
        and the backlight. Pushing the button again turns them all off.

        """
        self._logger.debug('Test Mode = %s', state)
        reply = round(self['STATUS'])
        value = self._test_on | reply if state else self._test_off & reply
        self['STATUS'] = value

    def can_testmode(self, state):
        """Enable or disable CAN Test Mode.

        Once test mode is active, all CAN packets received will display onto
        the console. This means that the Command-Response protocol cannot
        be used any more as it breaks with the extra asynchronous messages.

        """
        self._logger.debug('CAN Mode Enabled> %s', state)
        self.action('"RF,ALL CAN')
        reply = round(self['STATUS'])
        value = self._can_on | reply if state else self._can_off & reply
        self['STATUS'] = value


class DirectConsole(_Console, share.console.BadUart):

    """Console for a direct connection to a RVVIEW."""


class TunnelConsole(_Console, share.console.Base):

    """Console for a CAN tunneled connection to a RVVIEW.

    The CAN tunnel does not need the BadUartConsole stuff.

    """
