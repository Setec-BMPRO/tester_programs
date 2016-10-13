#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RVVIEW Initial Program Limits."""

import os
from tester.testlimit import (
    lim_hilo_percent, lim_hilo_int, lim_hilo,
    lim_lo, lim_string, lim_boolean)

BIN_VERSION = '1.0.13893.979'   # Software binary version
# Hardware version (Major [1-255], Minor [1-255], Mod [character])
ARM_HW_VER = (4, 0, 'A')

# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM16'}[os.name]
# Software image filename
ARM_BIN = 'RvView_{}.bin'.format(BIN_VERSION)
# CAN echo request messages
CAN_ECHO = 'TQQ,32,0'
# Input voltage to power the unit
VIN_SET = 8.1

# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28

DATA = (
    lim_hilo('Vin', 7.0, 8.0),
    lim_hilo_percent('3V3', 3.3, 3.0),
    lim_lo('BkLghtOff', 0.5),
    lim_hilo('BkLghtOn', 3.465, 4.545),     # 40mA = 4V with 100R (1%)
    lim_string('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    lim_string('SwVer', '^{}$'.format(BIN_VERSION.replace('.', r'\.'))),
    lim_string('CAN_RX', r'^RRQ,32,0'),
    lim_hilo_int('CAN_BIND', _CAN_BIND),
    lim_boolean('Notify', True),
    )
