#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 ARM processor console driver."""

from ..share import console


Sensor = console.Sensor

# Some easier to use short names
ParameterBoolean = console.ParameterBoolean
ParameterFloat = console.ParameterFloat
ParameterHex = console.ParameterHex
ParameterRaw = console.ParameterRaw


class Console(console.ConsoleGen2):

    """Communications to BC15 console."""

    def ps_mode(self):
        """Set the unit into Power Supply mode."""
        self.action('0 MAINLOOP')
        self.action('STOP')
        self.action('15000 SETMA')
        self.action('14400 SETMV')
        self.action('0 0 PULSE')
        self.action('RESETOVERVOLT')
        self.action('1 SETDCDCEN')
        self.action('1 SETPSON')
        self.action('1 SETDCDCOUT')
        self.action('0 SETPSON', delay=0.5)

    def cal_vout(self, voltage):
        """Calibrate the output voltage setpoint.

        This product does not have a calibration command, so we must adjust
        the internal calibration constants ourselves.

        """
        # Randall said:
        # I looked at the pwm calibration in the code, its possible for you to
        # employ a simple formula, taking data from the stat command and
        # issuing a modification to just the numerator leaving the
        # denominator alone.
        self.stat()
        self.cal_read()
        mv_num = float(self['set_volts_mv_num'])
        mv_den = float(self['set_volts_mv_den'])
        mv_set = float(self['mv-set'])
        # Calculate the PWM value (0-1023) given the numerator, denominator,
        # and millivolt setpoint.
        pwm = int(((mv_set * mv_num) / mv_den) + 0.5)
        # Calculate new numerator using measured voltage.
        mv_num_new = int(((pwm * mv_den) / (voltage * 1000)) + 0.5)
        # Write new numerator and save it.
        self.action('{} "SET_VOLTS_MV_NUM CAL'.format(mv_num_new))
        self.nvwrite()
        self.action('{} SETMV'.format(mv_set))
