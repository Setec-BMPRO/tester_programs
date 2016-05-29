#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Initial Main Program Limits."""

from testlimit import lim_lo, lim_hilo_delta

DATA = (
    lim_hilo_delta('Vbus', 340.0, 10.0),
    lim_hilo_delta('Off', 0, 1.5),
    lim_lo('FixtureLock', 20),
    )
