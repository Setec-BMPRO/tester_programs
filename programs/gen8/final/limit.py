#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""GEN8 Final Program Limits."""

from tester.testlimit import (
    lim_hilo_delta, lim_lo, lim_hi, lim_hilo, lim_boolean)

DATA = (
    lim_hilo_delta('Iecon', 240, 10),
    lim_lo('Iecoff', 10),
    lim_hilo('5V', 4.998, 5.202),
    lim_lo('24Voff', 0.5),
    lim_lo('12Voff', 0.5),
    lim_lo('12V2off', 0.5),
    lim_hilo('24Von', 22.80, 25.44),
    lim_hilo('12Von', 11.8755, 12.4845),
    lim_hilo('12V2on', 11.8146, 12.4845),
    lim_hi('PwrFailOff', 11.0),
    lim_boolean('Notify', True),
    )
