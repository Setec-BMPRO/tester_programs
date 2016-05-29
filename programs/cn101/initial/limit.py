#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CN101 Initial Program Limits."""

import os

from testlimit import (
    lim_hilo_delta, lim_hilo_percent, lim_hilo_int,
    lim_lo, lim_hi, lim_string, lim_boolean)

BIN_VERSION = '1.0.12904.169'      # Software binary version
HW_VER = (1, 0, 'A')

# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB1', 'nt': 'COM15'}[os.name]
# ARM software image file
ARM_BIN = 'cn101_{}.bin'.format(BIN_VERSION)
# Serial port for the Bluetooth module.
BLE_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM14'}[os.name]
# Serial port for the Trek2 as the CAN Bus interface.
#_CAN_PORT = {'posix': '/dev/ttyUSB2', 'nt': 'COM13'}[os.name]
# CAN echo request messages
CAN_ECHO = 'TQQ,32,0'

# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28

DATA = (
    lim_lo('Part', 20.0),
    lim_hilo_delta('Vin', 8.0, 0.5),
    lim_hilo_percent('3V3', 3.30, 3.0),
    lim_lo('AwnOff', 0.5),
    lim_hi('AwnOn', 10.0),
    lim_string('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    lim_string('CAN_RX', r'^RRQ,32,0'),
    lim_hilo_int('CAN_BIND', _CAN_BIND),
    lim_string('SwVer', '^{}$'.format(BIN_VERSION.replace('.', r'\.'))),
    lim_string('BtMac', r'^[0-F]{12}$'),
    lim_boolean('DetectBT', True),
    lim_hilo_int('Tank', 5),
    lim_boolean('Notify', True),
    )
