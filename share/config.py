#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd
"""Configuration classes."""

import os


class System():     # pylint: disable=too-few-public-methods

    """System data."""

    # Type of Tester.
    # One of ('ATE2a', 'ATE2c', 'ATE3', 'ATE4')
    #  Must be set by the user of this project, since there is
    #  no way we can find it...
    tester_type = 'ATE4'    # A default value...

    @classmethod
    def ble_url(cls):
        """Lookup the URL of the Bluetooth JSONRPC server.

        @return URL of JSON-RPC server

        """
        if cls.tester_type in ('ATE4', 'ATE5'):
            url = 'http://127.0.0.1:8888/'
        else:   # Use a networked Raspberry PI
            url = 'http://192.168.168.62:8888/'
        return url


class Fixture():

    """Fixture specific data, such as serial port assignment.

        Linux testers:
           Use /dev/ttyACM0 for the GEN4 (Arduino) device.
           /dev/ttyUSB0 is used for the Serial2Can interface device.

        Windows testers:
           COM port mapping must be manually set on each tester.
           COM30 is used for the Serial2Can interface device.

    """

    # A single direct connected FTDI, ID: 0403:6001, without S/N
    _ftdi = {'posix': '/dev/ttyUSB1', 'nt': 'COM16'}[os.name]
    # FTDI without S/N connected via a USB Hub
    _ftdi_hub_1 = {'posix': '/dev/ttyUSB1', 'nt': 'COM14'}[os.name]
    _ftdi_hub_2 = {'posix': '/dev/ttyUSB2', 'nt': 'COM15'}[os.name]

    _data = {

        # Fixtures with a single USB Serial (inc. FTDI with S/N)

        '017048': {     # IDS-500 Final (Prolific)
            'PIC': {'posix': '/dev/ttyUSB1', 'nt': 'COM6'}[os.name],
            },
        '017054': {     # IDS-500 Main Initial (Prolific) [ Unused ]
            'PIC': {'posix': '/dev/ttyUSB1', 'nt': 'COM6'}[os.name],
            },
        '017823': {     # C45A-15 Initial
            'ARDUINO': {'posix': '/dev/ttyACM0', 'nt': 'COM37'}[os.name],
            },
        '019883': {     # ETrac-II Initial
            'ARDUINO': {'posix': '/dev/ttyACM0', 'nt': 'COM36'}[os.name],
            },
        '027013': {     # BatteryCheck Final
            # Panasonic eUniStone PAN1322 (FTDI with S/N)
            'BT': {'posix': '/dev/ttyUSB1', 'nt': 'COM9'}[os.name],
            },

        # Fixtures with a single FTDI without any S/N

        '017056': {'PIC': _ftdi, },     # IDS-500 SubBoard Initial
        '021299': {'PIC': _ftdi, },     # Drifter Initial
        '025197': {'ARM': _ftdi, },     # GEN8 Initial
        '027420': {'ARM': _ftdi, },     # Trek2 Initial/Final
        '028467': {'ARM': _ftdi, },     # BC15 Initial
        '029242': {'ARM': _ftdi, },     # J35 Initial
        '029687': {'ARM': _ftdi, },     # RvView/JDisplay/RVMD50 Initial
        '031032': {'ARM': _ftdi, },     # BC25 Initial
        '032715': {'ARM': _ftdi, },     # GEN9-540 Initial
        '032870': {'ARM': _ftdi, },     # RVMC101 Initial
        '033633': {'AVR': _ftdi, },     # MB3 Initial
        '034352': {'NORDIC': _ftdi, },  # TRS-BTx Initial
        '036746': {'ARM': _ftdi, },     # ASDisplay Initial

        # Fixtures with a USB Hub

        '017789': {     # CMR-SBP Initial (Prolific)
            # Hub port 1:
            'EV': {'posix': '/dev/ttyUSB1', 'nt': 'COM21'}[os.name],
            # Hub port 2:
            'CMR': {'posix': '/dev/ttyUSB2', 'nt': 'COM22'}[os.name],
            },
        '020827': {     # BCE282 Initial
            'MSP1': _ftdi_hub_1,    # Programming
            'MSP2': _ftdi_hub_2,    # Console
            },
        '022837': {     # SX-600/SX-750 Initial
            'ARM': _ftdi_hub_1,
            # Hub port 2:
            'ARDUINO': {'posix': '/dev/ttyACM0', 'nt': 'COM5'}[os.name],
            },
        '027176': {     # BP35 Initial
            'ARM': _ftdi_hub_1,
            # Hub port 2:
            'ARDUINO': {'posix': '/dev/ttyACM0', 'nt': 'COM39'}[os.name],
            },
        '028468': {     # CN101,2,3 Initial
            'ARM': _ftdi_hub_1,
            # Hub port 2:
            'nRF52': '682195648',
            },
# TODO: Remove the USB Hub & RN4020 on port 2
        '030451': {     # BC2/BLE2CAN/TRS2/TRSRFM Initial
            'ARM': _ftdi_hub_1,
            # Hub port 2: FTDI
            'BLE': {'posix': '/dev/ttyUSB2', 'nt': 'COM7'}[os.name],
            },
        '032869': {     # RVSWT101 Initial
            'NORDIC': _ftdi_hub_1,
            # Hub port 2: Nordic NRF52 device programmer
            'nRF52': '682507721',
            },
        '032871': {     # RVMN101B Initial
            'ARM': _ftdi_hub_1,
            'NORDIC': _ftdi_hub_2,
            # Hub port 3: Nordic NRF52 device programmer
            'nRF52': '682329023',
            },
        '033030': {     # RVSWT101 Final
            # Hub port 2:
            'ARDUINO': {'posix': '/dev/ttyACM1', 'nt': 'COM39'}[os.name],
            },
        '033550': {     # RVMN101A Initial
            'ARM': _ftdi_hub_1,
            'NORDIC': _ftdi_hub_2,
            # Hub port 3: Nordic NRF52 device programmer
            'nRF52': '682553964',
            },
        '034400': {     # BP35-II Initial
            'ARM': _ftdi_hub_1,
            # Hub port 2:
            'ARDUINO': {'posix': '/dev/ttyACM0', 'nt': 'COM38'}[os.name],
            },
        '034861': {     # RVMN5x Initial
            'ARM': _ftdi_hub_1,
            'NORDIC': _ftdi_hub_2,
            # Hub port 3: Nordic NRF52 device programmer
            'nRF52': '682781126',
            },
        '034882': {     # TRSRFM Initial
            'NORDIC': _ftdi_hub_1,
            # Hub port 2: Nordic NRF52 device programmer
            'nRF52': '682639845',
            },
        '035827': {     # SmartLink201 Initial
            'ARM': _ftdi_hub_1,
            'NORDIC': _ftdi_hub_2,
            # Hub port 3: Nordic NRF52 device programmer
            'nRF52': '682952990',
            },
        }

    @classmethod
    def port(cls, fixture, name):
        """Lookup the serial port assignment of a fixture.

        @param fixture Fixture ID
        @param name Port name
        @return Serial port name

        """
        result = cls._data[fixture][name]
        # ATE4 has the GEN4 Arduino as ttyACM0
        if System.tester_type == 'ATE4' and result == '/dev/ttyACM0':
            result = '/dev/ttyACM1'
        return result

    @classmethod
    def nrf52_sernum(cls, fixture):
        """Lookup the nRF52 serial number in a fixture.

        @param fixture Fixture ID
        @return Serial number string

        """
        return cls._data[fixture]['nRF52']
