#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drifter(BM) Final Program Limits."""

from tester.testlimit import lim_hilo_delta, lim_lo, lim_hi, lim_boolean

# Tuple ( Tuple (name, identity, low, high, string, boolean))
_COMMON = (
    lim_lo('SwOff', 1.0),
    lim_hi('SwOn', 10.0),
    lim_hilo_delta('USB5V', 5.00, 0.25),
    lim_boolean('Notify', True),
    )

DATA = _COMMON
DATA_BM = _COMMON
