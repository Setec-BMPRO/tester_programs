#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CN101 Console driver."""

import share


# Some easier to use short names
Sensor = share.Sensor
ParameterString = share.ParameterString
ParameterBoolean = share.ParameterBoolean
ParameterFloat = share.ParameterFloat
ParameterHex = share.ParameterHex


class _Console():

    """Base class for a CN101 console."""

    # Test mode controlled by STATUS bit 31
    _test_on = (1 << 31)
    _test_off = ~_test_on & 0xFFFFFFFF
    # CAN Test mode controlled by STATUS bit 29
    _can_on = (1 << 29)
    _can_off = ~_can_on & 0xFFFFFFFF
    # Bluetooth ready controlled by STATUS bit 27
    _ble_on = (1 << 27)
    _ble_off = ~_ble_on & 0xFFFFFFFF

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

    def testmode(self, state):
        """Enable or disable Test Mode."""
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


class DirectConsole(_Console, share.BadUartConsole):

    """Console for a direct connection to a CN101."""


class TunnelConsole(_Console, share.BaseConsole):

    """Console for a CAN tunneled connection to a CN101.

    The CAN tunnel does not need the BadUartConsole stuff.

    """
