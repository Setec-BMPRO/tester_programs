#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd.
"""Test suite definition for Eric Unittest plugin."""

import unittest
import logging

# Configuration of console logger when this script is run stand-alone.
#   Log Levels are: CRITICAL,ERROR,WARNING,INFO,DEBUG
_LOG_LEVEL = logging.CRITICAL
_LOG_FORMAT = '%(asctime)s:%(name)s:%(threadName)s:%(levelname)s:%(message)s'
# Set these logger names to INFO level
_LOGGER_NAMES = ('gpib', )


def suite():
    """Define the test suite for Eric unittest tool.

    @return unittest.testsuite

    """
    return unittest.defaultTestLoader.discover(
        start_dir='.', pattern='test_*.py')


def logging_setup():
    """Setup the logging system.

    Messages are sent to the stderr console.

    """
    # create console handler and set level
    hdlr = logging.StreamHandler()
    hdlr.setLevel(_LOG_LEVEL)
    # Log record formatter
    fmtr = logging.Formatter(_LOG_FORMAT)
    # Connect it all together
    hdlr.setFormatter(fmtr)
    if not logging.root.hasHandlers():
        logging.root.addHandler(hdlr)
    logging.root.setLevel(_LOG_LEVEL)
    # Suppress lower level logging level
    if _LOG_LEVEL < logging.INFO:
        for name in _LOGGER_NAMES:
            log = logging.getLogger(name)
            log.setLevel(logging.INFO)


def _main():
    """Run the testsuite."""
    logging_setup()
    runner = unittest.TextTestRunner()
    testsuite = suite()
    runner.run(testsuite)


if __name__ == '__main__':
    _main()
