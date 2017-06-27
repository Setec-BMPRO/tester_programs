#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 ARM processor console driver."""

import re
from share import console

Sensor = console.Sensor

# Some easier to use short names
ParameterString = console.ParameterString
ParameterBoolean = console.ParameterBoolean
ParameterFloat = console.ParameterFloat


class Console(console.BaseConsole):

    """Communications to BC15 console."""

    # Auto add prompt to puts strings
    puts_prompt = '\r\n> '
    cmd_data = {
        'UNLOCK': ParameterBoolean('0xDEADBEA7 UNLOCK',
            writeable=True, readable=False, write_format='{1}'),
        'NVDEFAULT': ParameterBoolean('NV-DEFAULT',
            writeable=True, readable=False, write_format='{1}'),
        'NVWRITE': ParameterBoolean('NV-WRITE',
            writeable=True, readable=False, write_format='{1}'),
        'SW_VER': ParameterString('SW-VERSION', read_format='{}?'),
        'SWITCH': ParameterFloat('SW', read_format='{}?'),
        }
    stat_data = {}  # Data readings: Key=Name, Value=Reading
    stat_regexp = re.compile('^([a-z\-]+)=([0-9]+).*$')
    cal_data = {}   # Calibration readings: Key=Name, Value=Setting
    cal_regexp = re.compile('^([a-z_]+) +([0-9]+) $')

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
        response = self.action('CAL?', expected=39)
        for line in response:
            match = self.cal_regexp.match(line)
            if match:
                key, val = match.groups()
                self.cal_data[key] = val
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
        pwm = round(((mv_set * mv_num) / mv_den) + 0.5)
        # Calculate new numerator using measured voltage.
        mv_num_new = round(((pwm * mv_den) / (voltage * 1000)) + 0.5)
        # Write new numerator and save it.
        self.action('{} "SET_VOLTS_MV_NUM CAL'.format(mv_num_new))
        self['NVWRITE'] = True
        self.action('{} SETMV'.format(round(mv_set)))

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
#
#print('stat', len(stat))
#print('cal', len(cal))
