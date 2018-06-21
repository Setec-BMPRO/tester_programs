#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for J35 Initial Test program."""

from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import j35


class _J35Initial(ProgramTestCase):

    """J35 Initial program test suite."""

    prog_class = j35.Initial
    sernum = 'A1626010123'

    def setUp(self):
        """Per-Test setup."""
        mycon = MagicMock(name='MyConsole')
        mycon.ocp_cal.return_value = 1
        patcher = patch(
            'programs.j35.console.DirectConsole', return_value=mycon)
        self.addCleanup(patcher.stop)
        patcher.start()
        for target in (
                'share.timers.BackgroundTimer',
                'share.programmer.ARM',
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
                    (sen['olock'], 10.0),
                    (sen['sernum'], self.sernum),
                    (sen['ovfuse'], 12.0),
                    (sen['ovbat'], 12.0),
                    (sen['ovfuse'], 12.0),
                    (sen['o3V3U'], 3.3),
                    ),
                'Initialise': (
                    (sen['sernum'], self.sernum),
                    ),
                'Aux': (
                    (sen['ovbat'], 13.5),
                    (sen['arm_auxv'], 13.5),
                    (sen['arm_auxi'], 1.1),
                    ),
                'Solar': (
                    (sen['oair'], 13.5),
                    (sen['ovbat'], 13.5),
                    ),
                'SolarComp': (
                    (sen['arm_solar_status'], (False, ) * 30 + (True, ), ),
                    (sen['arm_solar_status'], (False, ) * 20 + (True, ), ),
                    ),
                'PowerUp': (
                    (sen['oacin'], 240.0),
                    (sen['ovbus'], 340.0),
                    (sen['o12Vpri'], 12.5),
                    (sen['o3V3'], 3.3),
                    (sen['o15Vs'], 12.5),
                    (sen['ovbat'], (12.8, 12.8, 12.8, )),
                    (sen['ofan'], (0, 12)),
                    (sen['arm_vout_ov'], (0, 0, )),
                    (sen['arm_acv'], 240),
                    (sen['arm_acf'], 50),
                    (sen['arm_sect'], 35),
                    (sen['arm_vout'], 12.80),
                    (sen['arm_fan'], 50),
                    (sen['arm_bati'], 4.0),
                    ),
                'Output': (
                    (sen['ovload'], 0.0),
                    ),
                'RemoteSw': (
                    (sen['ovload'], (12.8, )),
                    ),
                'Load': (
                    (sen['ovbat'], 12.8),
                    (sen['arm_loadset'], 0x5555555),
                    ),
                'OCP': (
                    (sen['ovbat'], (12.8, ) * 20 + (11.0, ), ),
                    (sen['ovbat'], (12.8, ) * 20 + (11.0, ), ),
                    ),
                'CanBus': (
                    (sen['ocanpwr'], 12.5),
                    (sen['arm_canbind'], 1 << 28),
                    ),
                },
            UnitTester.key_call: {      # Callables
                'Initialise':
                    (self.test_program.sensors['arm_swver'].store,
                        self.test_program.cfg.sw_version),
                'Load': (self._arm_loads, 2.0),
                'CanBus':
                    (self.test_program.sensors['TunnelSwVer'].store,
                        self.test_program.cfg.sw_version),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(rdg_count, len(result.readings))
        self.assertEqual(steps, self.tester.ut_steps)


class J35_A_Initial(_J35Initial):

    """J35-A Initial program test suite."""

    parameter = 'A'
    debug = False

    def test_pass_run(self):
        """PASS run of the A program."""
        super()._pass_run(
            44,
            ['Prepare', 'ProgramARM', 'Initialise', 'Aux', 'ManualMode',
             'PowerUp', 'Output', 'RemoteSw', 'Load', 'OCP', 'CanBus']
            )


class J35_B_Initial(_J35Initial):

    """J35-B Initial program test suite."""

    parameter = 'B'
    debug = False

    def test_pass_run(self):
        """PASS run of the B program."""
        super()._pass_run(
            55,
            ['Prepare', 'ProgramARM', 'Initialise', 'Aux', 'Solar',
             'ManualMode', 'SolarComp', 'PowerUp', 'Output', 'RemoteSw',
             'Load', 'OCP', 'CanBus']
            )


class J35_C_Initial(J35_B_Initial):

    """J35-C Initial program test suite."""

    parameter = 'C'
    debug = False

class J35_D_Initial(J35_B_Initial):

    """J35-D Initial program test suite."""

    parameter = 'D'
    debug = False
