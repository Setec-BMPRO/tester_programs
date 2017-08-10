#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""Fixture specific data, such as serial port assignment."""

import os

# Windows COM port mapping that must be manually set on each tester

# A single direct connected SETEC FTDI, ID: 0403:6001
SETEC_FTDI = 'COM16'
# SETEC FTDI connected via a USB Hub (index by hub port number [1-4])
SETEC_FTDI_HUB = [None, 'COM14', 'COM15', 'COM10', 'COM11']

DATA = {

    # Fixtures using Non-USB serial ports

    '020827': {     # BCE282 Initial
        'MSP1': {'posix': '/dev/ttyS0', 'nt': 'COM1'}[os.name], # programming
        'MSP2': {'posix': '/dev/ttyS1', 'nt': 'COM2'}[os.name], # comms
        },
    '017789': {     # CMR-SBP Initial
        'EV': {'posix': '/dev/ttyS0', 'nt': 'COM1'}[os.name],
        'CMR': {'posix': '/dev/ttyS1', 'nt': 'COM2'}[os.name],
        },
    '021299': {     # Drifter Initial
        'PIC': {'posix': '/dev/ttyS0', 'nt': 'COM1'}[os.name],
        },
    '017048': {     # IDS-500 Final
        'PIC': {'posix': '/dev/ttyS0', 'nt': 'COM1'}[os.name],
        },

    # Fixtures with a single USB Serial

    '027013': {     # BatteryCheck Final
        # Panasonic eUniStone PAN1322 (FTDI with S/N)
        'BT': {'posix': '/dev/ttyUSB0', 'nt': 'COM9'}[os.name],
        },
    '025197': {     # GEN8 Initial (Prolific)
        'ARM': {'posix': '/dev/ttyUSB0', 'nt': 'COM6'}[os.name],
        },

    # Fixtures with a single SETEC FTDI (without any S/N)

    '028467': {     # BC15 Initial
        'ARM': {'posix': '/dev/ttyUSB0', 'nt': SETEC_FTDI}[os.name],
        },
    '027176': {     # BP35 Initial
        'ARM': {'posix': '/dev/ttyUSB0', 'nt': SETEC_FTDI}[os.name],
        },
    '017056': {     # IDS-500 SubBoard Initial
        'PIC': {'posix': '/dev/ttyUSB0', 'nt': SETEC_FTDI}[os.name],
        },
    '029242': {     # J35 Initial
        'ARM': {'posix': '/dev/ttyUSB0', 'nt': SETEC_FTDI}[os.name],
        },
    '029687': {     # RvView Initial
        'ARM': {'posix': '/dev/ttyUSB0', 'nt': SETEC_FTDI}[os.name],
        },

    # Fixtures with a USB Hub

    '029083': {     # Batterycheck Initial
        'ARM_CON': {'posix': '/dev/ttyUSB0', 'nt': 'COM1'}[os.name],
        'ARM_PGM': {'posix': '/dev/ttyUSB1', 'nt': 'COM2'}[os.name],
        # Hub port X: Panasonic eUniStone PAN1322 (FTDI with S/N)
        'BT': {'posix': '/dev/ttyUSB2', 'nt': 'COM4'}[os.name],
        },
    '028468': {     # CN101 Initial
        # Hub port 1: SETEC FTDI
        'BLE': {'posix': '/dev/ttyUSB0', 'nt': SETEC_FTDI_HUB[1]}[os.name],
        # Hub port 2: SETEC FTDI
        'ARM': {'posix': '/dev/ttyUSB1', 'nt': SETEC_FTDI_HUB[2]}[os.name],
        },
    '022837': {     # SX-750 Initial
        # Hub port 2: Arduino
        'ARDUINO': {'posix': '/dev/ttyACM0', 'nt': 'COM5'}[os.name],
        # Hub port 3: SETEC FTDI
        'ARM': {'posix': '/dev/ttyUSB0', 'nt': SETEC_FTDI_HUB[3]}[os.name],
        },
    '027420': {     # Trek2 Initial/Final
        # Hub port 3: SETEC FTDI
        'ARM': {'posix': '/dev/ttyUSB0', 'nt': SETEC_FTDI_HUB[3]}[os.name],
        # Hub port 4: SETEC FTDI
        'CAN': {'posix': '/dev/ttyUSB1', 'nt': SETEC_FTDI_HUB[4]}[os.name],
        },
    '030451': {     # BC2/BLE2CAN/TRS2/TRSRFM Initial
        # Hub port X: HID Atmel programmer
#        'PROG': {'posix': '/dev/ttyUSB0', 'nt': 'COM17'}[os.name],
        # Hub port X: SETEC FTDI
        'ARM': {'posix': '/dev/ttyUSB1', 'nt': 'COM18'}[os.name],
        # Hub port X: SETEC FTDI
        'BLE': {'posix': '/dev/ttyUSB2', 'nt': 'COM19'}[os.name],
        },
    }


def port(fixture, name):
    """Lookup the serial port assignment of a fixture.

    @param fixture Fixture item number
    @param name Port name
    @return Serial port name

    """
    return DATA[fixture][name]
