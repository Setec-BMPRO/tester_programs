#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for IDS500 Initial Main Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import ids500


class Ids500IniMain(ProgramTestCase):

    """IDS500 Initial Main program test suite."""

    prog_class = ids500.InitialMain
    parameter = None
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "PowerUp": (
                    (sen["lock"], 10.0),
                    (sen["vbus"], 340.0),
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
                    (sen["vbus"], 405.0),
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
                    (sen["tec"], (0.0, -15.0, 15.0)),
                    (sen["oYesNoPsu"], True),
                    (sen["oYesNoTecGreen"], True),
                    (sen["oYesNoTecRed"], True),
                ),
                "LDD": (
                    (sen["ldd"], (2.0,) * 3),
                    (sen["IS_Iout"], (0.0, 0.601, 5.01)),
                    (sen["IS_Vmon"], (2.0,) * 3),
                    (sen["isset"], (0.6, 5.0)),
                    (sen["LDD_Iout"], (0.0, 0.00602, 0.0502)),
                    (sen["oYesNoLddGreen"], True),
                    (sen["oYesNoLddRed"], True),
                ),
                "OCP": (
                    (
                        sen["o5v"],
                        (5.0,) * 23 + (3.9,),
                    ),
                    (
                        sen["o15vp"],
                        (15.0,) * 23 + (11.9,),
                    ),
                    (
                        sen["tec"],
                        (-15.0,) * 23 + (-11.9,),
                    ),
                    (sen["o15vp"], (15.0,) * 3),
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
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(("UUT1",))
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.code)
        self.assertEqual(79, len(result.readings))
        self.assertEqual(
            ["PowerUp", "KeySw1", "KeySw12", "TEC", "LDD", "OCP", "EmergStop"],
            self.tester.ut_steps,
        )
