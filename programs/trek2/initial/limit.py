#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Initial Program Limits."""

BIN_VERSION = '1.1.12666.127'      # Software binary version

# Hardware version (Major [1-255], Minor [1-255], Mod [character])
HW_VER = (1, 0, 'A')

from testlimit import (
    lim_hilo_delta, lim_hilo_percent, lim_hilo_int, lim_hilo,
    lim_lo, lim_string, lim_boolean)

# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28

DATA = (
    lim_hilo_delta('Vin', 12.0, 0.5),
    lim_hilo_percent('3V3', 3.3, 3.0),
    lim_lo('BkLghtOff', 0.5),
    lim_hilo('BkLghtOn', 3.465, 4.545),     # 40mA = 4V with 100R (1%)
    lim_hilo_int('Program', 0),
    lim_string('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    lim_string('CAN_RX', r'^RRQ,16,0'),
    lim_hilo_int('CAN_BIND', _CAN_BIND),
    lim_string('SwVer', '^{}$'.format(BIN_VERSION.replace('.', r'\.'))),
    lim_boolean('Notify', True),
    )
