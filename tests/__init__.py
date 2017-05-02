#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 SETEC Pty Ltd.
"""Unittests."""

import unittest
import logging

_test_modules = [
    'test_bc15_initial',
    'test_bc15_final',
    'test_bp35_final',
    'test_bp35_initial',
    'test_bce282_final',
    'test_bce282_initial',
    'test_can_tunnel',
    'test_console',
    'test_gen8_final',
    'test_gen8_initial',
    'test_genius2_initial',
    'test_ids_final',
    'test_ids_ini_main',
    'test_j35_final',
    'test_j35_initial',
    'test_parameter',
    'test_rvview_initial',
    'test_smu75070_initial',
    'test_sx750_final',
    'test_sx750_initial',
    ]

__all__ = ['suite'] + _test_modules


def suite():
    """Define the TestSuite for Eric unittest."""
    testsuite = unittest.defaultTestLoader.loadTestsFromNames(
        ('tests.' + name for name in _test_modules)
        )
    return testsuite

# Configuration of logger.
_CONSOLE_LOG_LEVEL = logging.DEBUG
_LOG_FORMAT = '%(asctime)s:%(name)s:%(threadName)s:%(levelname)s:%(message)s'

_SETUP = False

def logging_setup():
    """Setup the logging system.

    Messages are sent to the stderr console.

    """
    global _SETUP
    if not _SETUP:
        # create console handler and set level
        hdlr = logging.StreamHandler()
        hdlr.setLevel(_CONSOLE_LOG_LEVEL)
        # Log record formatter
        fmtr = logging.Formatter(_LOG_FORMAT)
        # Connect it all together
        hdlr.setFormatter(fmtr)
        if not logging.root.hasHandlers():
            logging.root.addHandler(hdlr)
        logging.root.setLevel(logging.DEBUG)
        _SETUP = True
