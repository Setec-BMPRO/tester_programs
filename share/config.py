#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 - 2019 SETEC Pty Ltd
"""Configuration classes."""

import os


class System():

    """System data."""

    # Type of Tester.
    # One of ('ATE2a', 'ATE2c', 'ATE3', 'ATE4')
    #  Must be set by the user of this project, since there is
    #  no way we can find it...
    tester_type = None


class Fixture():

    """Fixture specific data, such as serial port assignment.

        Windows testers:
           COM port mapping must be manually set on each tester.
           COM30 is used for the Serial2Can interface device.

        Linux testers:
           Use /dev/ttyACM0 for the GEN4 (Arduino) device.
           /dev/ttyUSB0 is used for the Serial2Can interface device.

    """

    # Traditional motherboard serial ports
    _internal_1 = {'posix': '/dev/ttyS0', 'nt': 'COM1'}[os.name]
    _internal_2 = {'posix': '/dev/ttyS1', 'nt': 'COM2'}[os.name]
    # A single direct connected FTDI, ID: 0403:6001, without S/N
    _ftdi = {'posix': '/dev/ttyUSB1', 'nt': 'COM16'}[os.name]
    # FTDI without S/N connected via a USB Hub
    _ftdi_hub_1 = {'posix': '/dev/ttyUSB1', 'nt': 'COM14'}[os.name]
    _ftdi_hub_2 = {'posix': '/dev/ttyUSB2', 'nt': 'COM15'}[os.name]

    _data = {

        # Fixtures using Non-USB serial ports

        '029083': {     # Batterycheck Initial
            'ARM_CON': _internal_1,
            'ARM_PGM': _internal_2,
            # Hub port X: Panasonic eUniStone PAN1322 (FTDI with S/N)
            'BT': {'posix': '/dev/ttyUSB1', 'nt': 'COM4'}[os.name],
            },
        '020827': {     # BCE282 Initial( MSP1: programming, MSP2: comms)
            'MSP1': _internal_1,
            'MSP2': {'posix': '/dev/ttyS1', 'nt': 'COM2'}[os.name],
            },
        '021299': {'PIC': _internal_1, },   # Drifter Initial

        # Fixtures with a single USB Serial (inc. FTDI with S/N)

        '027013': {     # BatteryCheck Final
            # Panasonic eUniStone PAN1322 (FTDI with S/N)
            'BT': {'posix': '/dev/ttyUSB1', 'nt': 'COM9'}[os.name],
            },
        '017048': {     # IDS-500 Final (Prolific)
            'PIC': {'posix': '/dev/ttyUSB1', 'nt': 'COM6'}[os.name],
            },

        # Fixtures with a single FTDI without any S/N

        '028467': {'ARM': _ftdi, },     # BC15 Initial
        '031032': {'ARM': _ftdi, },     # BC25 Initial
        '027176': {'ARM': _ftdi, },     # BP35 Initial
        '017056': {'PIC': _ftdi, },     # IDS-500 SubBoard Initial
        '029242': {'ARM': _ftdi, },     # J35 Initial
        '029687': {'ARM': _ftdi, },     # RvView Initial
        '027420': {'ARM': _ftdi, },     # Trek2 Initial/Final
        '025197': {'ARM': _ftdi, },     # GEN8 Initial
        '032715': {'ARM': _ftdi, },     # GEN9-540 Initial
        '032870': {'ARM': _ftdi, },     # RVMC101 Initial
        '033633': {'AVR': _ftdi, },     # MB3 Initial

        # Fixtures with a USB Hub

        '017789': {     # CMR-SBP Initial (Prolific)
            'EV': {'posix': '/dev/ttyUSB1', 'nt': 'COM21'}[os.name],
            'CMR': {'posix': '/dev/ttyUSB2', 'nt': 'COM22'}[os.name],
            },
        '028468': {     # CN101 Initial
            'BLE': _ftdi_hub_1,
            'ARM': _ftdi_hub_2,
            },
        '030451': {     # BC2/BLE2CAN/TRS2/TRSRFM Initial
            'ARM': _ftdi_hub_1,
            # Hub port 2: FTDI
            'BLE': {'posix': '/dev/ttyUSB2', 'nt': 'COM7'}[os.name],
            },
        '032869': {     # RVSWT101 Initial
            'NORDIC': _ftdi_hub_1,
            # Hub port 2: Nordic NRF52 device programmer
            # Hub port 3,4: not used
            },
        '033550': {     # RVMN101A Initial
            'ARM': _ftdi_hub_1,
            # Hub port 2: FTDI with S/N
            'NORDIC': {'posix': '/dev/ttyUSB2', 'nt': 'COM29'}[os.name],
            # Hub port 3: Nordic NRF52 device programmer
            # Hub port 4: not used
            },
        '032871': {     # RVMN101B Initial
            'ARM': _ftdi_hub_1,
            # Hub port 2: FTDI with S/N
            'NORDIC': {'posix': '/dev/ttyUSB2', 'nt': 'COM28'}[os.name],
            # Hub port 3: Nordic NRF52 device programmer
            # Hub port 4: not used
            },
        }

    _data_per_tester = {

        # Fixtures with a USB Hub

        '022837': {     # SX-600/SX-750 Initial
            'ATE2a': {
                'ARM': _ftdi_hub_1,
                # Hub port 2: Arduino
                'ARDUINO': {'posix': '/dev/ttyACM0', 'nt': 'COM5'}[os.name],
                },
            'ATE2c': {
                'ARM': _ftdi_hub_1,
                # Hub port 2: Arduino
                'ARDUINO': {'posix': '/dev/ttyACM0', 'nt': 'COM5'}[os.name],
                },
            'ATE3': {
                'ARM': _ftdi_hub_1,
                # Hub port 2: Arduino
                'ARDUINO': {'posix': '/dev/ttyACM0', 'nt': 'COM5'}[os.name],
                },
            'ATE4': {
                'ARM': _ftdi_hub_1,
                # Hub port 2: Arduino
                'ARDUINO': {'posix': '/dev/ttyACM1', 'nt': 'COM5'}[os.name],
                },
            },
        }

    @classmethod
    def port(cls, fixture, name):
        """Lookup the serial port assignment of a fixture.

        @param fixture Fixture ID
        @param name Port name
        @return Serial port name

        """
        if fixture in cls._data_per_tester:
            result = cls._data_per_tester[fixture][System.tester_type][name]
        else:
            result = cls._data[fixture][name]
        return result
