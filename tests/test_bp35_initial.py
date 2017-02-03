#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BP35 Initial Test program."""

from unittest.mock import MagicMock, patch
from .data_feed import UnitTester, ProgramTestCase
from programs import bp35


class BP35Initial(ProgramTestCase):

    """BP35 Initial program test suite."""

    prog_class = bp35.Initial
    parameter = None
    debug = False

    def _arm_loads(self, value):
        """Fill all ARM Load sensors with a value."""
        sen = self.test_program.sensors
        for sensor in sen['arm_loads']:
            sensor.store(value)

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['bp35_ser'].flushInput()    # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Prepare':
                    ((sen['lock'], 10.0), (sen['hardware'], 4400),
                     (sen['vbat'], 12.0), (sen['o3v3'], 3.3),
                     (sen['solarvcc'], 3.3),
                     (sen['sernum'], ('A1626010123', )), ),
                'Initialise': ((sen['sernum'], ('A1526040123', )), ),
                'SolarReg':
                    ((sen['vset'], (13.0, 13.5)), (sen['solarvin'], 19.55), ),
                'Aux': ((sen['vbat'], 13.5), ),
                'PowerUp':
                    ((sen['acin'], 240.0), (sen['pri12v'], 12.5),
                     (sen['o3v3'], 3.3), (sen['o15vs'], 12.5),
                     (sen['vbat'], 12.8), (sen['vpfc'], (415.0, 415.0), )),
                'Output': ((sen['vload'], (0.0, ) + (12.8, ) * 14), ),
                'RemoteSw': ((sen['vload'], (0.25, 12.34)), ),
                'OCP':
                    ((sen['fan'], (0, 12.0)), (sen['vbat'], 12.8),
                     (sen['vbat'], (12.8, ) * 6 + (11.0, ), ), ),
                },
            UnitTester.key_call: {      # Callables
                'OCP': (self._arm_loads, 2.0),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'Initialise':
                    ('Banner1\r\nBanner2', ) +
                    ('', ) + ('success', ) * 2 + ('', ) * 4 +
                    ('Banner1\r\nBanner2', ) +
                    ('', ) +
                    (bp35.initial.ARM_VERSION, ) +
                    ('', ) + ('0x10000', ) + ('', ) * 3,      # Manual mode
                'SolarReg':
                    ('1.0', '0') +      # Solar alive, Vout OV
                    ('', ) * 3 +        # 2 x Solar VI, Vout OV
                    ('0', '1') +        # Errorcode, Relay
                    ('19900', ) +       # Vin pre
                    ('', ) * 2 +        # 2 x Vcal
                    ('', ) * 2 +        # 2 x Solar VI
                    ('19501', ) +       # Vin post
                    ('10500', ) +       # IoutPre
                    ('', ) +            # Ical
                    ('10100', ),        # IoutPost
                'Aux': ('', '13500', '1100', ''),
                'PowerUp':
                    ('', ) * 4 +     # Manual mode
                    ('0', ) * 2,
                'Output': ('', ) * (1 + 14 + 1),
                'OCP':
                    ('240', '50000', '350', '12800', '500', ) +
                    ('', '4000', '32000', ),
                'CanBus': ('0x10000000', '', '0x10000000', '', '', ),
                },
            UnitTester.key_con_np: {    # Tuples of strings, addprompt=False
                'CanBus': ('RRQ,32,0,7,0,0,0,0,0,0,0\r\n', ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push, dev['bp35'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(73, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['Prepare', 'Initialise', 'SolarReg', 'Aux', 'PowerUp',
             'Output', 'RemoteSw', 'OCP', 'CanBus'],
            self.tester.ut_steps)

    def test_fail_run(self):
        """FAIL 1st Vbat reading."""
        # Patch threading.Event & threading.Timer to remove delays
        mymock = MagicMock()
        mymock.is_set.return_value = True   # threading.Event.is_set()
        patcher = patch('threading.Event', return_value=mymock)
        self.addCleanup(patcher.stop)
        patcher.start()
        patcher = patch('threading.Timer', return_value=mymock)
        self.addCleanup(patcher.stop)
        patcher.start()
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Prepare':
                    ((sen['lock'], 10.0), (sen['hardware'], 4400),
                     (sen['sernum'], ('A1626010123', )),
                     (sen['vbat'], 2.5), ),   # Vbat will fail
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('F', result.code)      # Must have failed
        self.assertEqual(4, len(result.readings))
        self.assertEqual(['Prepare'], self.tester.ut_steps)
