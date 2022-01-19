#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for AsDisplay Test program."""

from unittest.mock import MagicMock, patch

from ..data_feed import UnitTester, ProgramTestCase
from programs import asdisplay


class SerialResponder():

    """Feed data bytes to serial.Serial.read.side_effect of a Mock."""

    def __init__(self):
        """Create instance."""
        self.str_buffer = []

    def append(self, str):
        """Append a string to the response list."""
        self.str_buffer.append(str)

    def bytes_generator(self):
        """Return generator of the strings as bytes of length 1."""
        for a_str in self.str_buffer:
            for a_chr in a_str:
                yield(a_chr.encode())


class ASDisplayInitial(ProgramTestCase):
    """ASDisplay Initial program test suite."""

    prog_class = asdisplay.Initial
    debug = False
    sernum = 'A2150080001'

    def setUp(self):
        for target in (
                'share.programmer.ARM',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        # Patch the serial port with the expected responses
        patcher = patch('serial.Serial', return_value=self.mycon())
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def mycon(self):
        """ Mock the console and create responses (side_effect)
            to return a sequence of byte values.
        """
        con = MagicMock(name='console')
        # Console response strings
        cmd_set_led = 'set_led '
        on      = '0xFF,0xFF,0xFF,0xFF,0xFF'
        default = '0x01,0x00,0x00,0x00,0x00'
        cmd_prompt_resp_ok = '\rOK\r\n>'
        cmd_tank_levs = (
            '0x00,0x00,0x00,0x00',
            '0x01,0x01,0x01,0x01',
            '0x02,0x02,0x02,0x02',
            '0x03,0x03,0x03,0x03',
            '0x04,0x04,0x04,0x04',
            )
        resp = SerialResponder()
        resp.append('testmode\rOK\r\n>')
        resp.append(cmd_set_led + on + cmd_prompt_resp_ok)
        resp.append(cmd_set_led + default + cmd_prompt_resp_ok)
        for lev in cmd_tank_levs:
            resp.append('read_tank_level\r{0}\r\n>'.format(lev))
        con.read.side_effect = resp.bytes_generator()
        return con

    def test_pass(self):
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {
                'PowerUp': (
                    (sen['SnEntry'], self.sernum),
                    (sen['Vin'], 12.0),
                    (sen['3V3'], 3.3),
                    (sen['5V0'], 5.0),
                    ),
                'Testmode': (
                    (sen['test_mode'], 'OK'),
                    ),
                'LEDCheck': (
                    (sen['leds_on'], 'OK'),
                    (sen['LEDsOnCheck'], True),
                    (sen['leds_off'], 'OK'),
                    ),
                'TankSense': (
                    (sen['tank_sensor'], ((0, ) * 4,
                                          (1, ) * 4,
                                          (2, ) * 4,
                                          (3, ) * 4,
                                          (4, ) * 4,
                                          )),
                    ),
                }}
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result[0]
        self.assertEqual('P', result.code)
        self.assertEqual(28, len(result.readings))
        self.assertEqual(
            ['PowerUp', 'PgmARM', 'Testmode',
             'LEDCheck', 'TankSense'],
            self.tester.ut_steps)
