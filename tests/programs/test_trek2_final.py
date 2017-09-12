#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for Trek2 Final Test program."""

from ..data_feed import UnitTester, ProgramTestCase
from programs import trek2


class Trek2Final(ProgramTestCase):

    """Trek2 Final program test suite."""

    prog_class = trek2.Final
    parameter = None
    debug = False
    real_tunnel_puts = None

    def _tank_sensors(self, value):
        """Fill all tank sensors with a value."""
        for sen in self.test_program.sensors['otanks']:
            sen.store(value)

    def _tunnel_puts(self, string_data,
             preflush=0, postflush=0,
             priority=False, addprompt=True):
        """Push data into the Tunnel port, ignoring addprompt."""
        self.real_tunnel_puts(string_data, preflush, postflush, priority)

    def test_pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        dev = self.test_program.devices
        dev['trek2'].port.flushInput()      # Flush console input buffer
        dev['tunnel'].port.flushInput()     # Flush Bluetooth input buffer
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Display': (
                    (sen['oSwVer'], (trek2.final.Final.bin_version, )),
                    (sen['oYesNoSeg'], True),
                    (sen['oYesNoBklight'], True),
                    ),
                },
            UnitTester.key_call: {      # Callables
                'Tanks': (
                    self._tank_sensors, (1, 2, 3, 4)
                    ),
                },
            UnitTester.key_con: {       # Tuples of console strings
                'TunnelOpen':(
                    ('0x10000000', '', )
                    ),
                'Display': (
                    ('0x10000000', '', )
                    ),
                'Tanks': (
                    ('', '', )
                    ),
                },
            UnitTester.key_ext: {       # Tuples of extra strings
                'TunnelOpen':(
                    (None, '0 ECHO -> \r\n> ', ) +
                    ('\r\n', ) +
                    ('\r\n', ) +
                    ('0x10000000\r\n', ) +
                    ('\r\n', ) +
                    ('\r\n', ) +
                    ('RRC,32,3,3,0,16,1\r\n', )
                    ),
                },
            }
        self.tester.ut_load(
            data, self.test_program.fifo_push,
            dev['trek2'].puts, self._tunnel_puts)
        self.real_tunnel_puts = dev['tunnel'].port.puts
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)          # Test Result
        self.assertEqual(19, len(result.readings))  # Reading count
        # And did all steps run in turn?
        self.assertEqual(
            ['PowerUp', 'TunnelOpen', 'Display', 'Tanks'],
            self.tester.ut_steps)
