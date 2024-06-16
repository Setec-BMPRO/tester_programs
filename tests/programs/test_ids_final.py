#!/usr/bin/env python3
"""UnitTest for IDS500 Final Test program."""

from unittest.mock import patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import ids500


class Ids500Final(ProgramTestCase):
    """IDS500 Final program test suite."""

    prog_class = ids500.Final
    parameter = None
    debug = False

    def setUp(self):
        """Per-Test setup."""
        patcher = patch("programs.ids500.console.Console")
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["tec"], 0.0),
                    (sen["tecvmon"], 0.0),
                    (sen["ldd"], 0.0),
                    (sen["IS_Vmon"], 0.0),
                    (sen["o15v"], 0.0),
                    (sen["o_15v"], 0.0),
                    (sen["o15vp"], 0.0),
                    (sen["o15vpsw"], 0.0),
                    (sen["o5v"], 0.0),
                ),
                "KeySw1": (
                    (sen["tec"], 0.0),
                    (sen["tecvmon"], 0.0),
                    (sen["ldd"], 0.0),
                    (sen["IS_Vmon"], 0.0),
                    (sen["o15v"], 15.0),
                    (sen["o_15v"], -15.0),
                    (sen["o15vp"], 15.0),
                    (sen["o15vpsw"], 0.0),
                    (sen["o5v"], 5.0),
                ),
                "KeySw12": (
                    (sen["tec"], 0.0),
                    (sen["tecvmon"], 0.0),
                    (sen["ldd"], 0.0),
                    (sen["IS_Vmon"], 0.0),
                    (sen["o15v"], 15.0),
                    (sen["o_15v"], -15.0),
                    (sen["o15vp"], 15.0),
                    (sen["o15vpsw"], 15.0),
                    (sen["o5v"], 5.0),
                ),
                "TEC": (
                    (sen["tecvset"], 5.05),
                    (sen["tecvmon"], (0.0, 4.99)),
                    (sen["tec"], (0.0, 15.0, -15.0)),
                    (sen["oYesNoPsu"], True),
                    (sen["oYesNoTecGreen"], True),
                    (sen["oYesNoTecRed"], True),
                ),
                "LDD": (
                    (sen["IS_Vmon"], (2.0,) * 3),
                    (sen["isset"], (0.6, 5.0)),
                    (sen["IS_Iout"], (0.0, 0.601, 5.01)),
                    (sen["LDD_Iout"], (0.0, 0.00602, 0.0502)),
                    (sen["oYesNoLddGreen"], True),
                    (sen["oYesNoLddRed"], True),
                ),
                "Comms": (
                    (sen["oHwRevEntry"], ("07A ",)),
                    (sen["hwrev"], ("I,  2, 07A,Hardware Revision",)),
                    (
                        sen["sernum"],
                        ("I,  3, {0},Serial Number".format(self.uuts[0].sernum),),
                    ),
                ),
                "EmergStop": (
                    (sen["tec"], 0.0),
                    (sen["tecvmon"], 0.0),
                    (sen["ldd"], 0.0),
                    (sen["IS_Vmon"], 0.0),
                    (sen["o15v"], 0.0),
                    (sen["o_15v"], 0.0),
                    (sen["o15vp"], 0.0),
                    (sen["o15vpsw"], 0.0),
                    (sen["o5v"], 0.0),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(67, len(result.readings))
        self.assertEqual(
            ["PowerUp", "KeySw1", "KeySw12", "TEC", "LDD", "Comms", "EmergStop"],
            self.tester.ut_steps,
        )
