#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 ARM processor console driver."""

from share import console

Sensor = console.Sensor

# Some easier to use short names
ParameterString = console.ParameterString
ParameterBoolean = console.ParameterBoolean
ParameterFloat = console.ParameterFloat


class Console(console.Variable, console.BaseConsole):

    """Communications to BC15 console."""

    def __init__(self, port, verbose=False):
        """Create console instance."""
        # Call __init__() methods directly, since we cannot use super() as
        # the arguments don't match
        console.Variable.__init__(self)
        console.BaseConsole.__init__(self, port, verbose)
        self.cmd_data = {
            'UNLOCK': ParameterString('0xDEADBEA7 UNLOCK',
                writeable=True, readable=False, write_format='{1}'),
            'NVDEFAULT': ParameterBoolean('NV-DEFAULT',
                writeable=True, readable=False, write_format='{1}'),
            'NVWRITE': ParameterBoolean('NV-WRITE',
                writeable=True, readable=False, write_format='{1}'),
            'SW_VER': ParameterString('SW-VERSION', read_format='{}?'),
            'SWITCH': ParameterFloat('SW', read_format='{}?'),
            }
        self.stat_data = {}  # Data readings: Key=Name, Value=Reading
        self.cal_data = {}  # Calibration readings: Key=Name, Value=Setting

    def __getitem__(self, key):
        """Read a value."""
        if key in self.stat_data:       # Try a data value
            return self.stat_data[key]
        if key in self.cal_data:        # Next, try a calibration value
            return self.cal_data[key]
        return super().__getitem__(key) # Last, try the command table

    def stat(self):
        """Use STAT command to read data values."""
        self._logger.debug('Stat')
        response = self.action('STAT')
        for line in response:
            if line[0] == '#':              # ignore comment lines
                continue
            line = line.split()[0]          # stop at the 1st space
            line = line.split(sep='=')      # break the "key=value" pairs up
            self.stat_data[line[0]] = line[1]
        self._logger.debug('Stat read %s data values', len(self.stat_data))

    def cal_read(self):
        """Use CAL? command to read calibration values."""
        self._logger.debug('Cal')
        self.cal_data = {}
        response = self.action('CAL?')
        for line in response:
            line = line.split()
            self.cal_data[line[0]] = line[1]
        self._logger.debug('Cal read %s values', len(self.cal_data))

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
        self['NVWRITE'] = True
        self.action('{} SETMV'.format(mv_set))
