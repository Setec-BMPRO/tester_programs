#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BLE2CAN Console driver."""

import share


class Console(share.console.SamB11):

    """Communications to BLE2CAN console."""

    cmd_data = {
        # LED override command, a bit-mapped field:
        #   b0 = Red, b1 = Green, b2 = Blue
        # Values:
        #   0 = LED off, 1 = LED on
        # "-1" for normal LED operation
        'LEDS': share.console.parameter.Hex(
            'LEDS_OVERRIDE', writeable=True, readable=False),
        'CAN_BIND': share.console.parameter.Hex(
            'STATUS', writeable=True,
            minimum=0, maximum=0xF0000000, mask=(1 << 28)),
        'CAN': share.console.parameter.String(
            'CAN', writeable=True, write_format='"{0} {1}'),
        }

    def override(self, state=share.console.parameter.OverrideTo.normal):
        """Manually override LED operation.

        @param state OverrideTo enumeration

        """
        if state == share.console.parameter.OverrideTo.normal:
            value = 0xFFFFFFFF
        if state == share.console.parameter.OverrideTo.force_on:
            value = 0b111
        if state == share.console.parameter.OverrideTo.force_off:
            value = 0b000
        self['LEDS'] = value
