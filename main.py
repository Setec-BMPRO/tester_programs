#!/usr/bin/env python3
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
import _2040_final
import _2040_initial
import atxg450_2v_final
import batterycheck_initial
import batterycheck_final
import bc15_initial
import bc15_final
import bce4_final
import bce282_final
import bp35_initial
import c15a15_final
import c15d15_final
import c45a15_initial
import c45a15_final
import cmrsbp_all
import drifter_initial
import drifter_final
import etracII_initial
import gen8_final
import gen8_initial
import geniusII_final
import gsu3601ta_initial
import gsu3601ta_final
import mk7_final
import opto_test
import rm50_final
import smu75070_final
import spa_multi
import spa_single
import st3_final
import trek2_initial
import trek2_final
import sx750_initial
import sx750_safety
import sx750_final
import ts3020h_initial
import ts3020h_final
import ts3520_final
import uni750_final
import wtsi200_final


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
        ('2040 Final', _2040_final.Main, _2040_final.LIMIT_DATA),
        ('2040 Initial', _2040_initial.Main, _2040_initial.LIMIT_DATA),
        ('ATXG-450-2V Final', atxg450_2v_final.Main,
         atxg450_2v_final.LIMIT_DATA),
        ('BatteryCheck Initial', batterycheck_initial.Main,
         batterycheck_initial.LIMIT_DATA),
        ('BatteryCheck Final', batterycheck_final.Main,
         batterycheck_final.LIMIT_DATA),
        ('BC15 Initial', bc15_initial.Main, bc15_initial.LIMIT_DATA),
        ('BC15 Final', bc15_final.Main, bc15_final.LIMIT_DATA),
        ('BCE4 Final', bce4_final.Main, bce4_final.LIMIT_DATA4),
        ('BCE5 Final', bce4_final.Main, bce4_final.LIMIT_DATA5),
        ('BCE282-12 Final', bce282_final.Main, bce282_final.LIMIT_DATA12),
        ('BCE282-24 Final', bce282_final.Main, bce282_final.LIMIT_DATA24),
        ('BP35 Initial', bp35_initial.Main, bp35_initial.LIMIT_DATA),
        ('C15A-15 Final', c15a15_final.Main, c15a15_final.LIMIT_DATA),
        ('C15D-15(M) Final', c15d15_final.Main, c15d15_final.LIMIT_DATA),
        ('C45A-15(M) Initial', c45a15_initial.Main, c45a15_initial.LIMIT_DATA),
        ('C45A-15(M) Final', c45a15_final.Main, c45a15_final.LIMIT_DATA),
        ('CMR-INI', cmrsbp_all.Main, cmrsbp_all.LIMIT_DATA),
        ('CMR-SD', cmrsbp_all.Main, cmrsbp_all.LIMIT_DATA),
        ('CMR8D-FIN', cmrsbp_all.Main, cmrsbp_all.LIMIT_DATA_8D),
        ('CMR13F-FIN', cmrsbp_all.Main, cmrsbp_all.LIMIT_DATA_13F),
        ('CMR17L-FIN', cmrsbp_all.Main, cmrsbp_all.LIMIT_DATA_17L),
        ('Drifter Initial', drifter_initial.Main, drifter_initial.LIMIT_DATA),
        ('Drifter Final', drifter_final.Main, drifter_final.LIMIT_DATA),
        ('Drifter BM Initial', drifter_initial.Main,
         drifter_initial.LIMIT_DATA_BM),
        ('Drifter BM Final', drifter_final.Main, drifter_final.LIMIT_DATA_BM),
        ('Etrac-II Initial', etracII_initial.Main, etracII_initial.LIMIT_DATA),
        ('GEN8 Final', gen8_final.Main, gen8_final.LIMIT_DATA),
        ('GEN8 Initial', gen8_initial.Main, gen8_initial.LIMIT_DATA),
        ('GENIUS-II Final', geniusII_final.Main, geniusII_final.LIMIT_DATA),
        ('GENIUS-II-H Final', geniusII_final.Main,
         geniusII_final.LIMIT_DATA_H),
        ('GSU360-1TA Initial', gsu3601ta_initial.Main,
         gsu3601ta_initial.LIMIT_DATA),
        ('GSU360-1TA Final', gsu3601ta_final.Main, gsu3601ta_final.LIMIT_DATA),
        ('MK7-400-1 Final', mk7_final.Main, mk7_final.LIMIT_DATA),
        ('Opto Test', opto_test.Main, opto_test.LIMIT_DATA),
        ('RM-50-24 Final', rm50_final.Main, rm50_final.LIMIT_DATA),
        ('Spa Multi RGB', spa_multi.Main, spa_multi.LIMIT_DATA_RGB),
        ('Spa Multi TRI', spa_multi.Main, spa_multi.LIMIT_DATA_TRI),
        ('Spa Single', spa_single.Main, spa_single.LIMIT_DATA),
        ('ST20-III Final', st3_final.Main, st3_final.LIMIT_DATA20),
        ('ST35-III Final', st3_final.Main, st3_final.LIMIT_DATA35),
        ('SX-750 Initial', sx750_initial.Main, sx750_initial.LIMIT_DATA),
        ('SX-750 Final', sx750_final.Main, sx750_final.LIMIT_DATA),
        ('SX-750 Safety', sx750_safety.Main, sx750_safety.LIMIT_DATA),
        ('SMU750-70 Final', smu75070_final.Main, smu75070_final.LIMIT_DATA),
        ('Trek2 Initial', trek2_initial.Main, trek2_initial.LIMIT_DATA),
        ('Trek2 Final', trek2_final.Main, trek2_final.LIMIT_DATA),
        ('TS3020-H Initial', ts3020h_initial.Main, ts3020h_initial.LIMIT_DATA),
        ('TS3020-H Final', ts3020h_final.Main, ts3020h_final.LIMIT_DATA),
        ('TS3520 Final', ts3520_final.Main, ts3520_final.LIMIT_DATA),
        ('UNI-750 Final', uni750_final.Main, uni750_final.LIMIT_DATA),
        ('WTSI200 Final', wtsi200_final.Main, wtsi200_final.LIMIT_DATA),
        )
    # Make a TEST PROGRAM descriptor
    pgm = tester.TestProgram(
        'BC15 Final',
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
