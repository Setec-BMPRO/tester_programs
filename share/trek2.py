#!/usr/bin/env python3
"""Trek2 ARM processor console driver."""

import share.arm_gen1


# Expose arm_gen1.Sensor as trek2.Sensor
Sensor = share.arm_gen1.Sensor

# Some easier to use short names
ArmConsoleGen1 = share.arm_gen1.ArmConsoleGen1
ParameterBoolean = share.arm_gen1.ParameterBoolean
ParameterFloat = share.arm_gen1.ParameterFloat
ParameterHex = share.arm_gen1.ParameterHex
ParameterCAN = share.arm_gen1.ParameterCAN

# Test mode controlled by STATUS bit 31
_TEST_ON = (1 << 31)
_TEST_OFF = ~_TEST_ON & 0xFFFFFFFF
# CAN Test mode controlled by STATUS bit 29
_CAN_ON = (1 << 29)
_CAN_OFF = ~_TEST_ON & 0xFFFFFFFF


class Console(ArmConsoleGen1):

    """Communications to Trek2 console."""

    def __init__(self, simulation=False, **kwargs):
        """Create console instance."""
        super().__init__(dialect=1, simulation=simulation, **kwargs)
        self.cmd_data = {
            'BACKLIGHT': ParameterFloat('BACKLIGHT', writeable=True,
                minimum=0, maximum=100, scale=1),
            'STATUS': ParameterHex('STATUS', writeable=True,
                minimum=0, maximum=0xF0000000),
            'CAN_BIND': ParameterHex('STATUS', writeable=True,
                minimum=0, maximum=0xF0000000, mask=(1 << 28)),
            'CAN_ID': ParameterCAN('TQQ,16,0'),
#            'SwVer': ParameterString(),
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
