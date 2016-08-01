#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GEN8 Initial Test Program Limits."""

import os

from testlimit import (
    lim_hilo_delta, lim_hilo_percent,
    lim_lo, lim_hi, lim_hilo, lim_string)

BIN_VERSION = '1.4.645'     # Software binary version

# Reading to reading difference for PFC voltage stability
PFC_STABLE = 0.05
# Reading to reading difference for 12V voltage stability
V12_STABLE = 0.005
# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM6'}[os.name]
# Software image filename
ARM_BIN = 'gen8_{0}.bin'.format(BIN_VERSION)

# Test Limits
DATA = (
    lim_lo('PartCheck', 100),    # Microswitches on C106, C107, D2
    lim_hi('FanShort', 20),     # Solder bridge on fan connector
    lim_lo('FixtureLock', 20),
    lim_lo('5Voff', 0.5),
    lim_hilo_percent('5Vset', 5.10, 1.0),
    lim_hilo_percent('5V', 5.10, 2.0),
    lim_lo('12Voff', 0.5),
    lim_hilo_delta('12Vpre', 12.1, 1.0),
    lim_hilo_delta('12Vset', 12.18, 0.01),
    lim_hilo_percent('12V', 12.18, 2.5),
    lim_lo('12V2off', 0.5),
    lim_hilo_delta('12V2pre', 12.0, 1.0),
    lim_hilo('12V2', 11.8146, 12.4845),     # 12.18 +2.5% -3.0%
    lim_lo('24Voff', 0.5),
    lim_hilo_delta('24Vpre', 24.0, 2.0),    # TestEng estimate
    lim_hilo('24V', 22.80, 25.68),          # 24.0 +7% -5%
    lim_lo('VdsQ103', 0.30),
    lim_hilo_percent('3V3', 3.30, 10.0),    # TestEng estimate
    lim_lo('PwrFail', 0.5),
    lim_hilo_delta('InputFuse', 240, 10),
    lim_hilo('12Vpri', 11.4, 17.0),
    lim_hilo_delta('PFCpre', 435, 15),
    lim_hilo_delta('PFCpost1', 440.0, 0.8),
    lim_hilo_delta('PFCpost2', 440.0, 0.8),
    lim_hilo_delta('PFCpost3', 440.0, 0.8),
    lim_hilo_delta('PFCpost4', 440.0, 0.8),
    lim_hilo_delta('PFCpost', 440.0, 0.9),
    lim_hilo_delta('ARM-AcFreq', 50, 10),
    lim_lo('ARM-AcVolt', 300),
    lim_hilo_delta('ARM-5V', 5.0, 1.0),
    lim_hilo_delta('ARM-12V', 12.0, 1.0),
    lim_hilo_delta('ARM-24V', 24.0, 2.0),
    lim_string('SwVer', '^{0}$'.format(BIN_VERSION[:3].replace('.', r'\.'))),
    lim_string('SwBld', '^{0}$'.format(BIN_VERSION[4:])),
    )
