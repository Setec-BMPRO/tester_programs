#!/usr/bin/env python3
"""CN101 ARM processor console driver."""

import share.arm_gen1


# Expose arm_gen1.Sensor as cn101.Sensor
Sensor = share.arm_gen1.Sensor

# Some easier to use short names
ArmConsoleGen1 = share.arm_gen1.ArmConsoleGen1
ParameterBoolean = share.arm_gen1.ParameterBoolean
ParameterFloat = share.arm_gen1.ParameterFloat
ParameterHex = share.arm_gen1.ParameterHex
ParameterCAN = share.arm_gen1.ParameterCAN
ParameterRaw = share.arm_gen1.ParameterRaw

# Test mode controlled by STATUS bit 31
_TEST_ON = (1 << 31)
_TEST_OFF = ~_TEST_ON & 0xFFFFFFFF
# CAN Test mode controlled by STATUS bit 29
_CAN_ON = (1 << 29)
_CAN_OFF = ~_CAN_ON & 0xFFFFFFFF


class Console(ArmConsoleGen1):

    """Communications to CN101 console."""

    def __init__(self, simulation=False, **kwargs):
        """Create console instance."""
        super().__init__(dialect=1, simulation=simulation, **kwargs)
        self.cmd_data = {
            'STATUS': ParameterHex('STATUS', writeable=True,
                minimum=0, maximum=0xF0000000),
            'CAN_BIND': ParameterHex('STATUS', writeable=True,
                minimum=0, maximum=0xF0000000, mask=(1 << 28)),
            'CAN_ID': ParameterCAN('TQQ,16,0'),
            'SwVer': ParameterRaw('', func=self.version),
            'BtMac': ParameterRaw('', func=self.mac),
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
        mac = self.action('BT-MAC?', expected=1).strip()
        parts = []
        for i in range(0, 12, 2):
            parts.append(mac[i:i+2])
        mac = ':'.join(parts)
        self._logger.debug('MAC address is %s', mac)
        return mac