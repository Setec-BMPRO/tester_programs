#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BC15/25 Initial Test program."""

import unittest
from unittest.mock import MagicMock, patch
import tester
from programs import bc15_25


class BC25_Console(unittest.TestCase):

    """BC25 Console program test suite."""

    prompt = '\r\n> '
    stat_reply = """# error blink count...
# battery:    solid
# polarity    1
# temperature 2
# short       3
# over volt   4
# under volt  5
# batt temp   6
used-data=0xB18
free-data=0x14E8
used-stack=0x98
free-stack=0x1450
pri-temp=304 hz=35 ;degCx10
sec-temp=229 raw=938/1024 ;degCx10
batttemp=10002 NOTINSTALLED override=yes raw=0/1024
pulsing-open-volts=N/A ;mV (=N/A because not pulsing)
pulsing-open-current=N/A ;mA (=N/A because not pulsing)
pulsing-closed-volts=N/A ;mV (=N/A because not pulsing)
pulsing-closed-current=N/A ;mA (=N/A because not pulsing)
not-pulsing-volts=14457 ;mV (=N/A if pulsing)
not-pulsing-current=14172 ;mA (=N/A if pulsing)
pulse-on-off-ms=0,0
batt-detect=NOINFO ;mV (NOINFO/NOBATT/SHORT/POLARITY/OVERVOLT)
volts-open-closed-rawadc=924,924
current-open-closed-rawadc=767,767
battdetect-open-closed-volts-rawadc=5,5
overvolt-latch=0 ;(r) resets
fan-enable=0
dcdc-enable=1 ;(e) toggles
dcdcout-enable=1 ;(o) toggles
ps-on=0 ;(p) toggles
mv-set=14400 ;mV
ma-set=15000 ;mA
logm=0x0
mainloop-run=0
mainloop-ms=100
mainloop-errors=1
mainloop-reconditions=0
chemistry=GEL
chargemode=CHARGEHIGHAMP
chargestate=ERROR
# LEDs:  .=off  *=on  @=blinking
# Fault=red   + Stage1=green  (bi-color)
# SizeC=green + SizeD =yellow (bi-color)
# Fault__Stage1  2  3  4  5  6   ChemA  B  C  D   SizeA  B  C__D
#     .       .  .  .  .  .  .       *  .  .  .       .  .  *  .
"""
    cal_reply = """get_volts_mv_num                      16022
get_volts_mv_den                       1024
get_volts_mv_off                          0
get_current_ma_num                     2365
get_current_ma_den                      128
get_current_ma_off                        0
set_volts_mv_num                        902
set_volts_mv_den                      14400
set_volts_mv_off                          0
set_current_ma_num                      831
set_current_ma_den                    15000
set_current_ma_off                        0
fan_pri_on_degcx10                      750
fan_pri_off_degcx10                     600
fan_sec_on_degcx10                      500
fan_sec_off_degcx10                     400
derate_pri_lo_degcx10                   900
derate_pri_hi_degcx10                  1100
derate_pri_tozero_degcx10              1150
derate_pri_lo_ma                       2500
derate_pri_hi_ma                      15000
derate_sec_lo_degcx10                   550
derate_sec_hi_degcx10                  1100
derate_sec_tozero_degcx10              1150
derate_sec_lo_ma                       2500
derate_sec_hi_ma                      15000
charge_high_ma                        15000
charge_med_ma                         10000
charge_low_ma                          5000
powersupply_led_is_greenred               1
longpress_ms                           5000
bmsoff_wake_set_mv                    15000
bmsoff_wake_set_ma                     2000
bmsoff_wake_det_mv                     9000
bmsoff_wake_det_ma                     1000
bmsoff_wake_det_ms                     3000
logm                                      0
powersupply_mv                        13600
powersupply_ma                        10000
"""
    @classmethod
    def setUpClass(cls):
        # We need a tester to get MeasurementFailedError.
        cls.tester = tester.Tester('MockATE', {})

    @classmethod
    def tearDownClass(cls):
        cls.tester.stop()

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'time.sleep',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        port = tester.devphysical.sim_serial.SimSerial()
        port.echo = True
        self.con = bc15_25.console.Console(port)
        self.con.parameter = '15'

    def test_nobanner(self):
        """Missing banner lines."""
        with self.assertRaises(tester.MeasurementFailedError):
            self.con.action(None, expected=3)

    def test_banner(self):
        """Banner lines present."""
        self.con.port.puts('X\r\n' * 3 + self.prompt)
        self.con.banner()

    def test_initialise(self):
        """Initialise."""
        relay = MagicMock()
        self.con.port.puts('X\r\n' * 3 + self.prompt, preflush=1)
        for _ in range(3):
            self.con.port.puts(self.prompt, preflush=1)
        self.con.initialise(relay)
        written = self.con.port.get()
        self.assertEqual(b'0xDEADBEA7 UNLOCK\rNV-DEFAULT\rNV-WRITE\r', written)
        self.assertTrue(relay.pulse.called)

    def test_stat(self):
        """STAT response."""
        self.con.port.puts(
            self.stat_reply.replace('\n', '\r\n') + '> ', preflush=1)
        self.con.stat()
        self.assertEqual(25, len(self.con.stat_data))

    def test_cal(self):
        """CAL? response."""
        self.con.port.puts(
            self.cal_reply.replace('\n', ' \r\n') + '> ', preflush=1)
        self.con.cal_read()
        self.assertEqual(39, len(self.con.cal_data))
