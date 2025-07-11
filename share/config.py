#!/usr/bin/env python3
# Copyright 2017 SETEC Pty Ltd
"""Configuration classes."""

import os
from typing import ClassVar, Dict

from attrs import define

import libtester


@define
class Fixture:
    """Fixture specific data, such as serial port assignment.

    Linux testers:
       /dev/ttyACM0 is the CANable Pro interface device.
       /dev/ttyACM1 is the ATE4 GEN4 (Arduino) device.

    Windows testers:
       COM port mapping must be manually set on each tester.
       COM30 is used for the CANable Pro interface device.

    """

    __slots__ = ()

    # A single direct connected FTDI, ID: 0403:6001, without S/N
    _ftdi: ClassVar[Dict[str, str]] = {"posix": "/dev/ttyUSB0", "nt": "COM16"}[os.name]
    # FTDI without S/N connected via a USB Hub
    _ftdi_hub_1: ClassVar[Dict[str, str]] = {"posix": "/dev/ttyUSB0", "nt": "COM14"}[
        os.name
    ]
    _ftdi_hub_2: ClassVar[Dict[str, str]] = {"posix": "/dev/ttyUSB1", "nt": "COM15"}[
        os.name
    ]

    _data: ClassVar[Dict[str, Dict[str, str]]] = {
        # ======== Fixtures with a single USB Serial (inc. FTDI with S/N)
        "017048": {  # IDS-500 Final (Prolific)
            "PIC": {"posix": "/dev/ttyUSB0", "nt": "COM6"}[os.name],
        },
        "017054": {  # IDS-500 Main Initial (Prolific) [ Unused ]
            "PIC": {"posix": "/dev/ttyUSB0", "nt": "COM6"}[os.name],
        },
        "017823": {  # C45A-15 Initial
            "ARDUINO": {"posix": "/dev/ttyACM1", "nt": "COM37"}[os.name],
        },
        "019883": {  # ETrac-II Initial
            "ARDUINO": {"posix": "/dev/ttyACM1", "nt": "COM36"}[os.name],
        },
        "027013": {  # BatteryCheck Final
            # Panasonic eUniStone PAN1322 (FTDI with S/N)
            "BT": {"posix": "/dev/ttyUSB0", "nt": "COM9"}[os.name],
        },
        # ======== Fixtures with a single FTDI without any S/N
        "017056": {
            "PIC": _ftdi,
        },  # IDS-500 SubBoard Initial
        "021299": {
            "PIC": _ftdi,
        },  # Drifter Initial
        "025197": {
            "ARM": _ftdi,
        },  # GEN8 Initial
        "027420": {
            "ARM": _ftdi,
        },  # Trek2 Initial/Final
        "028467": {
            "ARM": _ftdi,
        },  # BC15 Initial
        "028468": {
            "ARM": _ftdi,
        },  # CN101,2,3 Initial
        "029242": {
            "ARM": _ftdi,
        },  # J35 Initial
        "029687": {
            "ARM": _ftdi,
        },  # RvView/JDisplay/RVMD50 Initial
        "031032": {
            "ARM": _ftdi,
        },  # BC25 Initial
        "032715": {
            "ARM": _ftdi,
        },  # GEN9-540 Initial
        "032869": {
            "NORDIC": _ftdi,
        },  # RVSWT101 Initial
        "032870": {
            "ARM": _ftdi,
        },  # RVMC101 Initial
        "040556": {
            "NORDIC": _ftdi,
        },  # RVMN301C Initial
        "032871": {
            "NORDIC": _ftdi,
        },  # RVMN101B Initial
        "033550": {
            "NORDIC": _ftdi,
        },  # RVMN101A Initial
        "033633": {
            "AVR": _ftdi,
        },  # MB3 Initial
        "034352": {
            "NORDIC": _ftdi,
        },  # TRS-BTx Initial
        "034861": {
            "NORDIC": _ftdi,
        },  # RVMN5x Initial
        "034882": {
            "NORDIC": _ftdi,
        },  # TRSRFM Initial
        "037269": {
            "ARM": _ftdi,
            "NORDIC": _ftdi,
        },  # Opto Initial (Program/Initialize all boards on this fixture number)
        "036746": {
            "ARM": _ftdi,
        },  # ASDisplay Initial
        "039516": {
            "STM": _ftdi,
        },  # BC60 Initial
        "039517": {
            "ARM": _ftdi,
        },  # BSGateway Initial
        # ======== Fixtures with a USB Hub
        "017789": {  # CMR-SBP Initial (Prolific)
            # Hub port 1:
            "EV": {"posix": "/dev/ttyUSB0", "nt": "COM21"}[os.name],
            # Hub port 2:
            "CMR": {"posix": "/dev/ttyUSB1", "nt": "COM22"}[os.name],
        },
        "017790": {  # CMR-SBP Final (Prolific)
            # Hub port 1:
            "EV": {"posix": "/dev/ttyUSB0", "nt": "COM21"}[os.name],
            # Hub port 2:
            "CMR": {"posix": "/dev/ttyUSB1", "nt": "COM22"}[os.name],
        },
        "020827": {  # BCE282 Initial
            "BSL": _ftdi_hub_1,  # Programming
            "CON": _ftdi_hub_2,  # Console
        },
        "022837": {  # SX-750 Initial
            "ARM": _ftdi_hub_1,
            # Hub port 2:
            "ARDUINO": {"posix": "/dev/ttyACM1", "nt": "COM5"}[os.name],
        },
        "027176": {  # BP35 Initial
            "ARM": _ftdi_hub_1,
            # Hub port 2:
            "ARDUINO": {"posix": "/dev/ttyACM1", "nt": "COM39"}[os.name],
        },
        # TODO: Remove the USB Hub & RN4020 on port 2
        "030451": {  # BC2/BLE2CAN/TRS2/TRSRFM Initial
            "ARM": _ftdi_hub_1,
            # Hub port 2: FTDI
            "BLE": {"posix": "/dev/ttyUSB2", "nt": "COM7"}[os.name],
        },
        "033030": {  # RVSWT101 Final
            # Hub port 2:
            "ARDUINO": {"posix": "/dev/ttyACM1", "nt": "COM39"}[os.name],
        },
        "033484": {  # SX-600 Initial
            "ARM": _ftdi_hub_1,
            # Hub port 2:
            "ARDUINO": {"posix": "/dev/ttyACM1", "nt": "COM5"}[os.name],
        },
        "034400": {  # BP35-II Initial
            "ARM": _ftdi_hub_1,
            # Hub port 2:
            "ARDUINO": {"posix": "/dev/ttyACM1", "nt": "COM38"}[os.name],
        },
        "035827": {  # SmartLink201/BLExtender Initial
            "ARM": _ftdi_hub_1,
            "NORDIC": _ftdi_hub_2,
        },
    }

    @classmethod
    def port(cls, tester_type: str, fixture: libtester.Fixture, name: str) -> str:
        """Lookup the serial port assignment of a fixture.

        @param tester_type Tester name
        @param fixture libtester.Fixture
        @param name Port name
        @return Serial port name

        """
        if not isinstance(fixture, libtester.Fixture):
            raise ValueError(
                "Fixture must be a libtester.Fixture, not {0!r}".format(fixture)
            )
        item_num = fixture.item.number
        result = cls._data[item_num][name]
        # ATE4 has the GEN4 Arduino as ttyACM1
        if tester_type == "ATE4" and result == "/dev/ttyACM1":
            result = "/dev/ttyACM2"
        return result
