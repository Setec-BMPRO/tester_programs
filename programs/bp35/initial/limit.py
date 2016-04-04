#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BP35 Initial Program Limits."""

ARM_VERSION = '1.2.12951.3751'      # ARM versions
ARM_HW_VER = (3, 0, 'A')
PIC_VERSION = '1.1.12949.167'       # Solar Regulator versions
PIC_HW_VER = 1

from testlimit import (
    lim_hilo, lim_hilo_delta, lim_hilo_percent, lim_hilo_int,
    lim_hi, lim_lo, lim_string, lim_boolean)

# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28
# Solar Reg settings
_SOLAR_VSET = 13.65
_SOLAR_ISET = 30.0

#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    lim_hilo_delta('ACin', 240.0, 5.0),
    lim_hilo('Vpfc', 401.0, 424.0),
    lim_hilo('12Vpri', 11.5, 13.0),
    lim_hilo('5Vusb', -4.5, 5.5),
    lim_hilo('15Vs', 11.5, 13.0),
    lim_hilo('Vload', 12.0, 12.9),
    lim_lo('VloadOff', 0.5),
    lim_hilo_delta('VbatIn', 12.0, 0.5),
    lim_hilo('Vbat', 12.2, 13.0),
    lim_hilo('Vsreg', 0, 9999),
    lim_hilo_delta('Vaux', 13.4, 0.4),
    lim_hilo_delta('3V3', 3.30, 0.05),
    lim_hilo_delta('FanOn', 12.5, 0.5),
    lim_lo('FanOff', 0.5),
    lim_hilo_delta('3V3prog', 3.3, 0.1),
    # Solar Reg set output voltage and current
    lim_lo('Vset', _SOLAR_VSET),
    lim_lo('Iset', _SOLAR_ISET),
    lim_hilo_percent('VsetPre', _SOLAR_VSET, 6.0),
    lim_hilo_percent('VsetPost', _SOLAR_VSET, 3.0),
    lim_hilo('OCP', 6.0, 9.0),
    lim_lo('InOCP', 11.6),
    lim_hilo_int('Program', 0),
    lim_lo('FixtureLock', 1200),
    lim_hi('SwShort', 20),
    lim_boolean('Notify', True),
    lim_string('ARM-SwVer', '^{}$'.format(ARM_VERSION.replace('.', r'\.'))),
    lim_hilo_delta('ARM-AcV', 240.0, 10.0),
    lim_hilo_delta('ARM-AcF', 50.0, 1.0),
    lim_hilo('ARM-PriT', 8.0, 70.0),
    lim_hilo('ARM-SecT', 8.0, 70.0),
    lim_hilo_delta('ARM-Vout', 12.45, 0.45),
    lim_hilo('ARM-Fan', 0, 100),
    lim_hilo('ARM-LoadI', 0.1, 12.1),
    lim_hilo_delta('ARM-BattI', 4.0, 1.0),
    lim_hilo_delta('ARM-AuxV', 13.4, 0.4),
    lim_hilo('ARM-AuxI', 0.0, 1.1),
    lim_string('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    lim_string('CAN_ID', r'^RRQ,32,0'),
    lim_hilo_int('CAN_BIND', _CAN_BIND),
    lim_hilo('CAN_STATS', 0, 0xFFFFFFFF),
    lim_hilo_int('SOLAR_ALIVE', 1),
    lim_hilo_int('Vout_OV', 0),     # Over-voltage not triggered
    )
