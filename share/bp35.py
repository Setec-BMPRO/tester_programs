#!/usr/bin/env python3
"""BP35 ARM processor console driver."""

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

