#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tester program loader."""

import os
import traceback
import time
import inspect
import configparser
import logging.handlers
from pydispatch import dispatcher
import tester
import programs

# Configuration of logger.
_CONSOLE_LOG_LEVEL = logging.DEBUG
_LOG_FORMAT = '%(asctime)s:%(name)s:%(threadName)s:%(levelname)s:%(message)s'


def _main():
    """Run the Tester."""
    logger = logging.getLogger(__name__)
    logger.info('Starting')
    # Suppress lower level GPIB logging
    log = logging.getLogger('gpib')
    log.setLevel(logging.INFO)
    # Get the pathname of this module's configuration file
    head, tail = os.path.split(
        os.path.abspath(inspect.getfile(inspect.currentframe())))
    config_file = os.path.join(head, tail + '.ini')
    logger.debug('Configuration file: %s', config_file)
    # Read settings from the configuration file
    config = configparser.ConfigParser()
    config.read(config_file)
    test_program = config['DEFAULT'].get('Program')
    if test_program is None:
        test_program = 'Dummy'
    parameter = config['DEFAULT'].get('Parameter')
    tester_type = config['DEFAULT'].get('TesterType')
    if tester_type is None:
        tester_type = 'ATE3'
    # Receive Test Result signals here
    def test_result(result):
        logger.info('Test Result: %s', result)
    dispatcher.connect(
        test_result,
        sender=tester.signals.Thread.tester,
        signal=tester.signals.Status.result)
    # Make and run the TESTER
    logger.info('Creating "%s" Tester', tester_type)
    tst = tester.Tester(tester_type, programs.PROGRAMS)
    tst.start()
    logger.info('Create Program "%s"', test_program)
    # Make a TEST PROGRAM descriptor
    pgm = tester.TestProgram(
        test_program, per_panel=1, parameter=parameter)
    logger.info('Open Program "%s"', test_program)
    tst.open(pgm)
    logger.info('Running Test')
    try:
        tst.test(('UUT1', ))
#         tst.test(('UUT1', 'UUT2', 'UUT3', 'UUT4', ))
    except Exception:
        exc_str = traceback.format_exc()
        logger.error('Test Run Exception:\n%s', exc_str)
    finally:
        logger.info('Close Program')
        time.sleep(2)
        tst.close()
    logger.info('Stop Tester')
    tst.stop()
    tst.join()
    logger.info('Finished')


def _logging_setup():
    """
    Setup the logging system.

    Messages are sent to the stderr console.

    """
    # create console handler and set level
    hdlr = logging.StreamHandler()
    hdlr.setLevel(_CONSOLE_LOG_LEVEL)
    # Log record formatter
    fmtr = logging.Formatter(_LOG_FORMAT)
    # Connect it all together
    hdlr.setFormatter(fmtr)
    logging.root.addHandler(hdlr)
    logging.root.setLevel(logging.DEBUG)


if __name__ == '__main__':
    _logging_setup()
    _main()
