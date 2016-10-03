#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""J35 Final Program Limits."""

from tester.testlimit import lim_hilo_delta, lim_lo, lim_hi, lim_hilo

LOAD_CURRENT = 28.0
LOAD_COUNT = 14

DATA = (
    lim_lo('FanOff', 1.0),
    lim_hi('FanOn', 10.0),
    lim_hilo_delta('Vout', 12.8, 0.2),
    lim_hilo_delta('Vload', 12.8, 0.2),
    lim_hilo('OCP', 35.0, 42.0),
    lim_lo('InOCP', 11.6),
    )
