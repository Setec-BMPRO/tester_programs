#!/usr/bin/env python3
"""BP35 ARM processor console driver."""

import share.arm_gen1


# Expose arm_gen1.Sensor as bp35.Sensor
Sensor = share.arm_gen1.Sensor


class Console(share.arm_gen1.ArmConsoleGen1):

    """Communications to ARM console."""

    def __init__(self, simulation=False, **kwargs):
        """Create console instance."""
        super().__init__(dialect=1, simulation=simulation, **kwargs)
        self._read_cmd = None
        # Data readings: Name -> (function, parameter)
        self.cmd_data = {
            'CAN_ID': (self.can_id, None),
            }

    def defaults(self, hwver, sernum):
        """Write factory defaults into NV memory.

        @param hwver Tuple (Major [1-255], Minor [1-255], Mod [character]).
        @param sernum Serial number string.

        """
        self._logger.debug('Write factory defaults')
        self.unlock()
        self.action('{0[0]} {0[1]} "{0[2]} SET-HW-VER'.format(hwver))
        self.action('"{} SET-SERIAL-ID'.format(sernum))
        super().defaults()

    def sleepmode(self, state):
        """Enable or disable Test Mode"""
        self._logger.debug('Test Mode = %s', state)
        value = 3 if state else 0
        cmd = '{} "SLEEPMODE XN!'.format(value)
        self.action(cmd)

    def fanspeed(self, value):
        """Set the fan speed"""
        cmd = '{} "FAN_SPEED XN!'.format(value)
        self.action(cmd)

    def can_id(self, dummy):
        """Simple CAN check by sending an ID request to the Trek2.

        @param dummy Unused parameter.
        @return The response string from the target device.

        """
        try:
            reply = self.action('"TQQ,32,0 CAN', expected=2)[1]
        except share.arm_gen1.ArmError:
            reply = ''
        return reply
