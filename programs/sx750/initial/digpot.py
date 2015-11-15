#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Digital Pot Driver.

12V and 24V OCP point adjustment.
Both devices share UP/~DOWN pin.
Each has a ~ChipSelect pin.
Pins are driven by opto-couplers, driven by Tester relay drive lines.
All lines have 22k pull up to '5Vcc' of the unit.
NOTE: UP on the pots REDUCES the OCP point!

Pot UP Procedure (OCP DOWN):
    Both CS and UD are high (off)
    Set UD off (off = UP)
    Set CS on
    Set UD on
    Pulse UD off-on (setting moves when turn off happens)
    Set CS off (UD on here causes a write to EEPROM)
    Set UD off

Pot DOWN Procedure (OCP UP):
    Both CS and UD are high (off)
    Set UD on (on = DOWN)
    Set CS on
    Pulse UD on-off (setting moves when turn off happens)
    Set CS off (UD off here causes a write to EEPROM)

WriteLock device function is not used or enabled.

"""

import logging


class PotError(Exception):

    """Digital Pot exception class."""

    def __init__(self, message):
        """Create error."""
        super(PotError, self).__init__()
        self.message = message

    def __str__(self):
        """Error name.

        @return Error message

        """
        return repr(self.message)


class OCPAdjust():

    """12V and 24V OCP adjustment driver."""

    def __init__(self, relay_ud, relay_cs12v, relay_cs24v):
        """Initialise digital pot driver."""
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._logger.debug('Started')
        self._ud = relay_ud
        self._cs12 = relay_cs12v
        self._cs24 = relay_cs24v
        self._active = False
        self._isdown = False
        self.disable()

    def disable(self):
        """Reset digital pot drive bits to all high (off).

        CS lines must go high before the UD line.

        """
        self._logger.debug('Disable')
        self._cs12.set_off()
        self._cs24.set_off()
        self._ud.set_off()
        self._active = False

    def set_middle(self):
        """Set both pots to middle value.

        Set to Maximum, then go DOWN 32 steps.

        """
        self._logger.debug('SetMiddle')
        self.set_maximum()
        self._enable((self._cs12, self._cs24), step_down=True)
        self.step(32)
        self.disable()

    def set_maximum(self):
        """Set both pots to maximum value.

        Enable both, then pulse DOWN 64 times.

        """
        self._logger.debug('SetMaximum')
        self._enable((self._cs12, self._cs24), step_down=False)
        self.step(64)
        self.disable()

    def enable_12v(self, step_down=True):
        """Enable 12V adjustment.

        @param step_down True to step DOWN, False to step UP.

        """
        self._logger.debug('Enable12V')
        self._enable((self._cs12,), step_down)

    def enable_24v(self, step_down=True):
        """Enable 24V adjustment.

        @param step_down True to step DOWN, False to step UP.

        """
        self._logger.debug('Enable24V')
        self._enable((self._cs24,), step_down)

    def _enable(self, driver, step_down):
        """Enable an adjustment.

        @param driver Relay CS driver.
        @param step_down True to step DOWN, False to step UP.

        """
        if self._active:
            raise PotError('Enable when already busy')
        self._isdown = step_down
        if self._isdown:
            for drv in driver:
                drv.set_on()
            self._ud.set_on()
        else:
            self._ud.set_on()
            for drv in driver:
                drv.set_on()
        self._active = True

    def step(self, count=1):
        """Step the enabled adjustment.

        @param count Number of steps.

        """
        self._logger.debug('Step %s steps', count)
        if not self._active:
            raise PotError('Step when not enabled')
        if self._isdown:
            for _ in range(count):
                self._ud.set_off()
                self._ud.set_on()
        else:
            for _ in range(count):
                self._ud.set_on()
                self._ud.set_off()
        self._ud.opc()
