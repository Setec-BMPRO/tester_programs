#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for BP35 Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import bp35


class _BP35Initial(ProgramTestCase):

    """BP35 Initial program test suite."""

    prog_class = bp35.Initial

    def setUp(self):
        """Per-Test setup."""
        mycon = MagicMock(name='MyConsole')
        mycon.ocp_cal.return_value = 1
        mycon.port.readline.return_value = b'RRQ,32,0'
        patcher = patch('programs.bp35.console.Console', return_value=mycon)
        self.addCleanup(patcher.stop)
        patcher.start()
        for target in (
                'share.BackgroundTimer',
                'share.ProgramARM',
                'share.ProgramPIC',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def _arm_loads(self, value):
        """Fill all ARM Load sensors with a value."""
        sen = self.test_program.sensors
        for sensor in sen['arm_loads']:
            sensor.store(value)

    def _pass_run(self, rdg_count, steps):
        """PASS run of the program."""
        sen = self.test_program.sensors
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
                    (sen['arm_swver'], bp35.initial.Initial.arm_version),
                    ),
                'SrSolar': (
                    (sen['vset'], (13.0, 13.0, 13.5)),
                    (sen['solarvin'], 19.55),
                    (sen['arm_sr_alive'], 1),
                    (sen['arm_vout_ov'], 0),
                    (sen['arm_sr_relay'], 1),
                    (sen['arm_sr_error'], 0),
                    (sen['arm_sr_vin'], (19.900, 19.501, )),
                    (sen['arm_iout'], (10.5, 10.1, )),
                    ),
                'Aux': (
                    (sen['vbat'], (12.0, 13.5)),
                    (sen['arm_vaux'], 13.5),
                    (sen['arm_iaux'], 1.1),
                    ),
                'PowerUp': (
                    (sen['acin'], 240.0), (sen['pri12v'], 12.5),
                    (sen['o3v3'], 3.3), (sen['o15vs'], 12.5),
                    (sen['vbat'], 12.8), (sen['vpfc'], (415.0, 415.0), ),
                    (sen['arm_vout_ov'], (0, 0, )),
                    ),
                'Output': (
                    (sen['vload'], 0.0),
                    ),
                'RemoteSw': (
                    (sen['vload'], (12.34, )),
                    (sen['arm_remote'], 1),
                    ),
                'PmSolar': (
                    (sen['arm_pm_alive'], 1),
                    (sen['arm_pm_iout'], (0.55, 0.07, )),
                    ),
                'OCP': (
                    (sen['arm_acv'], 240),
                    (sen['arm_acf'], 50),
                    (sen['arm_sect'], 35),
                    (sen['arm_vout'], 12.80),
                    (sen['arm_fan'], 50),
                    (sen['fan'], (0, 12.0)), (sen['vbat'], 12.8),
                    (sen['arm_ibat'], 4.0),
                    (sen['arm_ibus'], 32.0),
                    (sen['vbat'], (12.8, ) * 20 + (11.0, ), ),
                    (sen['vbat'], (12.8, ) * 20 + (11.0, ), ),
                    ),
                'CanBus': (
                    (sen['arm_canbind'], 1 << 28),
                    ),
                },
            UnitTester.key_call: {      # Callables
                'OCP': (self._arm_loads, 2.0),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
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
        self.tester.ut_load(data, self.test_program.sensor_store)
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
        """PASS run of the SR program."""
        super()._pass_run(
            61,
            ['Prepare', 'ProgramPIC', 'ProgramARM', 'Initialise', 'SrSolar',
             'Aux', 'PowerUp', 'Output', 'RemoteSw', 'OCP', 'CanBus'],
            )


class BP35_HA_Initial(_BP35Initial):

    """BP35xxxHA Initial program test suite."""

    parameter = 'HA'
    debug = False

    def test_pass_run(self):
        """PASS run of the HA program."""
        super()._pass_run(
            61,
            ['Prepare', 'ProgramPIC', 'ProgramARM', 'Initialise', 'SrSolar',
             'Aux', 'PowerUp', 'Output', 'RemoteSw', 'OCP', 'CanBus'],
            )


class BP35_PM_Initial(_BP35Initial):

    """BP35xxxPM Initial program test suite."""

    parameter = 'PM'
    debug = False

    def test_pass_run(self):
        """PASS run of the PM program."""
        super()._pass_run(
            52,
            ['Prepare', 'ProgramARM', 'Initialise', 'Aux', 'PowerUp',
             'Output', 'RemoteSw', 'PmSolar', 'OCP', 'CanBus'],
            )
