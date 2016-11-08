#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GENIUS-II and GENIUS-II-H Initial Test Program Limits."""

from tester.testlimit import (
    lim_hilo, lim_hilo_delta, lim_lo, lim_boolean, lim_hi)

PIC_HEX = 'genius2_2.hex'

_BASE_DATA = (
    lim_hilo_delta('FlyLead', 30.0, 10.0),
    lim_hilo_delta('AcIn', 240.0, 5.0),
    lim_hilo_delta('Vbus', 330.0, 20.0),
    lim_hilo('Vcc', 13.8, 22.5),
    lim_lo('VccOff', 5.0),
    lim_hilo_delta('Vdd', 5.00, 0.1),
    lim_hilo('VbatCtl', 12.7, 13.5),
    lim_hilo_delta('Vctl', 12.0, 0.5),
    lim_hilo('VoutPre', 12.5, 15.0),
    lim_hilo_delta('Vout', 13.65, 0.05),
    lim_lo('VoutOff', 1.0),
    lim_hilo('VbatPre', 12.5, 15.0),
    lim_hilo_delta('Vbat', 13.65, 0.05),
    lim_hilo_delta('Vaux', 13.70, 0.5),
    lim_lo('FanOff', 0.5),
    lim_hilo('FanOn', 12.0, 14.1),
    lim_lo('InOCP', 13.24),
    lim_hilo('OCP', 34.0, 43.0),
    lim_boolean('Notify', True),
    lim_lo('FixtureLock', 20),
    )

DATA = _BASE_DATA + (
    lim_lo('MaxBattLoad', 15.0),
    lim_lo('VbatOCP', 10.0),
    )

DATA_H = _BASE_DATA + (
    lim_lo('MaxBattLoad', 30.0),
    lim_hi('VbatOCP', 13.0),
    )
