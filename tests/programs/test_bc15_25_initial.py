#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BC15/25 Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import bc15_25


class _BC15_25_Initial(ProgramTestCase):

    """BC15/25 Initial program test suite."""

    prog_class = bc15_25.Initial
    startup_banner = (
        'Banner line 1\r\n'
        'Banner line 2\r\n'
        'Banner line 3\r\n'
        )

    def _pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['arm'].port.flushInput()    # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PartDetect':
                    ((sen['lock'], 0.0), (sen['fanshort'], 3300.0), ),
                'PowerUp':
                    ((sen['ACin'], 240.0), (sen['Vbus'], 330.0),
                     (sen['12Vs'], 12.0), (sen['3V3'], 3.3),
                     (sen['15Vs'], 15.0), (sen['Vout'], 0.2), ),
                'Output': ((sen['Vout'], 14.40), (sen['Vout'], 14.40), ),
                'Loaded': ((sen['Vout'], (14.4, ) * 5 + (11.0, ), ), ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'Initialise': (
                    (None, ) +  # Terminate port.flushInput()
                    (self.startup_banner, ) +
                    ('', ) * 3 +
                    ('{}'.format(self.test_program.config['BinVersion']), )
                    ),
                'PowerUp': (
                    (self.startup_banner, ) +
                    ('', ) * 10
                    ),
                'Output':
                    ('#\r\n' * 44 +     # Dummy response lines
                        'not-pulsing-volts=14432 ;mV \r\n'
                        'not-pulsing-current=1987 ;mA ',
                    '3',
                    '#\r\n' * 44 +      # Dummy response lines
                        'mv-set=14400 ;mV \r\n'
                        'not-pulsing-volts=14432 ;mV ',
                    '#\r\n' * 37 +      # Dummy response lines
                        'set_volts_mv_num                        902 \r\n'
                        'set_volts_mv_den                      14400 ', ) +
                    ('', ) * 3,
                'Loaded':
                    ('#\r\n' * 44 +     # Dummy response lines
                        'not-pulsing-volts=14432 ;mV \r\n'
                        'not-pulsing-current={0} ;mA '.format(
                            round(1000 *
                                self.test_program.config['OCP_Nominal'])), ) +
                    ('OK', ) * 2,
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push, dev['arm'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(18, len(result.readings))
        self.assertEqual(
            ['PartDetect', 'Initialise', 'PowerUp', 'Output', 'Loaded'],
            self.tester.ut_steps)


class BC15_Initial(_BC15_25_Initial):

    """BC15 Initial program test suite."""

    parameter = '15'
    debug = False

    def test_pass_run(self):
        """PASS run of the BC15 program."""
        super()._pass_run()


class BC25_Initial(_BC15_25_Initial):

    """BC25 Initial program test suite."""

    parameter = '25'
    debug = False

    def test_pass_run(self):
        """PASS run of the BC25 program."""
        super()._pass_run()
