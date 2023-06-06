#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2021 SETEC Pty Ltd
"""ASDisplay Test Program."""

import time

import share


class Console(share.console.BadUart):

    """ASDisplay console."""

    # Console command prompt. Signals the end of response data.
    cmd_prompt = b">"
    tank_level_key = "TANK_LEVEL"
    reading_tanks = False

    # Console commands
    parameter = share.console.parameter
    set_led_cmd = "set_led "
    cmd_leds_on = set_led_cmd + "0xFF,0xFF,0xFF,0xFF,0xFF"
    cmd_leds_off = set_led_cmd + "0x01,0x00,0x00,0x00,0x00"

    cmd_data = {
        # Writable values
        # All led's on:  0xFF,0xFF,0xFF,0xFF,0xFF'
        # Pwr led only: 0x01,0x00,0x00,0x00,0x00'
        "ALL_LEDS_ON": parameter.String(
            cmd_leds_on, writeable=True, write_format="{1} {0}", read_format="{0}"
        ),
        "LEDS_OFF": parameter.String(
            cmd_leds_off, writeable=True, write_format="{1} {0}", read_format="{0}"
        ),
        # Action commands
        "TESTMODE": parameter.String(
            "testmode", writeable=True, write_format="{1} {0}", read_format="{0}"
        ),
        # Readable values
        tank_level_key: parameter.String(
            "read_tank_level", write_format="{1} {0}", read_format="{0}"
        ),
    }

    def open(self):
        self.port.baudrate = 19200
        self.port.timeout = 5
        super().open()

    def reset(self):
        self.port.dtr = self.port.rts = False
        self.port.dtr = True
        self.port.reset_input_buffer()
        self.port.dtr = False
        time.sleep(1)

    def configure(self, key):
        """Remember if we are reading tank levels."""
        self.reading_tanks = key == self.tank_level_key
        super().configure(key)

    def action(self, command=None, delay=0, expected=0):
        """Provide a custom action when reading tanks.

        Manipulate the response to be in a (1, 1, 1, 1) format

        > read_tank_level
        0x00,0x00,0x00,0x00  # Tank empty, all relays off
        0x01,0x01,0x01,0x01
        0x02,0x02,0x02,0x02
        0x03,0x03,0x03,0x03
        0x04,0x04,0x04,0x04  # Tank full, all relays on

        """
        reply = super().action(command, delay, expected)
        if self.reading_tanks:
            reply = tuple(int(val, 16) for val in reply.split(","))
        return reply
