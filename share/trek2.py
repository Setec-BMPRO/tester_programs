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


class Console(ArmConsoleGen1):

    """Communications to Trek2 console."""

    def __init__(self, simulation=False, **kwargs):
        """Create console instance."""
        super().__init__(dialect=1, simulation=simulation, **kwargs)
        self.cmd_data = {
            'BACKLIGHT': ParameterFloat('BACKLIGHT', writeable=True,
                minimum=0, maximum=100, scale=1),
            'STATUS': ParameterHex('STATUS', writeable=True,
                minimum=0, maximum=0xA0000000),
            'CAN_ID': ParameterCAN('TQQ,16,0'),
            }

    def testmode(self, state):
        """Enable or disable Test Mode"""
        self._logger.debug('Test Mode = %s', state)
        reply = self['STATUS']
        if state:
            value = 0x80000000 | reply
        else:
            value = 0x7FFFFFFF & reply
        self['STATUS'] = value

    def can_mode(self, state):
        """Enable or disable CAN Communications Mode"""
        self._logger.debug('CAN Mode Enabled> %s', state)
        self.action('"RF,ALL CAN')
        reply = self['STATUS']
        if state:
            value = 0x20000000 | reply
        else:
            value = 0xDFFFFFFF & reply
        self['STATUS'] = value
