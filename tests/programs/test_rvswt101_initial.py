#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for RVSWT101 Initial Test program."""

import unittest
from unittest.mock import Mock, patch

import setec

from ..data_feed import UnitTester, ProgramTestCase
from programs import rvswt101


class RVSWT101Initial(ProgramTestCase):

    """RVSWT101 Initial program test suite."""

    prog_class = rvswt101.Initial
    per_panel = 1
    parameter = '4gp1'
    debug = False

    def setUp(self):
        """Per-Test setup."""
        for target in (
                'share.bluetooth.RaspberryBluetooth',
                'share.bluetooth.SerialToMAC',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        mycon = Mock(name='MyConsole')
        mycon.get_mac.return_value = '001ec030c2be'
        patcher = patch(
            'programs.rvswt101.console.Console', return_value=mycon)
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['vin'], 3.3),
                    ),
                'ProgramTest': (
                    (sen['JLink'], 0),
                    (sen['mirmac'], 'ec70225e3dba'),
                    (sen['mirscan'], True),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(
            tuple(setec.UUT.from_sernum('A000000{0:04}'.format(uut))
                for uut in range(1, self.per_panel + 1)))
        for res in self.tester.ut_result:
            self.assertEqual('P', res.code)
            self.assertEqual(4, len(res.readings))
        self.assertEqual(
            ['PowerUp', 'ProgramTest'],
            self.tester.ut_steps)


class Fixture(unittest.TestCase):

    """RVSWT101 Initial Fixture test suite."""

    relay_count = 2

    def setUp(self):
        """Per-Test setup."""
        self.dcs = Mock(name='DCS')
        self.rla = ['Dummy']    # Dummy [0] entry
        for cnt in range(self.relay_count):
            self.rla.append(Mock(name='RLA{0}'.format(cnt + 1)))
        self.fxt = rvswt101.initial.Fixture(self.dcs, self.rla)

    def _reset_mocks(self):
        """Reset all my Mocks."""
        self.dcs.reset_mock()
        for cnt in range(self.relay_count):
            self.rla[cnt + 1].reset_mock()

    def test_program_mode(self):
        """Program mode."""
        self.dcs.output.assert_called_once_with(0.0, output=False)
        self.assertEqual(self.fxt.state, rvswt101.initial.FixtureState.idle)
        self._reset_mocks()
        # Connect a position
        mypos1 = 1
        self.fxt.connect(mypos1)
        self.assertEqual(self.fxt.state, rvswt101.initial.FixtureState.program)
        self.dcs.output.assert_called_once_with(
            rvswt101.initial.Fixture.dcs_program,
            output=True,
            delay=rvswt101.initial.Fixture.dcs_delay)
        self.rla[mypos1].set_on.assert_called_once()
        self._reset_mocks()
        # Connect another position
        mypos2 = 2
        self.fxt.connect(mypos2)
        self.assertEqual(self.fxt.state, rvswt101.initial.FixtureState.program)
        self.dcs.output.assert_not_called()
        self.rla[mypos1].set_off.assert_called_once()
        self.rla[mypos2].set_on.assert_called_once()
        self._reset_mocks()
        # Release a button in program mode (not allowed)
        with self.assertRaises(rvswt101.initial.FixtureError):
            self.fxt.release()
        # Swap to BUTTON mode
        self.fxt.press(mypos1)
        self.assertEqual(self.fxt.state, rvswt101.initial.FixtureState.button)
        self.dcs.output.assert_called_once_with(
            rvswt101.initial.Fixture.dcs_button,
            output=True,
            delay=rvswt101.initial.Fixture.dcs_delay)
        self.rla[mypos2].set_off.assert_called_once()
        self.rla[mypos1].set_on.assert_called_once()
        self._reset_mocks()

    def test_button_mode(self):
        """Button mode."""
        self.dcs.output.assert_called_once_with(0.0, output=False)
        self.assertEqual(self.fxt.state, rvswt101.initial.FixtureState.idle)
        self._reset_mocks()
        # Press a position
        mypos1 = 1
        self.fxt.press(mypos1)
        self.assertEqual(self.fxt.state, rvswt101.initial.FixtureState.button)
        self.dcs.output.assert_called_once_with(
            rvswt101.initial.Fixture.dcs_button,
            output=True,
            delay=rvswt101.initial.Fixture.dcs_delay)
        self.rla[mypos1].set_on.assert_called_once()
        self._reset_mocks()
        # Press another position (not allowed)
        mypos2 = 2
        with self.assertRaises(rvswt101.initial.FixtureError):
            self.fxt.press(mypos2)
        # Release the position
        self.fxt.release()
        self.assertEqual(self.fxt.state, rvswt101.initial.FixtureState.button)
        self.rla[mypos1].set_off.assert_called_once()
        self._reset_mocks()
        # Press another position
        mypos2 = 2
        self.fxt.press(mypos2)
        self.assertEqual(self.fxt.state, rvswt101.initial.FixtureState.button)
        self.rla[mypos2].set_on.assert_called_once()
        self._reset_mocks()
        # Swap to PROGRAM mode
        self.fxt.connect(mypos1)
        self.assertEqual(self.fxt.state, rvswt101.initial.FixtureState.program)
        self.dcs.output.assert_called_once_with(
            rvswt101.initial.Fixture.dcs_program,
            output=True,
            delay=rvswt101.initial.Fixture.dcs_delay)
        self.rla[mypos2].set_off.assert_called_once()
        self.rla[mypos1].set_on.assert_called_once()
        self._reset_mocks()
