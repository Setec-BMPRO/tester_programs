#!/usr/bin/env python3
"""UnitTest for GENIUS-II Initial Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import genius2


class _Genius2Initial(ProgramTestCase):
    """GENIUS-II Initial program test suite."""

    prog_class = genius2.Initial

    def _pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "Prepare": (
                    (sen["olock"], 0.0),
                    (sen["ovbatctl"], 13.0),
                    (sen["ovdd"], 5.0),
                    (sen["diode"], 0.25),
                ),
                "Program": ((sen["PicKit"], 0),),
                "Aux": (
                    (sen["ovout"], 13.65),
                    (sen["ovaux"], 13.70),
                ),
                "PowerUp": (
                    (sen["oflyld"], 30.0),
                    (sen["oacin"], 240.0),
                    (sen["ovbus"], 330.0),
                    (sen["ovcc"], 16.0),
                    (sen["ovbat"], 13.0),
                    (sen["ovout"], 13.0),
                    (sen["ovdd"], 5.0),
                    (sen["ovctl"], 12.0),
                ),
                "VoutAdj": (
                    (sen["oAdjVout"], True),
                    (
                        sen["ovout"],
                        (
                            13.65,
                            13.65,
                            13.65,
                        ),
                    ),
                    (sen["ovbatctl"], 13.0),
                    (sen["ovbat"], 13.65),
                    (sen["ovdd"], 5.0),
                ),
                "ShutDown": (
                    (sen["ofan"], (0.0, 13.0)),
                    (sen["ovout"], (13.65, 0.0, 13.65)),
                    (sen["ovcc"], 0.0),
                ),
                "OCP": (
                    (
                        sen["ovout"],
                        (13.5,) * 11 + (13.0,),
                    ),
                    (sen["ovbat"], (self.vbat_ocp, 13.6)),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(29, len(result.readings))
        self.assertEqual(
            ["Prepare", "Program", "Aux", "PowerUp", "VoutAdj", "ShutDown", "OCP"],
            self.tester.ut_steps,
        )


class _Genius2_Initial(_Genius2Initial):
    """GENIUS-II Initial program test suite."""

    parameter = "STD"
    debug = False
    vbat_ocp = 3.6  # Vbat when loaded to 18A

    def test_pass_run(self):
        super()._pass_run()


class _Genius2_H_Initial(_Genius2Initial):
    """GENIUS-II-H Initial program test suite."""

    parameter = "H"
    debug = False
    vbat_ocp = 13.6  # Vbat when loaded to 18A

    def test_pass_run(self):
        super()._pass_run()
