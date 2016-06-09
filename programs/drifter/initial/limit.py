#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drifter(BM) Initial Program Limits."""

import os

from testlimit import lim_hilo, lim_hilo_delta, lim_hilo_int, lim_string

# Serial port for the PIC.
PIC_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM1'}[os.name]

FORCE_OFFSET = -8
FORCE_THRESHOLD = 160

_COMMON = (
    lim_hilo_delta('Vin', 12.0, 0.1),
    lim_hilo_delta('Vsw', 0, 100),
    lim_hilo_delta('Vref', 0, 100),
    lim_hilo_delta('Vcc', 3.30, 0.07),
    lim_hilo_delta('Isense', -90, 5),
    lim_hilo('3V3', -2.8, -2.5),
    lim_hilo_delta('%ErrorV', 0, 2.24),
    lim_hilo_delta('%CalV', 0, 0.36),
    lim_hilo_delta('%ErrorI', 0, 2.15),
    lim_hilo_delta('%CalI', 0, 0.50),
    # Data reported by the PIC
    lim_hilo_int('PicStatus 0', 0),
    lim_hilo_delta('PicZeroChk', 0, 65.0),
    lim_hilo_delta('PicVin', 12.0, 0.5),
    lim_hilo_delta('PicIsense', -90, 5),
    lim_hilo_delta('PicVfactor', 20000, 1000),
    lim_hilo_delta('PicIfactor', 15000, 1000),
    lim_hilo('PicIoffset', -8.01, -8),
    lim_hilo('PicIthreshold', 160, 160.01),
    )

DATA = _COMMON + (
    lim_string('Software', 'Drifter-5.hex'),
    lim_hilo('0V8', -1.2, -0.4),
    )

DATA_BM = _COMMON + (
    lim_string('Software', 'DrifterBM-2.hex'),
    lim_hilo('0V8', -1.4, -0.6),
    )
