#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""J35 Final Program Limits."""

from tester.testlimit import (
    lim_hilo_delta, lim_lo, lim_hi, lim_hilo, lim_hilo_percent, lim_boolean)

COUNT_A = 7
CURRENT_A = 14.0
COUNT_BC = 14
CURRENT_BC = 28.0

_BASE_DATA = (
    lim_lo('FanOff', 1.0),
    lim_hi('FanOn', 10.0),
    lim_hilo_delta('Vout', 12.8, 0.2),
    lim_hilo_percent('Vload', 12.8, 5),
    lim_lo('InOCP', 11.6),
    )

DATA_A = _BASE_DATA + (
    lim_lo('LOAD_COUNT', COUNT_A),
    lim_lo('LOAD_CURRENT', CURRENT_A),
    lim_hilo('OCP', 20.0, 25.0),
    )

DATA_B = _BASE_DATA + (
    lim_lo('LOAD_COUNT', COUNT_BC),
    lim_lo('LOAD_CURRENT', CURRENT_BC),
    lim_hilo('OCP', 35.0, 42.0),
    lim_boolean('J35C', False),
    )

DATA_C = _BASE_DATA + (
    lim_lo('LOAD_COUNT', COUNT_BC),
    lim_lo('LOAD_CURRENT', CURRENT_BC),
    lim_hilo('OCP', 35.0, 42.0),
    lim_boolean('J35C', True),
    )
