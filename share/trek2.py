#!/usr/bin/env python3
"""Trek2 ARM processor console driver."""

import share.arm_gen1


class Console(share.arm_gen1.ArmConsoleGen1):

    """Communications to ARM console."""

    def __init__(self, serport):
        """Open serial communications.

        @param serport An opened serial port instance.

        """
        super().__init__(serport, dialect=1)
        self._read_cmd = None
        # Data readings:
        #   Name -> (function, ( Command, ScaleFactor, StrKill ))
#        self.cmd_data = {
#            'ARM-AcDuty':  (self.read_float,
#                            ('X-AC-DETECTOR-DUTY', 1, '%')),
#            }

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
        reply = int(self.action('"STATUS XN?', expected=1))
        if state:
            value = 0x80000000 | reply
        else:
            value = 0x7FFFFFFF & reply
        cmd = '${} "STATUS XN!'.format(value)
        self._logger.debug('%s', cmd)
        self.action(cmd)

    def bklght(self, param=100):
        """Set backlight intensity."""
        self.action('{} 0 X!'.format(param))
