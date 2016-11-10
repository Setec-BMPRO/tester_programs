#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BP35 Initial Program Limits."""

import os
from tester.testlimit import (
    lim_hilo, lim_hilo_delta, lim_hilo_percent, lim_hilo_int,
    lim_lo, lim_string, lim_boolean)

ARM_VERSION = '1.2.13351.3801'      # ARM versions
ARM_HW_VER1 = (3, 0, 'A')
ARM_HW_VER5 = (7, 0, 'A')
ARM_HW_VER8 = (8, 0, 'A')
PIC_VERSION1 = '1.1.13543.181'      # Solar Regulator for Rev 1-7
PIC_HW_VER1 = 1
PIC_VERSION8 = '1.1.13802.182'      # Solar Regulator for Rev 8
PIC_HW_VER8 = 3

# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM16'}[os.name]
# ARM software image file
ARM_BIN = 'bp35_{}.bin'.format(ARM_VERSION)
# dsPIC software image file
PIC_HEX1 = 'bp35sr_{}.hex'.format(PIC_VERSION1)
PIC_HEX8 = 'bp35sr_{}.hex'.format(PIC_VERSION8)
# CAN echo request messages
CAN_ECHO = 'TQQ,32,0'

# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28
# Solar Reg settings
SOLAR_VSET = 13.650
SOLAR_ISET = 30.0
SOLAR_VIN = 20.0
# Injected Vbat & Vaux
VBAT_IN = 12.4
VAUX_IN = 13.5
# PFC settling level
PFC_STABLE = 0.05

DATA = (
    lim_lo('FixtureLock', 50),
    lim_boolean('Notify', True),
    lim_hilo_delta('HwVer5', 3200.0, 250.0),    # Rev 5-7
    lim_hilo_delta('HwVer8', 4400.0, 250.0),    # Rev 8+
    lim_hilo_delta('ACin', 240.0, 5.0),
    lim_hilo('Vpfc', 401.0, 424.0),
    lim_hilo('12Vpri', 11.5, 13.0),
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
    lim_hilo_delta('SolarVcc', 3.3, 0.1),
    lim_hilo_percent('VsetPre', SOLAR_VSET, 6.0),
    lim_hilo_percent('VsetPost', SOLAR_VSET, 3.0),
    lim_hilo_percent('ARM-IoutPre', 10.0, 9.0),
    lim_hilo_percent('ARM-IoutPost', 10.0, 4.0),
    lim_hilo('OCP', 6.0, 9.0),
    lim_lo('InOCP', 11.6),
    lim_string('ARM-SwVer', '^{}$'.format(ARM_VERSION.replace('.', r'\.'))),
    lim_hilo_delta('ARM-AcV', 240.0, 10.0),
    lim_hilo_delta('ARM-AcF', 50.0, 1.0),
    lim_hilo('ARM-SecT', 8.0, 70.0),
    lim_hilo_delta('ARM-Vout', 12.45, 0.45),
    lim_hilo('ARM-Fan', 0, 100),
    lim_hilo('ARM-LoadI', 0.1, 12.1),
    lim_hilo_delta('ARM-BattI', 4.0, 1.0),
    lim_hilo_delta('ARM-AuxV', 13.4, 0.4),
    lim_hilo('ARM-AuxI', 0.0, 1.5),
    lim_string('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    lim_string('CAN_RX', r'^RRQ,32,0'),
    lim_hilo_int('CAN_BIND', _CAN_BIND),
    lim_hilo_int('SOLAR_ALIVE', 1),
    lim_hilo_int('SOLAR_RELAY', 1),
    lim_hilo_int('SOLAR_ERROR', 0),
    lim_hilo_int('Vout_OV', 0),     # Over-voltage not triggered
    )
