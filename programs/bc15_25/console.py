#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2015 SETEC Pty Ltd.
"""BC15/25 ARM processor console driver."""

import re
import share


class Console(share.console.Base):

    """Communications to BC15/25 console."""

    # Number of lines in startup banner
    banner_lines = 3
    # Number of lines in a STAT response
    stat_linecount = 46
    # Number of lines in a CAL? response
    cal_linecount = None
    parameter = share.console.parameter
    cmd_data = {
        'UNLOCK': parameter.Boolean(
            '0xDEADBEA7 UNLOCK',
            writeable=True, readable=False, write_format='{1}'),
        'NVDEFAULT': parameter.Boolean(
            'NV-DEFAULT',
            writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': parameter.Boolean(
            'NV-WRITE',
            writeable=True, readable=False, write_format='{1}'),
        'SW_VER': parameter.String('SW-VERSION', read_format='{0}?'),
        'SWITCH': parameter.Float('SW', read_format='{0}?'),
        }
    stat_data = {}  # Data readings: Key=Name, Value=Reading
    stat_regexp = re.compile('^([a-z\-]+)=([0-9]+).*$')
    cal_data = {}   # Calibration readings: Key=Name, Value=Setting
    cal_regexp = re.compile('^([a-z_0-9]+) +([\-0-9]+) $')

    def initialise(self, reset_relay):
        """Initialise the unit."""
        self.port.reset_input_buffer()
        reset_relay.pulse(0.1)
        self.banner()
        self['UNLOCK'] = True
        self['NVDEFAULT'] = True
        self['NVWRITE'] = True

    def banner(self):
        """Consume the startup banner."""
        self.action(None, delay=2, expected=self.banner_lines)

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
        self.stat_data.clear()
        response = self.action('STAT', expected=self.stat_linecount)
        for line in response:
            match = self.stat_regexp.match(line)
            if match:
                key, val = match.groups()
                self.stat_data[key] = val
        self._logger.debug('Stat read %s data values', len(self.stat_data))

    def cal_read(self):
        """Use CAL? command to read calibration values."""
        self._logger.debug('Cal')
        self.cal_data.clear()
        response = self.action('CAL?', expected=self.cal_linecount)
        for line in response:
            match = self.cal_regexp.match(line)
            if match:
                key, val = match.groups()
                self.cal_data[key] = val
        self._logger.debug('Cal read %s values', len(self.cal_data))

    def ps_mode(self, voltage, current):
        """Set the unit into Power Supply mode.

        @param voltage Output voltage setting
        @param current Output OCP setting

        """
        self.action('0 MAINLOOP')
        self.action('STOP')
        self.action('{0} SETMA'.format(round(current * 1000)))
        self.action('{0} SETMV'.format(round(voltage * 1000)))
        self.action('0 0 PULSE')
        self.action('RESETOVERVOLT')
        self.action('1 SETDCDCEN')
        self.action('1 SETPSON')
        self.action('1 SETDCDCOUT')
        self.action('0 SETPSON', delay=0.5)
        self.action('RESETOVERVOLT')

    def powersupply(self):
        """Set the unit to default to Power Supply mode at switch-on."""
        self.action('"POWERSUPPLY SETCHARGEMODE')
        self['NVWRITE'] = True

    def cal_vout(self, voltage):
        """Calibrate the output voltage setpoint.

        This product does not have a calibration command, so we must adjust
        the internal calibration constants ourselves.

        @param voltage Actual output voltage of the unit

        """
        # Randall said:
        # I looked at the PWM calibration in the code, its possible for you to
        # employ a simple formula, taking data from the STAT command and
        # issuing a modification to just the numerator leaving the
        # denominator alone.
        self.stat()
        self.cal_read()
        mv_num = float(self['set_volts_mv_num'])
        mv_den = float(self['set_volts_mv_den'])
        mv_set = float(self['mv-set'])
        # Calculate the PWM value (0-1023) given the numerator, denominator,
        # and millivolt set point.
        pwm = round((mv_set * mv_num) / mv_den)
        # Calculate new numerator using measured voltage.
        mv_num_new = round((pwm * mv_den) / (voltage * 1000))
        # Write new numerator and save it.
        self.action('{0} "SET_VOLTS_MV_NUM CAL'.format(mv_num_new))
        self['NVWRITE'] = True
        self.action('{0} SETMV'.format(round(mv_set)))

    def cal_iout(self, current, ocp_factor):
        """Calibrate the output current reading & setpoint.

        This product does not have a calibration command, so we must adjust
        the internal calibration constants ourselves.

        @param current Actual output current of the unit
        @param ocp_factor Factor to apply to the OCP setpoint

        """
        self.stat()
        self.cal_read()
        # Output current reading correction
        ma_num = float(self['get_current_ma_num'])
        ma_rdg = float(self['not-pulsing-current'])
        ma_set = self['ma-set']
        ma_num_new = round((current * 1000 * ma_num) / ma_rdg)
        self.action('{0} "GET_CURRENT_MA_NUM CAL'.format(ma_num_new))
        # OCP setpoint correction
        new_set_num = round(float(self['set_current_ma_num']) * ocp_factor)
        self.action('{0} "SET_CURRENT_MA_NUM CAL'.format(new_set_num))
        # Save & refresh
        self['NVWRITE'] = True
        self.action('{0} SETMA'.format(ma_set))
