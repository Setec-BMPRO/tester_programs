#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BLE2CAN Console driver."""

import share

# Some easier to use short names
Sensor = share.Sensor


class Console(share.SamB11Console):

    """Communications to BLE2CAN console."""

    cmd_data = {
        # LED override command, a bit-mapped field:
        #   b0 = Red, b1 = Green, b2 = Blue
        # Values:
        #   0 = LED off, 1 = LED on
        # "-1" for normal LED operation
        'LEDS': share.ParameterHex(
            'LEDS_OVERRIDE', writeable=True, readable=False),
        }

    def override(self, state=share.Override.normal):
        """Manually override LED operation.

        @param state Override enumeration

        """
        if state == share.Override.normal:
            value = 0xFFFFFFFF
        if state == share.Override.force_on:
            value = 0b111
        if state == share.Override.force_off:
            value = 0b000
        self['LEDS'] = value
