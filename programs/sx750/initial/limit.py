#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Initial Test Program Limits."""

import os

from testlimit import (
    lim_hilo_delta, lim_hilo_percent, lim_hilo, lim_hilo_int,
    lim_lo, lim_hi, lim_string
    )

BIN_VERSION = '3.1.2118'        # Software versions
PIC_HEX1 = 'sx750_pic5Vsb_1.hex'
PIC_HEX2 = 'sx750_picPwrSw_2.hex'

# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM1'}[os.name]
# Serial port for the Arduino.
ARDUINO_PORT = {'posix': '/dev/ttyACM0', 'nt': 'COM5'}[os.name]
# Software image filenames
ARM_BIN = 'sx750_arm_{}.bin'.format(BIN_VERSION)

# Reading to reading difference for PFC voltage stability
PFC_STABLE = 0.05

# Test Limits
DATA = (
    lim_hilo('8.5V Arduino', 8.1, 8.9),
    lim_lo('5Voff', 0.5),
    lim_hilo('5Vext', 5.5, 5.9),
    lim_hilo_percent('5Vsb_set', 5.10, 1.5),
    lim_hilo_percent('5Vsb', 5.10, 5.5),
    lim_lo('5Vsb_reg', 3.0),        # Load Reg < 3.0%
    lim_lo('12Voff', 0.5),
    lim_hilo_percent('12V_set', 12.25, 2.0),
    lim_hilo_percent('12V', 12.25, 8.0),
    lim_lo('12V_reg', 3.0),         # Load Reg < 3.0%
    lim_hilo('12V_ocp', 4, 63),     # Digital Pot setting - counts up from MIN
    lim_hi('12V_inOCP', 4.0),       # Detect OCP when TP405 > 4V
    lim_hilo('12V_OCPchk', 36.2, 37.0),
    lim_lo('24Voff', 0.5),
    lim_hilo_percent('24V_set', 24.13, 2.0),
    lim_hilo_percent('24V', 24.13, 10.5),
    lim_lo('24V_reg', 7.5),         # Load Reg < 7.5%
    lim_hilo('24V_ocp', 4, 63),     # Digital Pot setting - counts up from MIN
    lim_hi('24V_inOCP', 4.0),       # Detect OCP when TP404 > 4V
    lim_hilo('24V_OCPchk', 18.1, 18.5),
    lim_hilo('PriCtl', 11.40, 17.0),
    lim_lo('PGOOD', 0.5),
    lim_hilo_delta('ACFAIL', 5.0, 0.5),
    lim_lo('ACOK', 0.5),
    lim_hilo_delta('3V3', 3.3, 0.1),
    lim_hilo_delta('ACin', 240, 10),
    lim_hilo_delta('PFCpre', 420, 20),
    lim_hilo_delta('PFCpost', 435, 1.0),
    lim_hilo_delta('OCP12pre', 36, 2),
    lim_hilo('OCP12post', 35.7, 36.5),
    lim_lo('OCP12step', 0.116),
    lim_hilo_delta('OCP24pre', 18, 1),
    lim_hilo_delta('OCP24post', 18.2, 0.1),
    lim_lo('OCP24step', 0.058),
    # Data reported by the ARM
    lim_lo('ARM-AcFreq', 999),
    lim_lo('ARM-AcVolt', 999),
    lim_lo('ARM-12V', 999),
    lim_lo('ARM-24V', 999),
    lim_string(
        'ARM-SwVer', '^{}$'.format(BIN_VERSION[:3].replace('.', r'\.'))),
    lim_string('ARM-SwBld', '^{}$'.format(BIN_VERSION[4:])),
    #
    lim_lo('FixtureLock', 20),
    lim_lo('PartCheck', 20),            # Microswitches on C612, C613, D404
    lim_hilo('Snubber', 1000, 3000),    # Snubbing resistors
    lim_string('Reply', '^OK$'),
    lim_hilo_int('Program', 0)
    )
