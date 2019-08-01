#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for SX600/750 Initial Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import sx600_750


class SX600Initial(ProgramTestCase):

    """SX600 Initial program test suite."""

    prog_class = sx600_750.Initial
    parameter = '600'
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'share.programmer.ARM',
                'programs.sx600_750.console.Console',
                'programs.sx600_750.arduino.Arduino',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PartDetect':(
                    (sen['Lock'], 10.1), (sen['Part'], 0.5),
                    (sen['R601'], 2001.0), (sen['R602'], 2002.0),
                    (sen['R609'], 2003.0), (sen['R608'], 2004.0),
                    ),
                'Program': (
                    (sen['o5Vsb'], 5.0), (sen['o5Vsbunsw'], (5.0,) * 2),
                    (sen['o3V3'], 3.21), (sen['o8V5Ard'], 8.5),
                    (sen['PriCtl'], 12.34), (sen['pgm5Vsb'], 'OK'),
                    (sen['pgmPwrSw'], 'OK'), (sen['ocpMax'], 'OK'),
                    ),
                'Initialise': ((sen['o5Vsb'], 5.0), (sen['o5Vsbunsw'], 5.0), ),
                'PowerUp': (
                    (sen['ACin'], 240.0), (sen['PriCtl'], 12.34),
                    (sen['o5Vsb'], 5.05), (sen['o12V'], (0.12, 12.34)),
                    (sen['o24V'], (0.24, 24.34)), (sen['ACFAIL'], 5.0),
                    (sen['PGOOD'], 0.123),
                    (sen['PFC'],
                        (432.0, 432.0,     # Initial reading
                         433.0, 433.0,     # After 1st cal
                         433.0, 433.0,     # 2nd reading
                         435.0, 435.0,     # Final value
                        )),
                    (sen['ARM_AcFreq'], 50), (sen['ARM_AcVolt'], 240),
                    (sen['ARM_12V'], 12.180), (sen['ARM_24V'], 24.0),
                    (sen['ARM_SwVer'],
                        '.'.join(
                            self.test_program.cfg._bin_version.split('.')[:2])),
                    (sen['ARM_SwBld'],
                        self.test_program.cfg._bin_version.split('.')[3]),
                    ),
                '5Vsb': ((sen['o5Vsb'], (5.20, 5.15, 5.14, 5.10, )), ),
                '12V': (
                    (sen['o12V'], (12.34, 12.25, 12.10, 12.00, 12.34, )),
                    # OPC SET: Push 32 reads before OCP detected
                    # OCP CHECK: Push 37 reads before OCP detected
                    (sen['o12VinOCP'],
                        ((0.123, ) * 32 + (4.444, )) +
                        ((0.123, ) * 37 + (4.444, ))),
                    (sen['ocp12Unlock'], 'OK'),
                    (sen['ocpStepDn'], ('OK', ) * 35),
                    (sen['ocpLock'], 'OK'),
                    ),
                '24V': (
                    (sen['o24V'], (24.44, 24.33, 24.22, 24.11, 24.24)),
                    # OPC SET: Push 32 reads before OCP detected
                    # OCP CHECK: Push 18 reads before OCP detected
                    (sen['o24VinOCP'],
                        ((0.123, ) * 32 + (4.444, )) +
                        ((0.123, ) * 18 + (4.444, ))),
                    (sen['ocp24Unlock'], 'OK'),
                    (sen['ocpStepDn'], ('OK', ) * 35),
                    (sen['ocpLock'], 'OK'),
                    ),
                'PeakPower': (
                    (sen['o5Vsb'], 5.15), (sen['o12V'], 12.22),
                    (sen['o24V'], 24.44), (sen['PGOOD'], 0.15),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(55, len(result.readings))
        self.assertEqual(
            ['PartDetect', 'Program', 'Initialise', 'PowerUp',
             '5Vsb', '12V', '24V', 'PeakPower'],
            self.tester.ut_steps)


class SX750Initial(ProgramTestCase):

    """SX750 Initial program test suite."""

    prog_class = sx600_750.Initial
    parameter = '750'
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'share.programmer.ARM',
                'programs.sx600_750.console.Console',
                'programs.sx600_750.arduino.Arduino',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PartDetect':(
                    (sen['Lock'], 10.1), (sen['Part'], 0.5),
                    (sen['R601'], 2001.0), (sen['R602'], 2002.0),
                    (sen['R609'], 2003.0), (sen['R608'], 2004.0),
                    ),
                'Program': (
                    (sen['o5Vsb'], 5.0), (sen['o5Vsbunsw'], (5.0,) * 2),
                    (sen['o3V3'], 3.21), (sen['o8V5Ard'], 8.5),
                    (sen['PriCtl'], 12.34), (sen['pgm5Vsb'], 'OK'),
                    (sen['pgmPwrSw'], 'OK'), (sen['ocpMax'], 'OK'),
                    ),
                'Initialise': ((sen['o5Vsb'], 5.0), (sen['o5Vsbunsw'], 5.0), ),
                'PowerUp': (
                    (sen['ACin'], 240.0), (sen['PriCtl'], 12.34),
                    (sen['o5Vsb'], 5.05), (sen['o12V'], (0.12, 12.34)),
                    (sen['o24V'], (0.24, 24.34)), (sen['ACFAIL'], 5.0),
                    (sen['PGOOD'], 0.123),
                    (sen['PFC'],
                        (432.0, 432.0,     # Initial reading
                         433.0, 433.0,     # After 1st cal
                         433.0, 433.0,     # 2nd reading
                         435.0, 435.0,     # Final value
                        )),
                    (sen['ARM_AcFreq'], 50), (sen['ARM_AcVolt'], 240),
                    (sen['ARM_12V'], 12.180), (sen['ARM_24V'], 24.0),
                    (sen['ARM_SwVer'], self.test_program.cfg._bin_version[:3]),
                    (sen['ARM_SwBld'], self.test_program.cfg._bin_version[4:]),
                    ),
                '5Vsb': ((sen['o5Vsb'], (5.20, 5.15, 5.14, 5.10, )), ),
                '12V': (
                    (sen['o12V'], (12.34, 12.25, 12.10, 12.00, 12.34, )),
                    # OPC SET: Push 32 reads before OCP detected
                    # OCP CHECK: Push 37 reads before OCP detected
                    (sen['o12VinOCP'],
                        ((0.123, ) * 32 + (4.444, )) +
                        ((0.123, ) * 37 + (4.444, ))),
                    (sen['ocp12Unlock'], 'OK'),
                    (sen['ocpStepDn'], ('OK', ) * 35),
                    (sen['ocpLock'], 'OK'),
                    ),
                '24V': (
                    (sen['o24V'], (24.44, 24.33, 24.22, 24.11, 24.24)),
                    # OPC SET: Push 32 reads before OCP detected
                    # OCP CHECK: Push 18 reads before OCP detected
                    (sen['o24VinOCP'],
                        ((0.123, ) * 32 + (4.444, )) +
                        ((0.123, ) * 18 + (4.444, ))),
                    (sen['ocp24Unlock'], 'OK'),
                    (sen['ocpStepDn'], ('OK', ) * 35),
                    (sen['ocpLock'], 'OK'),
                    ),
                'PeakPower': (
                    (sen['o5Vsb'], 5.15), (sen['o12V'], 12.22),
                    (sen['o24V'], 24.44), (sen['PGOOD'], 0.15),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(55, len(result.readings))
        self.assertEqual(
            ['PartDetect', 'Program', 'Initialise', 'PowerUp',
             '5Vsb', '12V', '24V', 'PeakPower'],
            self.tester.ut_steps)
