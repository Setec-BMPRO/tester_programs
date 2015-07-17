#!/usr/bin/env python3
"""BP35 ARM processor console driver."""

import share.arm_gen1


# Expose arm_gen1.Sensor as bp35.Sensor
Sensor = share.arm_gen1.Sensor


class Console(share.arm_gen1.ArmConsoleGen1):

    """Communications to ARM console."""

    def __init__(self):
        """Create console instance."""
        super().__init__(dialect=1)
        self._read_cmd = None
        # Data readings:
        #   Name -> (function, ( Command, ScaleFactor, StrKill ))
#        self.cmd_data = {
#            'ARM-AcDuty':  (self.read_float,
#                            ('X-AC-DETECTOR-DUTY', 1, '%')),
#            }
