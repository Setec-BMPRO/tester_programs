#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS1 Initial Program Limits."""

from tester.testlimit import lim_hilo_delta, lim_boolean, lim_lo, lim_hi, lim_hilo

LOW_BATT_L = 10.85
LOW_BATT_U = 11.55

DATA = (
    lim_lo('VinOff', 0.5),
    lim_hilo('Vin', 11.0, 12.0),
    lim_lo('5VOff', 0.1),
    lim_hilo_delta('5VOn', 5.0, 0.1),
    lim_lo('BrakeOff', 0.1),
    lim_hilo_delta('BrakeOn', 12.0, 0.1),
    lim_lo('LightOff', 0.3),
    lim_hilo_delta('LightOn', 12.0, 0.3),
    lim_lo('RemoteOff', 0.1),
    lim_hilo_delta('RemoteOn', 12.0, 0.1),
    lim_hi('RedLedOff', 9.0),
    lim_lo('RedLedOn', 0.1),
    lim_hilo_delta('FreqTP3', 0.56, 0.2),
    lim_boolean('Notify', True),
    )
