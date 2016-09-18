#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BatteryCheck Test Program Limits."""

import os
from tester.testlimit import (
    lim_hilo, lim_hilo_delta, lim_hilo_int, lim_lo, lim_string,
    lim_boolean)

ARM_VERSION = '1.7.4080'        # Software binary version
AVR_HEX = 'BatteryCheckSupervisor-2.hex'

# Serial port for the ARM console module.
ARM_CON = {'posix': '/dev/ttyUSB0', 'nt': 'COM1'}[os.name]
# Serial port for the ARM programmer.
ARM_PGM = {'posix': '/dev/ttyUSB1', 'nt': r'\\.\COM2'}[os.name]
# Serial port for the Bluetooth device
BT_PORT = {'posix': '/dev/ttyUSB2', 'nt': 'COM4'}[os.name]

AVRDUDE = {
    'posix': 'avrdude',
    'nt': r'C:\Program Files\AVRdude\avrdude.exe',
    }[os.name]

ARM_BIN = 'BatteryCheckControl_{}.bin'.format(ARM_VERSION)

SHUNT_SCALE = 0.08     # Ishunt * this = DC Source voltage

# Test Limits
DATA = (
    lim_string('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    lim_hilo_delta('3V3', 3.3, 0.1),
    lim_hilo_delta('5VReg', 5.0, 0.1),
    lim_hilo_delta('12VReg', 12.0, 0.1),
    lim_hilo('shunt', -65.0, -60.0),
    lim_lo('Relay', 100),
    lim_hilo_int('PgmAVR', 0),
    lim_hilo_int('DetectBT', 0),
    lim_string('ARM_SwVer', '^{}$'.format(ARM_VERSION.replace('.', r'\.'))),
    lim_hilo_delta('ARM_Volt', 12.0, 0.5),
    lim_hilo('ARM_Curr', -65.0, -60.0),
    lim_hilo_delta('Batt_Curr_Err', 0, 5.0),
    lim_boolean('BTscan', True),
    )
