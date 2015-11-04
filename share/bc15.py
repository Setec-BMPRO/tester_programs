#!/usr/bin/env python3
"""BC15 ARM processor console driver."""

import share.arm_gen1


# Expose arm_gen1.Sensor as bc15.Sensor
Sensor = share.arm_gen1.Sensor

# Some easier to use short names
ArmConsoleGen1 = share.arm_gen1.ArmConsoleGen1
ParameterBoolean = share.arm_gen1.ParameterBoolean
ParameterFloat = share.arm_gen1.ParameterFloat
ParameterHex = share.arm_gen1.ParameterHex
ParameterRaw = share.arm_gen1.ParameterRaw

# Test mode controlled by STATUS bit 31
_TEST_ON = (1 << 31)
_TEST_OFF = ~_TEST_ON & 0xFFFFFFFF


class Console(ArmConsoleGen1):

    """Communications to BC15 console."""

    def __init__(self, simulation=False, **kwargs):
        """Create console instance."""
        super().__init__(dialect=1, simulation=simulation, **kwargs)
        self.cmd_data = {
            'STATUS': ParameterHex('STATUS', writeable=True,
                minimum=0, maximum=0xF0000000),
            'SwVer': ParameterRaw('', func=self.version),
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
