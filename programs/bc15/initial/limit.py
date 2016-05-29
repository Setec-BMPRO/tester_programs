#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 Initial Program Limits."""

import os

from testlimit import (
    lim_lo, lim_hi,
    lim_hilo, lim_hilo_delta, lim_hilo_percent, lim_hilo_int,
    lim_string)

BIN_VERSION = '1.0.13136.1528'      # Software binary version

# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM12'}[os.name]
# ARM software image file
ARM_BIN = 'bc15_{}.bin'.format(BIN_VERSION)

DATA = (
    lim_hilo_delta('ACin', 240.0, 5.0),
    lim_hilo_delta('Vbus', 335.0, 10.0),
    lim_hilo_delta('14Vpri', 14.0, 1.0),
    lim_hilo('12Vs', 11.7, 13.0),
    lim_hilo_delta('5Vs', 5.0, 0.1),
    lim_hilo('3V3', 3.20, 3.35),
    lim_lo('FanOn', 0.5),
    lim_hi('FanOff', 11.0),
    lim_hilo_delta('15Vs', 15.5, 1.0),
    lim_hilo_percent('Vout', 14.40, 5.0),
    lim_hilo_percent('VoutCal', 14.40, 1.0),
    lim_lo('VoutOff', 2.0),
    lim_hilo_percent('OCP', 15.0, 5.0),
    lim_lo('InOCP', 12.0),
    lim_lo('FixtureLock', 20),
    lim_hi('FanShort', 100),
    # Data reported by the ARM
    lim_string('ARM-SwVer', '^{}$'.format(BIN_VERSION.replace('.', r'\.'))),
    lim_hilo_percent('ARM-Vout', 14.40, 5.0),
    lim_hilo('ARM-2amp', 0.5, 3.5),
    # Why 'Lucky'?
    #   The circuit specs are +/- 1.5A, and we hope to be lucky
    #   and get units within +/- 1.0A ...
    lim_hilo_delta('ARM-2amp-Lucky', 2.0, 1.0),
    lim_hilo_delta('ARM-14amp', 14.0, 2.0),
    lim_hilo_int('ARM-switch', 3),
    )
