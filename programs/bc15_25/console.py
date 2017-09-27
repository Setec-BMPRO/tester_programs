#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15/25 ARM processor console driver."""

import re
import share

# Some easier to use short names
Sensor = share.console.Sensor
ParameterString = share.console.ParameterString
ParameterBoolean = share.console.ParameterBoolean
ParameterFloat = share.console.ParameterFloat


class Console(share.console.BaseConsole):

    """Communications to BC15/25 console."""

    # Auto add prompt to puts strings
    puts_prompt = '\r\n> '
    # Number of lines in startup banner
    banner_lines = 3
    cmd_data = {
        'UNLOCK': ParameterBoolean('0xDEADBEA7 UNLOCK',
            writeable=True, readable=False, write_format='{1}'),
        'NVDEFAULT': ParameterBoolean('NV-DEFAULT',
            writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': ParameterBoolean('NV-WRITE',
            writeable=True, readable=False, write_format='{1}'),
        'SW_VER': ParameterString('SW-VERSION', read_format='{0}?'),
        'SWITCH': ParameterFloat('SW', read_format='{0}?'),
        }
    stat_data = {}  # Data readings: Key=Name, Value=Reading
    stat_regexp = re.compile('^([a-z\-]+)=([0-9]+).*$')
    cal_data = {}   # Calibration readings: Key=Name, Value=Setting
    cal_regexp = re.compile('^([a-z_0-9]+) +([\-0-9]+) $')
    # Program parameter ('15' for BC15 or '25' for BC25)
    parameter = None
    # OCP setpoint adjustment factor
    ocp_setpoint_factor = 0.9

    def initialise(self, reset_relay):
        """Initialise the unit."""
        self.port.flushInput()
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
        response = self.action('STAT', expected=46)
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
        expected = {'15': 39,  '25': 43}[self.parameter]
        response = self.action('CAL?', expected=expected)
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

    def powersupply(self):
        """Set the unit to default to Power Supply mode at switch-on."""
        self.action('"POWERSUPPLY SETCHARGEMODE')
        self['NVWRITE'] = True

    def cal_vout(self, voltage):
        """Calibrate the output voltage setpoint.

        This product does not have a calibration command, so we must adjust
        the internal calibration constants ourselves.

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

    def cal_iout(self, current):
        """Calibrate the output current reading & setpoint.

        This product does not have a calibration command, so we must adjust
        the internal calibration constants ourselves.

        """
        self.stat()
        self.cal_read()
        # Output current reading closed-loop correction
        ma_num = float(self['get_current_ma_num'])
        ma_rdg = float(self['not-pulsing-current'])
        ma_set = self['ma-set']
        ma_num_new = round((current * 1000 * ma_num) / ma_rdg)
        self.action('{0} "GET_CURRENT_MA_NUM CAL'.format(ma_num_new))
        # OCP setting open-loop adjustment
        new_set_num = round(
            float(self['set_current_ma_num']) * self.ocp_setpoint_factor)
        self.action('{0} "SET_CURRENT_MA_NUM CAL'.format(new_set_num))
        # Save & refresh
        self['NVWRITE'] = True
        self.action('{0} SETMA'.format(ma_set))

# Sample console responses 2017-06-27
#
#stat = [
#    '# error blink count...',
#    '# battery:    solid',
#    '# polarity    1',
#    '# temperature 2',
#    '# short       3',
#    '# over volt   4',
#    '# under volt  5',
#    '# batt temp   6',
#    'used-data=0xB18',
#    'free-data=0x14E8',
#    'used-stack=0x98',
#    'free-stack=0x1450',
#    'pri-temp=304 hz=35 ;degCx10',
#    'sec-temp=229 raw=938/1024 ;degCx10',
#    'batttemp=10002 NOTINSTALLED override=yes raw=0/1024',
#    'pulsing-open-volts=N/A ;mV (=N/A because not pulsing)',
#    'pulsing-open-current=N/A ;mA (=N/A because not pulsing)',
#    'pulsing-closed-volts=N/A ;mV (=N/A because not pulsing)',
#    'pulsing-closed-current=N/A ;mA (=N/A because not pulsing)',
#    'not-pulsing-volts=14457 ;mV (=N/A if pulsing)',
#    'not-pulsing-current=14172 ;mA (=N/A if pulsing)',
#    'pulse-on-off-ms=0,0',
#    'batt-detect=NOINFO ;mV (NOINFO/NOBATT/SHORT/POLARITY/OVERVOLT)',
#    'volts-open-closed-rawadc=924,924',
#    'current-open-closed-rawadc=767,767',
#    'battdetect-open-closed-volts-rawadc=5,5',
#    'overvolt-latch=0 ;(r) resets',
#    'fan-enable=0',
#    'dcdc-enable=1 ;(e) toggles',
#    'dcdcout-enable=1 ;(o) toggles',
#    'ps-on=0 ;(p) toggles',
#    'mv-set=14400 ;mV',
#    'ma-set=15000 ;mA',
#    'logm=0x0',
#    'mainloop-run=0',
#    'mainloop-ms=100',
#    'mainloop-errors=1',
#    'mainloop-reconditions=0',
#    'chemistry=GEL',
#    'chargemode=CHARGEHIGHAMP',
#    'chargestate=ERROR',
#    '# LEDs:  .=off  *=on  @=blinking',
#    '# Fault=red   + Stage1=green  (bi-color)',
#    '# SizeC=green + SizeD =yellow (bi-color)',
#    '# Fault__Stage1  2  3  4  5  6   ChemA  B  C  D   SizeA  B  C__D',
#    '#     .       .  .  .  .  .  .       *  .  .  .       .  .  *  .',
#    ]
#
#cal = [
#    'get_volts_mv_num                      16022 ',
#    'get_volts_mv_den                       1024 ',
#    'get_volts_mv_off                          0 ',
#    'get_current_ma_num                     2365 ',
#    'get_current_ma_den                      128 ',
#    'get_current_ma_off                        0 ',
#    'set_volts_mv_num                        902 ',
#    'set_volts_mv_den                      14400 ',
#    'set_volts_mv_off                          0 ',
#    'set_current_ma_num                      831 ',
#    'set_current_ma_den                    15000 ',
#    'set_current_ma_off                        0 ',
#    'fan_pri_on_degcx10                      750 ',
#    'fan_pri_off_degcx10                     600 ',
#    'fan_sec_on_degcx10                      500 ',
#    'fan_sec_off_degcx10                     400 ',
#    'derate_pri_lo_degcx10                   900 ',
#    'derate_pri_hi_degcx10                  1100 ',
#    'derate_pri_tozero_degcx10              1150 ',
#    'derate_pri_lo_ma                       2500 ',
#    'derate_pri_hi_ma                      15000 ',
#    'derate_sec_lo_degcx10                   550 ',
#    'derate_sec_hi_degcx10                  1100 ',
#    'derate_sec_tozero_degcx10              1150 ',
#    'derate_sec_lo_ma                       2500 ',
#    'derate_sec_hi_ma                      15000 ',
#    'charge_high_ma                        15000 ',
#    'charge_med_ma                         10000 ',
#    'charge_low_ma                          5000 ',
#    'powersupply_led_is_greenred               1 ',
#    'longpress_ms                           5000 ',
#    'bmsoff_wake_set_mv                    15000 ',
#    'bmsoff_wake_set_ma                     2000 ',
#    'bmsoff_wake_det_mv                     9000 ',
#    'bmsoff_wake_det_ma                     1000 ',
#    'bmsoff_wake_det_ms                     3000 ',
#    'logm                                      0 ',
#    'powersupply_mv                        13600 ',
#    'powersupply_ma                        10000 ',
#    ]
