#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CMR-SBP ALL Test Program Limits."""

import os
from tester.testlimit import (
    lim_hilo, lim_hilo_delta, lim_hilo_int, lim_lo, lim_string, lim_boolean)

PIC_HEX = 'CMR-SBP-9.hex'

# Serial port for the EV2200.
EV_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM1'}[os.name]
# Serial port for the CMR.
CMR_PORT = {'posix': '/dev/ttyUSB1', 'nt': 'COM2'}[os.name]

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    lim_hilo_delta('Vbat', 12.0, 0.10),
    lim_hilo('VbatCharge', 11.8, 12.5),
    lim_hilo_delta('Vcc', 3.3, 0.2),
    lim_hilo('VErase', 4.8, 5.05),
    lim_lo('IStart', 0.02),
    lim_hilo('Vchge', 12.8, 15.0),
    # 2.0A +/- 10mA
    lim_hilo_delta('Ibat', -2.00, 0.01),
    lim_lo('Final Not Connected', 1.0),
    lim_hilo_delta('SenseRes', 250, 30),
    lim_hilo_delta('Halfcell', 110, 10),
    lim_hilo_delta('VChgeOn', 350, 50),
    lim_hilo_delta('ErrVUncal', 0.0, 0.5),
    lim_hilo_delta('ErrVCal', 0.0, 0.03),
    lim_hilo_delta('ErrIUncal', 0.0, 0.060),
    lim_hilo_delta('ErrICal', 0.0, 0.015),
    # 298K nominal +/- 2.5K in Kelvin (25C +/- 2.5C in Celsius).
    lim_hilo_delta('BQ-Temp', 300, 4.5),
    # SerialDate
    lim_string('SerNum', r'^[9A-HJ-NP-V][1-9A-C][0-9]{5}F[0-9]{4}$'),
    )

_FIN_DATA = (   # Shared Final Test limits
    lim_hilo('VbatIn', 12.8, 15.0),
    lim_hilo_delta('ErrV', 0.0, 0.03),
    lim_hilo('CycleCnt', 0.5, 20.5),
    lim_boolean('RelrnFlg', False),
    lim_hilo_int('RotarySw', 256),
    lim_hilo_delta('Halfcell', 400, 50),
    lim_boolean('VFCcalStatus', True),
    lim_string('SerNumChk', ''),
    )

DATA_8D = _FIN_DATA + (
    lim_hilo('SenseRes', 39.0, 91.0),
    lim_hilo('Capacity', 6400, 11000),
    lim_hilo_delta('StateOfCharge', 100.0, 10.5),
    lim_string('SerNum', r'^[9A-HJ-NP-V][1-9A-C](36861|40214)F[0-9]{4}$'),
    )

DATA_13F = _FIN_DATA + (
    lim_hilo('SenseRes', 221.0, 280.0),
    lim_hilo('Capacity', 11000, 15000),
    lim_hilo_delta('StateOfCharge', 100.0, 10.5),
    lim_string('SerNum', r'^[9A-HJ-NP-V][1-9A-C](36862|40166)F[0-9]{4}$'),
    )

DATA_17L = _FIN_DATA + (
    lim_hilo('SenseRes', 400.0, 460.0),
    lim_hilo('Capacity', 15500, 20000),
    lim_lo('StateOfCharge', 30.0),
    lim_string('SerNum', r'^[9A-HJ-NP-V][1-9A-C]403(15|23)F[0-9]{4}$'),
    )
