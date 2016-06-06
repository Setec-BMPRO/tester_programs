#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Initial Program Limits."""

import os

from testlimit import (
    lim_hilo_delta, lim_hilo_percent, lim_hilo_int, lim_hilo,
    lim_lo, lim_string, lim_boolean)

BIN_VERSION = '1.2.13347.138'   # Software binary version

# Hardware version (Major [1-255], Minor [1-255], Mod [character])
HW_VER = (2, 0, 'E')

# Serial port for the Trek2 in the fixture. Used for the CAN Tunnel port
CAN_PORT = {'posix': '/dev/ttyUSB1', 'nt': 'COM11'}[os.name]
# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM10'}[os.name]
# Software image filename
ARM_BIN = 'Trek2_{}.bin'.format(BIN_VERSION)
# CAN echo request messages
CAN_ECHO = 'TQQ,16,0'
# Input voltage to power the unit
VIN_SET = 12.75

# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28

DATA = (
    lim_hilo_delta('Vin', 12.0, 0.5),
    lim_hilo_percent('3V3', 3.3, 3.0),
    lim_lo('BkLghtOff', 0.5),
    lim_hilo('BkLghtOn', 3.465, 4.545),     # 40mA = 4V with 100R (1%)
    lim_string('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    lim_string('CAN_RX', r'^RRQ,16,0'),
    lim_hilo_int('CAN_BIND', _CAN_BIND),
    lim_string('SwVer', '^{}$'.format(BIN_VERSION.replace('.', r'\.'))),
    lim_boolean('Notify', True),
    )
