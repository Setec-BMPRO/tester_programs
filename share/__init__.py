#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""Shared modules for Tester programs."""

import enum
# Easy access to utility methods and classes
from .testsequence import Devices, Sensors, Measurements, TestSequence
from .testsequence import teststep      # a decorator
from . import fixture
from . import console
from . import bluetooth
from . import timers


@enum.unique
class CanID(enum.IntEnum):

    """CAN device ID values for different products.

    From "SetecCANandBLECommunicationsProtocol Ver2B".

    """

    cn100 = 4
    bp35 = 16
    j35 = 20
    trek2 = 32
    cn101 = 36
    ble2can = 40
    rvview = 44
    bc2 = 128
