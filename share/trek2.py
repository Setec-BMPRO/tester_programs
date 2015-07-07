#!/usr/bin/env python3
"""Trek2 ARM processor console driver.

Communication via Serial port to the ARM processor.

"""
import logging

import tester
import share.arm_gen1

class Sensor(tester.sensor.Sensor):

    """ARM console data exposed as a Sensor."""

    def __init__(self, arm, key, rdgtype=tester.sensor.Reading, position=1):
        """Create a sensor."""
        super().__init__(arm, position)
        self._arm = arm
        self._key = key
        self._rdgtype = rdgtype
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._logger.debug('Created')

    def configure(self):
        """Configure measurement."""
        self._arm.configure(self._key)

    def read(self):
        """Take a reading.

        @return Reading

        """
        rdg = self._rdgtype(value=super().read(), position=self.position)
        return (rdg, )


class Console(share.arm_gen1.ArmConsoleGen1):

    """Communications to ARM console."""

    def __init__(self, serport):
        """Open serial communications."""
        super().__init__(serport, dialect=1)
        self._read_cmd = None
        # Data readings:
        #   Name -> (function, ( Command, ScaleFactor, StrKill ))
        self._data = {
            'ARM-AcDuty':  (self._getvalue,
                            ('X-AC-DETECTOR-DUTY', 1, '%')),
            }

    def configure(self, cmd):
        """Sensor: Configure for next reading."""
        self._read_cmd = cmd

    def opc(self):
        """Sensor: Dummy OPC."""
        pass

    def read(self):
        """Sensor: Read ARM data.

        @return Value

        """
        self._logger.debug('read %s', self._read_cmd)
        fn, param = self._data[self._read_cmd]
        result = fn(param)
        self._logger.debug('result %s', result)
        return result

    def _getvalue(self, data):
        """Get data value from ARM.

        @return Value

        """
        cmd, scale, strkill = data
        reply = self._sendrecv('{} X?'.format(cmd))
        if reply is None:
            value = -999.999
        else:
            reply = reply.replace(strkill, '')
            value = float(reply) * scale
        return value

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
        reply = self.action('"STATUS XN?', expected=1)
        if state:
            value = 0x80000000 | int(reply)
        else:
            value = 0x7FFFFFFF & int(reply)
        cmd = '${} "STATUS XN!'.format(value)
        self._logger.debug('%s', cmd)
        self.action(cmd)

    def bklght(self, param=100):
        """Turn backlight on/off."""
        self.action('{} 0 X!'.format(param))
