#!/usr/bin/env python3
"""Trek2 ARM processor console driver."""

import share.arm_gen1


# Expose arm_gen1.Sensor as trek2.Sensor
Sensor = share.arm_gen1.Sensor


class Console(share.arm_gen1.ArmConsoleGen1):

    """Communications to ARM console."""

    def __init__(self):
        """Create console instance."""
        super().__init__(dialect=1)
        self._read_cmd = None
        # Data readings: Name -> (function, parameter)
        self.cmd_data = {
            'CAN_ID': (self.can_id, None),
            }

    def can_id(self, dummy):
        """Simple CAN check by sending a ID request.

        @param dummy Unused parameter.
        @return The response string from the target device.

        """
        try:
            reply = self.action('"TQQ,16,0 CAN', expected=2)[1]
        except share.arm_gen1.ArmError:
            reply = ''
        return reply

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

    def testmode(self, state):
        """Enable or disable Test Mode"""
        self._logger.debug('Test Mode Enabled> %s', state)
        reply = int(self.action('"STATUS XN?', expected=1), 16) # Reply is hex
        if state:
            value = 0x80000000 | reply
        else:
            value = 0x7FFFFFFF & reply
        cmd = '${:08X} "STATUS XN!'.format(value)
        self._logger.debug('%s', cmd)
        self.action(cmd)

    def bklght(self, param=100):
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
        self._logger.debug('%s', cmd)
        self.action(cmd)
