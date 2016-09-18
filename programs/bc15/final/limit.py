#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BC15 Final Program Limits."""

from tester.testlimit import lim_hilo_delta, lim_hilo_percent, lim_lo, lim_boolean

DATA = (
    lim_boolean('Notify', True),
    lim_hilo_percent('VoutNL', 13.85, 1.0),
    lim_hilo_percent('Vout', 13.85, 5.0),
    lim_lo('InOCP', 12.0),
    lim_hilo_delta('OCP', 14.0, 2.0),
    )
