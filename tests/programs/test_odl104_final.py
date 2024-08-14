#!/usr/bin/env python3
"""UnitTest for ODL104 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import odl104


class ODL104Final(ProgramTestCase):
    """ODL104 Final program test suite."""

    prog_class = odl104.Final
    parameter = "104"
    debug = False

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_sequence.sensors
        data = {
            UnitTester.key_sen: {  # Tuples of sensor data
                "Bluetooth": (
                    (sen["mirmac"], "001ec030c2be"),
                    (sen["RSSI"], -50),
                ),
            },
        }
        self.tester.ut_load(data, self.test_sequence.sensor_store)
        self.tester.test(self.uuts)
        result = self.tester.ut_result[0]
        self.assertEqual("P", result.letter)
        self.assertEqual(2, len(result.readings))
        self.assertEqual(["Bluetooth"], self.tester.ut_steps)
