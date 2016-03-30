#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CN101 Initial Program Limits."""

from testlimit import (
    lim_hilo_delta, lim_hilo_percent, lim_hilo_int,
    lim_lo, lim_hi, lim_string, lim_boolean)

# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28


#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    lim_lo('Part', 20.0),
    lim_hilo_delta('Vin', 8.0, 0.5),
    lim_hilo_percent('3V3', 3.30, 3.0),
    lim_lo('AwnOff', 0.5),
    lim_hi('AwnOn', 10.0),
    lim_hilo_int('Program', 0),
    lim_string('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    lim_string('CAN_ID', r'^RRQ,32,0'),
    lim_hilo_int('CAN_BIND', _CAN_BIND),
    lim_string('SwVer', r'^1\.0\.12904\.169$'),
    lim_string('BtMac', r'^[0-F]{12}$'),
    lim_boolean('DetectBT', True),
    lim_hilo_int('Tank', 5),
    lim_boolean('Notify', True),
    )
