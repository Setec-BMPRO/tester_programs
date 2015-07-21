#!/usr/bin/env python3
"""Trek2 ARM processor console driver."""

import share.arm_gen1


# Expose arm_gen1.Sensor as trek2.Sensor
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

    def testmode(self, state):
        """Enable or disable Test Mode"""
        self._logger.debug('Test Mode = %s', state)
        reply = int(self.action('"STATUS XN?', expected=1), 16) # Reply is hex
        if state:
            value = 0x80000000 | reply
        else:
            value = 0x7FFFFFFF & reply
        cmd = '${:08X} "STATUS XN!'.format(value)
        self.action(cmd)

    def backlight(self, param=100):
        """Set backlight intensity."""
        self.action('{} 0 X!'.format(param))

    def can_mode(self, state):
        """Enable or disable CAN Communications Mode"""
        self._logger.debug('CAN Mode Enabled> %s', state)
        self.action('"RF,ALL CAN')
        reply = int(self.action('"STATUS XN?', expected=1), 16) # Reply is hex
        if state:
            value = 0x20000000 | reply
        else:
            value = 0xDFFFFFFF & reply
        cmd = '${:08X} "STATUS XN!'.format(value)
        self.action(cmd)

    def can_id(self, dummy):
        """Simple CAN check.

        Done by sending an ID request to the Trek2 in the fixture.
        (It is setup to have the ID of a BP35 - 16)

        @param dummy Unused parameter.
        @return The response string from the target device.

        """
        try:
            reply = self.action('"TQQ,16,0 CAN', expected=2)[1]
        except share.arm_gen1.ArmError:
            reply = ''
        return reply
