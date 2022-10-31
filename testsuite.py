#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2015 SETEC Pty Ltd.
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

import logging
import unittest

from tests import programs, share  # for running individual tests


def suite():
    """Define the TestSuite for Eric unittest.

    @return TestSuite

    """
    testnames = []
    for name in share.__all__:
        testnames.append("tests.share." + name)
    for name in programs.__all__:
        testnames.append("tests.programs." + name)
    testsuite = unittest.defaultTestLoader.loadTestsFromNames(testnames)
    return testsuite


class Main:

    # Configuration of console logger.
    #   Log Levels are: CRITICAL,ERROR,WARNING,INFO,DEBUG
    log_level = logging.CRITICAL
    log_format = "{asctime}:{name}:{threadName}:{levelname}:{message}"
    # Set these logger names to INFO level
    logger_names = ("gpib",)

    @classmethod
    def setup(cls):
        """Setup the logging system.

        Messages are sent to the stderr console.

        """
        # Create console handler and set level
        hdlr = logging.StreamHandler()
        hdlr.setLevel(cls.log_level)
        # Log record formatter
        fmtr = logging.Formatter(cls.log_format, style="{")
        # Connect it all together
        hdlr.setFormatter(fmtr)
        if not logging.root.hasHandlers():
            logging.root.addHandler(hdlr)
        logging.root.setLevel(cls.log_level)
        # Suppress lower level logging level
        if cls.log_level < logging.INFO:
            for name in cls.logger_names:
                log = logging.getLogger(name)
                log.setLevel(logging.INFO)

    @classmethod
    def run(cls):
        """Run the testsuite."""
        cls.setup()
        runner = unittest.TextTestRunner()
        testsuite = suite()
        runner.run(testsuite)


if __name__ == "__main__":
    Main.run()
