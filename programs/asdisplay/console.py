#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021 SETEC Pty Ltd
"""ASDisplay Test Program."""

import re

import setec

import share


class Console(share.console.BadUart):

    """ASDisplay console."""

    # Console command prompt. Signals the end of response data.
    cmd_prompt = b'>'
    tank_level_key = 'TANK_LEVEL'

    # Console commands
    parameter = share.console.parameter
    set_led_cmd = 'set_led '
    cmd_leds_on = set_led_cmd + '0xFF,0xFF,0xFF,0xFF,0xFF'
    cmd_leds_off = set_led_cmd + '0x01,0x00,0x00,0x00,0x00'

    cmd_data = {
        # Writable values
        # All led's on:  0xFF,0xFF,0xFF,0xFF,0xFF'
        # Pwr led only: 0x01,0x00,0x00,0x00,0x00'
        'ALL_LEDS_ON': parameter.String(
            cmd_leds_on, writeable=True,
            write_format='{1} {0}', read_format='{0}'),
        'LEDS_OFF': parameter.String(
            cmd_leds_off, writeable=True,
            write_format='{1} {0}', read_format='{0}'),
        # Action commands
        'TESTMODE': parameter.String(
            'testmode', writeable=True,
            write_format='{1} {0}', read_format='{0}'),
        # Readable values
        tank_level_key: parameter.String(
            'read_tank_level',
            write_format='{1} {0}', read_format='{0}'),
        }

    def configure(self, key):

        self.reading_tanks = (key == self.tank_level_key)
        super().configure(key)

    def action(self, command=None, delay=0, expected=0):
        """ Provide a custom action when reading tanks
            Manupilate the response to be in a (1, 1, 1, 1) format

            > read_tank_level
            0x00,0x00,0x00,0x00  # Tank empty, all relays off
            0x01,0x01,0x01,0x01
            0x02,0x02,0x02,0x02
            0x03,0x03,0x03,0x03
            0x04,0x04,0x04,0x04  # Tank full, all relays on
        """
        if self.reading_tanks:
            reply = None
            try:
                if command:
                    self.last_cmd = command
                    self.port.reset_input_buffer()
                    self._write_command(command)
                if delay:
                    time.sleep(delay)

                response = self._read_response(expected)
                reply = tuple(int(val, 16)
                        for val in response.split(','))
            except Error as err:
                if self.measurement_fail_on_error:
                    # Read any more waiting data (a possible hard-fault message)
                    port_timeout = self.port.timeout
                    self.port.timeout = 0.1
                    data = self.port.read(1000)
                    self.port.timeout = port_timeout
                    if len(data) > 0:
                        self._logger.error('Console Error extra data: %s', data)
                    # Generate a Measurement failure
                    self._logger.debug('Caught Error: "%s"', err)
                    comms = tester.Measurement(
                        tester.LimitRegExp('Action', 'ok', doc='Command succeeded'),
                        tester.sensor.MirrorReadingString())
                    comms.sensor.store(str(err))
                    comms.measure()   # Generates a test FAIL result
                else:
                    raise
            return reply

        else:
            return super().action(command, delay, expected)






