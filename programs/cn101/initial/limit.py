#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CN101 Initial Program Limits."""

# CAN Bus is operational if status bit 28 is set
_CAN_BIND = 1 << 28


def _hilo_delta(name, nominal, delta):
    """Return a Hi/Lo limit tuple for use in the Limit Set data.

    @param name Test limit name
    @param nominal Nominal value
    @param delta Absolute deviation of the limits from nominal
    @return Tuple of (name, 0, Low, High, None, None)
    """
    return (name, 0, nominal - delta, nominal + delta, None, None)


def _hilo_percent(name, nominal, tolerance):
    """Return a Hi/Lo limit tuple for use in the Limit Set data.

    @param name Test limit name
    @param nominal Nominal value
    @param tolerance Tolerance in %
    @return Tuple of (name, 0, Low, High, None, None)
    """
    return _hilo_delta(name, nominal, nominal * tolerance / 100.0)


def _hilo_int(name, nominal):
    """Return a Hi/Lo limit tuple for use in the Limit Set data.

    @param name Test limit name
    @param nominal Nominal integer value
    @return Tuple of (name, 0, Low, High, None, None)
    """
    return _hilo_delta(name, nominal, 0.5)


def _lo(name, nominal):
    """Return a Lo limit tuple for use in the Limit Set data.

    @param name Test limit name
    @param nominal Low value
    @return Tuple of (name, 0, nominal, None, None, None)
    """
    return (name, 0, nominal, None, None, None)


def _hi(name, nominal):
    """Return a Hi limit tuple for use in the Limit Set data.

    @param name Test limit name
    @param nominal High value
    @return Tuple of (name, 0, None, nominal, None, None)
    """
    return (name, 0, None, nominal, None, None)


def _string(name, pattern):
    """Return a String limit tuple for use in the Limit Set data.

    @param name Test limit name
    @param pattern RegEx pattern
    @return Tuple of (name, 0, None, None, pattern, None)
    """
    return (name, 0, None, None, pattern, None)


def _boolean(name, value):
    """Return a Boolean limit tuple for use in the Limit Set data.

    @param name Test limit name
    @param value Boolean value
    @return Tuple of (name, 0, None, None, None, value)
    """
    return (name, 0, None, None, None, value)


#   Tuple ( Tuple (name, identity, low, high, string, boolean))
DATA = (
    _hilo_delta('Vin', 12.0, 0.5),
    _hilo_percent('3V3', 3.30, 3.0),
    _lo('AwnOff', 0.5),
    _hilo_delta('AwnOn', 12.0, 0.5),
    _lo('SldOutOff', 0.5),
    _hilo_delta('SldOutOn', 12.0, 0.5),
    _hilo_int('Program', 0),
    _string('SerNum', r'^A[0-9]{4}[0-9A-Z]{2}[0-9]{4}$'),
    _string('CAN_ID', r'^RRQ,16,0'),
    _hilo_int('CAN_BIND', _CAN_BIND),
    _string('SwVer', r'^1\.0\.10892\.110$'),
    _string(
        'BtMac', r'^[0-9]{2}:[0-9]{2}:[0-9]{2}:[0-9]{2}:[0-9]{2}:[0-9]{2}$'),
    _hilo_int('DetectBT', 0),
    _hilo_int('Tank', 4),
    _boolean('Notify', True),
    )

if __name__ == '__main__':
    for lim in DATA:
        print(lim)
