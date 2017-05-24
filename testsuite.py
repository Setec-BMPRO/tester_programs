#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd.
"""Test suite loader for Eric Unittest.

In Eric, this module is imported by unittest using a call to:
  loadTestsFromName(name, module=None)
    with parameters of  name="suite", module="testsuite"

From the Python unittest help...
  Return a suite of all tests cases given a string specifier.
  The specifier name is a "dotted name" that may resolve either to
    a module,
    a test case class,
    a test method within a test case class,
    a TestSuite instance,
    a callable object which returns a TestCase or TestSuite instance.
  These checks are applied in the order listed here.

For "Rerun Failed" unittest, loadTestsFromName is called with parameters:
    name="programs.test_XXXX", module="testsuite"

"""

import unittest
import logging
from tests import programs, share # for running individual tests


def suite():
    """Define the TestSuite for Eric unittest.

    @return TestSuite

    """
    testnames = []
    for name in share.__all__:
        testnames.append('tests.share.' + name)
    for name in programs.__all__:
        testnames.append('tests.programs.' + name)
    testsuite = unittest.defaultTestLoader.loadTestsFromNames(testnames)
    return testsuite


# Configuration of console logger when this script is run stand-alone.
#   Log Levels are: CRITICAL,ERROR,WARNING,INFO,DEBUG
_LOG_LEVEL = logging.CRITICAL
_LOG_FORMAT = '%(asctime)s:%(name)s:%(threadName)s:%(levelname)s:%(message)s'
# Set these logger names to INFO level
_LOGGER_NAMES = ('gpib', )


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
