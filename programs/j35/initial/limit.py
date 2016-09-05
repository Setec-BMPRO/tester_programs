#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""J35 Initial Program Limits."""

import os

from testlimit import (
    lim_hilo, lim_hilo_delta, lim_lo, lim_boolean, lim_string, lim_hilo_int)

ARM_VERSION = '1.0.13788.904'      # ARM versions
ARM_HW_VER = (1, 0, 'A')

# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM16'}[os.name]
# ARM software image file
ARM_BIN = 'j35_{}.bin'.format(ARM_VERSION)
# CAN echo request messages
CAN_ECHO = 'TQQ,36,0'
# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28

DATA = (
    lim_hilo_delta('ACin', 240.0, 5.0),
    lim_hilo('Vbus', 335.0, 345.0),
    lim_hilo('12Vpri', 11.5, 13.0),
    lim_hilo('Vload', 12.0, 12.9),
    lim_lo('VloadOff', 0.5),
    lim_hilo_delta('Vaux', 13.5, 0.5),
    lim_hilo_delta('Vair', 13.5, 0.5),
    lim_hilo_delta('VbatIn', 12.0, 0.5),
    lim_hilo_delta('Vbat', 12.8, 0.2),
    lim_hilo_delta('Vout', 12.8, 0.2),
    lim_hilo_delta('3V3U', 3.30, 0.05),
    lim_hilo_delta('3V3', 3.30, 0.05),
    lim_hilo('15Vs', 11.5, 13.0),
    lim_hilo_delta('FanOn', 12.5, 0.5),
    lim_lo('FanOff', 0.5),
    lim_string('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    lim_string('ARM-SwVer', '^{}$'.format(ARM_VERSION.replace('.', r'\.'))),
    lim_hilo_delta('ARM-AuxV', 13.5, 0.37),
    lim_hilo('ARM-AuxI', 0.0, 1.5),
    lim_hilo_int('Vout_OV', 0),     # Over-voltage not triggered
    lim_hilo_delta('ARM-AcV', 240.0, 10.0),
    lim_hilo_delta('ARM-AcF', 50.0, 1.0),
    lim_hilo('ARM-SecT', 8.0, 70.0),
    lim_hilo_delta('ARM-Vout', 12.45, 0.45),
    lim_hilo('ARM-Fan', 0, 100),
    lim_hilo_delta('ARM-BattI', 4.0, 1.0),
    lim_hilo('ARM-LoadI', 0.1, 3.0),
    lim_hilo_delta('CanPwr', 12.0, 1.0),
    lim_string('CAN_RX', r'^RRQ,36,0'),
    lim_hilo_int('CAN_BIND', _CAN_BIND),
    lim_hilo('OCP', 6.0, 9.0),
    lim_lo('InOCP', 11.6),
    lim_lo('FixtureLock', 20),
    lim_boolean('Notify', True),
    )
