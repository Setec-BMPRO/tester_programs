#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BP35 Initial Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import bp35

# Console response string for "Initialise" step
_INIT_CON_SRHA = (
    ('B1\r\nB2\r\nB3', ) +
    ('', ) +
    ('B1\r\nB2\r\nB3', ) +
    ('', ) * 5 +
    ('B1\r\nB2\r\nB3', ) +
    (bp35.initial.Initial.arm_version, ) +
    ('', )
    )
_INIT_CON_PM = (
    ('B1\r\nB2\r\nB3', ) +
    ('', ) +
    ('B1\r\nB2\r\nB3', ) +
    ('', ) * 3 +        # Missing 2 x SR commands here
    ('B1\r\nB2\r\nB3', ) +
    (bp35.initial.Initial.arm_version, ) +
    ('', ) * 2 +
    ('', )
    )


class _BP35Initial(ProgramTestCase):

    """BP35 Initial program test suite."""

    prog_class = bp35.Initial

    def setUp(self):
        """Per-Test setup."""
        patcher = patch('share.BackgroundTimer')
        self.addCleanup(patcher.stop)
        patcher.start()
        patcher = patch('share.ProgramARM')
        self.addCleanup(patcher.stop)
        patcher.start()
        patcher = patch('share.ProgramPIC')
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def _arm_loads(self, value):
        """Fill all ARM Load sensors with a value."""
        sen = self.test_program.sensors
        for sensor in sen['arm_loads']:
            sensor.store(value)

    def _pass_run(self, init_con, rdg_count, steps):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['bp35'].port.flushInput()   # Flush console input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Prepare': (
                    (sen['sernum'], ('A1626010123', )),
                    (sen['lock'], 10.0), (sen['hardware'], 4400),
                    (sen['vbat'], 12.0), (sen['o3v3'], 3.3),
                    ),
                'ProgramPIC': (
                    (sen['solarvcc'], 3.3),
                    ),
                'Initialise': (
                    (sen['sernum'], ('A1626010123', )),
                    ),
                'SrSolar': (
                    (sen['vset'], (13.0, 13.0, 13.5)),
                    (sen['solarvin'], 19.55),
                    ),
                'Aux': (
                    (sen['vbat'], (12.0, 13.5)),
                    ),
                'PowerUp': (
                    (sen['acin'], 240.0), (sen['pri12v'], 12.5),
                    (sen['o3v3'], 3.3), (sen['o15vs'], 12.5),
                    (sen['vbat'], 12.8), (sen['vpfc'], (415.0, 415.0), ),
                    ),
                'Output': (
                    (sen['vload'], (0.0, ) + (12.8, ) * 14),
                    ),
                'RemoteSw': (
                    (sen['vload'], (12.34, )),
                    ),
                'OCP': (
                    (sen['fan'], (0, 12.0)), (sen['vbat'], 12.8),
                    (sen['vbat'], (12.8, ) * 20 + (11.0, ), ),
                    (sen['vbat'], (12.8, ) * 20 + (11.0, ), ),
                    ),
                },
            UnitTester.key_call: {      # Callables
                'OCP': (self._arm_loads, 2.0),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'Initialise':
                    init_con,
                'SrSolar':
                    ('1 ', '0') +      # Solar alive, Vout OV
                    ('', ) * 3 +        # 2 x Solar VI, Vout OV
                    ('0 ', '1') +        # Errorcode, Relay
                    ('19900', ) +       # Vin pre
                    ('', ) * 2 +        # 2 x Vcal
                    ('', ) * 2 +        # 2 x Solar VI
                    ('19501', ) +       # Vin post
                    ('10500', ) +       # IoutPre
                    ('', ) +            # Ical
                    ('10100', ),        # IoutPost
                'Aux': ('', '13500', '1100', ''),
                'PowerUp':
                    ('', ) * 8 +       # Manual mode
                    ('0', ) * 2 +
                    ('12341234', ) * 2 + # Calibrations
                    ('', ),
                'Output':
                    ('', ) * (1 + 14 + 1),
                'RemoteSw':
                    ('1', ),
                'PmSolar':
                    ('1', '555', '1234 -> 1235', '', '66', ),
                'OCP':
                    ('240', '50000', '350', '12800', '500', ) +
                    ('', '4000', '32000', '12341234', '41000', '', '', ),
                'CanBus': ('0x10000000', '', '0x10000000', '', '', ),
                },
            UnitTester.key_con_np: {    # Tuples of strings, addprompt=False
                'CanBus': ('RRQ,32,0,7,0,0,0,0,0,0,0\r\n', ),
                },
            }
        self.tester.ut_load(data, self.test_program.fifo_push, dev['bp35'].puts)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(rdg_count, len(result.readings))
        self.assertEqual(steps, self.tester.ut_steps)

    def _fail_run(self):
        """FAIL 1st Vbat reading."""
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


class BP35_SR_Initial(_BP35Initial):

    """BP35xxxSR Initial program test suite."""

    parameter = 'SR'
    debug = False

    def test_pass_run(self):
        """PASS run of the C program."""
        super()._pass_run(
            _INIT_CON_SRHA,
            75,
            ['Prepare', 'ProgramPIC', 'ProgramARM', 'Initialise', 'SrSolar',
             'Aux', 'PowerUp', 'Output', 'RemoteSw', 'OCP', 'CanBus'],
            )


class BP35_HA_Initial(_BP35Initial):

    """BP35xxxHA Initial program test suite."""

    parameter = 'HA'
    debug = False

    def test_pass_run(self):
        """PASS run of the C program."""
        super()._pass_run(
            _INIT_CON_SRHA,
            75,
            ['Prepare', 'ProgramPIC', 'ProgramARM', 'Initialise', 'SrSolar',
             'Aux', 'PowerUp', 'Output', 'RemoteSw', 'OCP', 'CanBus'],
            )


class BP35_PM_Initial(_BP35Initial):

    """BP35xxxPM Initial program test suite."""

    parameter = 'PM'
    debug = False

    def test_pass_run(self):
        """PASS run of the C program."""
        super()._pass_run(
            _INIT_CON_PM,
            66,
            ['Prepare', 'ProgramARM', 'Initialise', 'Aux', 'PowerUp',
             'Output', 'RemoteSw', 'PmSolar', 'OCP', 'CanBus'],
            )
