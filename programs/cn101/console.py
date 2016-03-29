#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CN101 Console driver."""

from ..share import console

Sensor = console.Sensor

# Some easier to use short names
ParameterBoolean = console.ParameterBoolean
ParameterFloat = console.ParameterFloat
ParameterHex = console.ParameterHex
ParameterCAN = console.ParameterCAN
ParameterRaw = console.ParameterRaw

# Test mode controlled by STATUS bit 31
_TEST_ON = (1 << 31)
_TEST_OFF = ~_TEST_ON & 0xFFFFFFFF
# CAN Test mode controlled by STATUS bit 29
_CAN_ON = (1 << 29)
_CAN_OFF = ~_CAN_ON & 0xFFFFFFFF
# Bluetooth ready controlled by STATUS bit 27
_BLE_ON = (1 << 27)
_BLE_OFF = ~_BLE_ON & 0xFFFFFFFF


class Console(console.ConsoleGen1):

    """Communications to CN101 console."""

    def __init__(self, port):
        """Create console instance."""
        super().__init__(port)
        self.cmd_data = {
            'STATUS': ParameterHex('STATUS', writeable=True,
                minimum=0, maximum=0xF0000000),
            'CAN_BIND': ParameterHex('STATUS', writeable=True,
                minimum=0, maximum=0xF0000000, mask=(1 << 28)),
            'CAN_ID': ParameterCAN('TQQ,36,0'),
            'SwVer': ParameterRaw('', func=self.version),
            'BtMac': ParameterRaw('', func=self.mac),
            'TANK1': ParameterFloat('TANK_1_LEVEL'),
            'TANK2': ParameterFloat('TANK_2_LEVEL'),
            'TANK3': ParameterFloat('TANK_3_LEVEL'),
            'TANK4': ParameterFloat('TANK_4_LEVEL'),
            }

    def testmode(self, state):
        """Enable or disable Test Mode."""
        self._logger.debug('Test Mode = %s', state)
        reply = self['STATUS']
        if state:
            value = _TEST_ON | reply
        else:
            value = _TEST_OFF & reply
        self['STATUS'] = value

    def can_mode(self, state):
        """Enable or disable CAN Communications Mode."""
        self._logger.debug('CAN Mode Enabled> %s', state)
        self.action('"RF,ALL CAN')
        reply = self['STATUS']
        if state:
            value = _CAN_ON | reply
        else:
            value = _CAN_OFF & reply
        self['STATUS'] = value

    def mac(self, param=None):
        """Read the Bluetooth MAC adderess.

        @return MAC address

        """
        mac = self.action('BLE-MAC?', expected=1).strip()
        parts = []
        for i in range(0, 12, 2):
            parts.append(mac[i:i+2])
        mac = ':'.join(parts)
        self._logger.debug('MAC address is %s', mac)
        return mac
