#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trek2 Final Program Limits."""

from testlimit import (
    lim_hilo_delta, lim_hilo_int, lim_boolean)

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    lim_hilo_delta('Vin', 12.0, 0.5),
    lim_boolean('Notify', True),
    lim_hilo_int('Tank1', 1),
    lim_hilo_int('Tank2', 2),
    lim_hilo_int('Tank3', 3),
    lim_hilo_int('Tank4', 4),
    )
