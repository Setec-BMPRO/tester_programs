#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Selfchecker Test Program Limits."""

from testlimit import lim_hilo_delta, lim_hilo, lim_lo

DATA = (
    lim_hilo_delta('12V', 12.0, 0.5),
    lim_hilo_delta('5V', 5.0, 0.5),
    lim_hilo_delta('ShieldOFF', 6.0, 0.5),
    lim_hilo_delta('ShieldON', 0.0, 0.5),
    lim_hilo_delta('Dso8', 8.0, 0.5),
    lim_hilo_delta('Dso6', 6.0, 0.5),
    lim_hilo_delta('Dso4', 4.0, 0.5),
    lim_hilo('Dso2', 1.35, 2.5),
    lim_hilo_delta('Dcs5', 5.0, 0.5),
    lim_hilo_delta('Dcs10', 10.0, 0.5),
    lim_hilo_delta('Dcs20', 20.0, 0.5),
    lim_hilo_delta('Dcs35', 35.0, 0.5),
    lim_hilo_delta('120Vac', 120.0, 5.0),
    lim_hilo_delta('240Vac', 240.0, 5.0),
    lim_hilo_delta('Dcl05', 5.0, 1),
    lim_hilo_delta('Dcl10', 10.0, 1),
    lim_hilo_delta('Dcl20', 20.0, 1),
    lim_hilo_delta('Dcl40', 40.0, 1),
    lim_hilo_delta('RlaOff', 12.0, 0.5),
    lim_lo('RlaOn', 1.5),
    lim_hilo_delta('Disch_on', 10.0, 1.0),
    lim_lo('Disch_off', 0.5),
    )
