#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tester program loader."""

import os
import inspect
import configparser
import logging.handlers
from pydispatch import dispatcher
import time

import gpib
import tester
#tester.sensor.DSO_DELAY = False
import dummy
import selftest
# Product test programs
import _2040
import atxg450
import batterycheck
import bc15
import bce4
import bce282
import bp35
import c15a15
import c15d15
import c45a15
import cmrsbp
import cn101
import drifter
import etrac
import gen8
import genius2
import gsu360
import ids500
import mk7400
import opto_test
import rm50
import smu75070
import spa
import st3
import sx750
import trek2
import trs1
import ts3020h
import ts3520
import uni750
import wtsi200


# Configuration of logger.
_CONSOLE_LOG_LEVEL = logging.DEBUG
_LOG_FORMAT = '%(asctime)s:%(name)s:%(threadName)s:%(levelname)s:%(message)s'


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
    debug_gpib = config['DEFAULT'].getboolean('DebugGPIB')
    if debug_gpib is None:
        debug_gpib = False
    gpib.DEBUG_GPIB.enabled = debug_gpib
    fifo = config['DEFAULT'].getboolean('FIFO')
    if fifo is None:
        fifo = True
    use_progdata_limits = config['DEFAULT'].getboolean('UseProgDataLimits')
    if use_progdata_limits is None:
        use_progdata_limits = False
    tester_type = config['DEFAULT'].get('TesterType')
    if tester_type is None:
        tester_type = 'ATE3'
    no_delays = config['DEFAULT'].getboolean('NoDelays')
    if no_delays is None:
        no_delays = False
    # "Monkey Patch" time, so all delays are zero
    if no_delays:
        def no_sleep(secs=0):
            pass
        time.sleep = no_sleep
    # Receive Test Result signals here
    def test_result(result):
        logger.info('Test Result: %s', result)
    dispatcher.connect(test_result,
                       sender=tester.signals.Thread.tester,
                       signal=tester.signals.Status.result)
    # All the Test Programs
    programs = (
        ('Dummy', dummy.Main, dummy.LIMIT_DATA),
        ('Self-Test', selftest.Main, selftest.LIMIT_DATA),
        ('2040 Final', _2040.final.Main, _2040.final.LIMIT_DATA),
        ('2040 Initial', _2040.initial.Main, _2040.initial.LIMIT_DATA),
        ('ATXG-450-2V Final', atxg450.final_2v.Main,
         atxg450.final_2v.LIMIT_DATA),
        ('BatteryCheck Initial', batterycheck.initial.Main,
         batterycheck.initial.LIMIT_DATA),
        ('BatteryCheck Final', batterycheck.final.Main,
         batterycheck.final.LIMIT_DATA),
        ('BC15 Initial', bc15.initial.Main, bc15.initial.LIMIT_DATA),
        ('BC15 Final', bc15.final.Main, bc15.final.LIMIT_DATA),
        ('BCE4 Final', bce4.final.Main, bce4.final.LIMIT_DATA4),
        ('BCE5 Final', bce4.final.Main, bce4.final.LIMIT_DATA5),
        ('BCE282-12 Initial', bce282.initial.Main,
         bce282.initial.LIMIT_DATA12),
        ('BCE282-12 Final', bce282.final.Main, bce282.final.LIMIT_DATA12),
        ('BCE282-24 Initial', bce282.initial.Main,
         bce282.initial.LIMIT_DATA24),
        ('BCE282-24 Final', bce282.final.Main, bce282.final.LIMIT_DATA24),
        ('BP35 Initial', bp35.initial.Main, bp35.initial.LIMIT_DATA),
        ('BP35 Final', bp35.final.Main, bp35.final.LIMIT_DATA),
        ('C15A-15 Final', c15a15.final.Main, c15a15.final.LIMIT_DATA),
        ('C15D-15(M) Final', c15d15.final.Main, c15d15.final.LIMIT_DATA),
        ('C45A-15(M) Initial', c45a15.initial.Main, c45a15.initial.LIMIT_DATA),
        ('C45A-15(M) Final', c45a15.final.Main, c45a15.final.LIMIT_DATA),
        ('CMR-INI', cmrsbp.Main, cmrsbp.LIMIT_DATA),
        ('CMR-SD', cmrsbp.Main, cmrsbp.LIMIT_DATA),
        ('CMR8D-FIN', cmrsbp.Main, cmrsbp.LIMIT_DATA_8D),
        ('CMR13F-FIN', cmrsbp.Main, cmrsbp.LIMIT_DATA_13F),
        ('CMR17L-FIN', cmrsbp.Main, cmrsbp.LIMIT_DATA_17L),
        ('CN101 Initial', cn101.initial.Main, cn101.initial.LIMIT_DATA),
        ('Drifter Initial', drifter.initial.Main, drifter.initial.LIMIT_DATA),
        ('Drifter Final', drifter.final.Main, drifter.final.LIMIT_DATA),
        ('Drifter BM Initial', drifter.initial.Main,
         drifter.initial.LIMIT_DATA_BM),
        ('Drifter BM Final', drifter.final.Main, drifter.final.LIMIT_DATA_BM),
        ('Etrac-II Initial', etrac.initial.Main, etrac.initial.LIMIT_DATA),
        ('GEN8 Final', gen8.final.Main, gen8.final.LIMIT_DATA),
        ('GEN8 Initial', gen8.initial.Main, gen8.initial.LIMIT_DATA),
        ('GENIUS-II Final', genius2.final.Main, genius2.final.LIMIT_DATA),
        ('GENIUS-II-H Final', genius2.final.Main, genius2.final.LIMIT_DATA_H),
        ('GSU360-1TA Initial', gsu360.initial.Main, gsu360.initial.LIMIT_DATA),
        ('GSU360-1TA Final', gsu360.final.Main, gsu360.final.LIMIT_DATA),
        ('IDS500 Initial Micro', ids500.initial_sub.Main,
         ids500.initial_sub.LIMIT_DATA),
        ('IDS500 Initial Main', ids500.initial_main.Main,
         ids500.initial_main.LIMIT_DATA),
        ('IDS500 Final', ids500.final.Main, ids500.final.LIMIT_DATA),
        ('MK7-400-1 Final', mk7400.final.Main, mk7400.final.LIMIT_DATA),
        ('Opto Test', opto_test.Main, opto_test.LIMIT_DATA),
        ('RM-50-24 Final', rm50.final.Main, rm50.final.LIMIT_DATA),
        ('Spa Multi RGB', spa.multi.Main, spa.multi.LIMIT_DATA_RGB),
        ('Spa Multi TRI', spa.multi.Main, spa.multi.LIMIT_DATA_TRI),
        ('Spa Single', spa.single.Main, spa.single.LIMIT_DATA),
        ('ST20-III Final', st3.final.Main, st3.final.LIMIT_DATA20),
        ('ST35-III Final', st3.final.Main, st3.final.LIMIT_DATA35),
        ('SX-750 Initial', sx750.initial.Main, sx750.initial.LIMIT_DATA),
        ('SX-750 Final', sx750.final.Main, sx750.final.LIMIT_DATA),
        ('SX-750 Safety', sx750.safety.Main, sx750.safety.LIMIT_DATA),
        ('SMU750-70 Final', smu75070.final.Main, smu75070.final.LIMIT_DATA),
        ('Trek2 Initial', trek2.initial.Main, trek2.initial.LIMIT_DATA),
        ('Trek2 Final', trek2.final.Main, trek2.final.LIMIT_DATA),
        ('Trs1 Initial', trs1.initial.Main, trs1.initial.LIMIT_DATA),
        ('Trs1 Final', trs1.final.Main, trs1.final.LIMIT_DATA),
        ('TS3020-H Initial', ts3020h.initial.Main, ts3020h.initial.LIMIT_DATA),
        ('TS3020-H Final', ts3020h.final.Main, ts3020h.final.LIMIT_DATA),
        ('TS3520 Final', ts3520.final.Main, ts3520.final.LIMIT_DATA),
        ('UNI-750 Final', uni750.final.Main, uni750.final.LIMIT_DATA),
        ('WTSI200 Final', wtsi200.final.Main, wtsi200.final.LIMIT_DATA),
        )
    # Make a TEST PROGRAM descriptor
    pgm = tester.TestProgram(
        'BC15 Initial',
        per_panel=1, parameter=None, test_limits=[])
    # Make and run the TESTER
    logger.info('Creating "%s" Tester', tester_type)
    tst = tester.Tester(tester_type, programs, fifo, use_progdata_limits)
    tst.start()
    logger.info('Open Tester')
    tst.open(pgm)
#    Allows 2 seconds before fixture lock to remove board at ATE2
    time.sleep(2)
    logger.info('Running Test')
    tst.test(('UUT1', ))
#    tst.test(('UUT1', 'UUT2', 'UUT3', 'UUT4', ))
    time.sleep(2)
    logger.info('Close Tester')
    tst.close()
    logger.info('Stop Tester')
    tst.stop()
    tst.join()
    logger.info('Finished')

if __name__ == '__main__':
    _logging_setup()
    _main()
