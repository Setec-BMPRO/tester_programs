#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Product Test Programs."""

from . import selftest
from . import _2040
from . import atxg450
from . import batterycheck
from . import bc15
from . import bce4
from . import bce282
from . import bp35
from . import c15a15
from . import c15d15
from . import c45a15
from . import cmrsbp
from . import cn101
from . import drifter
from . import etrac
from . import gen8
from . import genius2
from . import gsu360
from . import ids500
from . import j35
from . import mk7400
from . import opto_test
from . import rvview
from . import rm50
from . import smu75070
from . import spa
from . import st3
from . import sx750
from . import trek2
from . import trs1
from . import ts3020h
from . import ts3520
from . import uni750
from . import wtsi200

# All the Test Programs
#   The tester package iterates through this Tuple of Tuples to build
#   the test program data structures.
#
#   Each Tuple holds 3 items:
#   1) Name of the program,
#       Note that this name must match the entry in:
#           The ATE4 storage system (No size limit)
#           The ATE2 database (maximum of 50 characters)
#   2) The class to use to create a program instance,
#   3) Test limit data structure for testlimit.limitset()
#
#   Names listed in ALL_SKIP will not be run by the ALL PROGRAMS
#   option in main.py

PROGRAMS = (
    ('Self-Test', selftest.Main, selftest.LIMIT),
    ('2040 Final', _2040.Final, _2040.FIN_LIMIT),
    ('2040 Initial', _2040.Initial, _2040.INI_LIMIT),
    ('ATXG-450-2V Final', atxg450.Final2V, atxg450.FIN2V_LIMIT),
    ('BatteryCheck Initial', batterycheck.Initial, batterycheck.INI_LIMIT),
    ('BatteryCheck Final', batterycheck.Final, batterycheck.FIN_LIMIT),
    ('BC15 Initial', bc15.Initial, bc15.INI_LIMIT),
    ('BC15 Final', bc15.Final, bc15.FIN_LIMIT),
    ('BCE4 Final', bce4.Final, bce4.LIMIT_DATA4),
    ('BCE5 Final', bce4.Final, bce4.LIMIT_DATA5),
    ('BCE282-12 Initial', bce282.Initial, bce282.INI_LIMIT_12),
    ('BCE282-12 Final', bce282.Final, bce282.FIN_LIMIT_12),
    ('BCE282-24 Initial', bce282.Initial, bce282.INI_LIMIT_24),
    ('BCE282-24 Final', bce282.Final, bce282.FIN_LIMIT_24),
    ('BP35 Initial', bp35.Initial, bp35.INI_LIMIT),
    ('BP35 Final', bp35.Final, bp35.FIN_LIMIT),
    ('C15A-15 Initial', c15a15.Initial, c15a15.INI_LIMIT),
    ('C15A-15 Final', c15a15.Final, c15a15.FIN_LIMIT),
    ('C15D-15(M) Initial', c15d15.Initial, c15d15.INI_LIMIT),
    ('C15D-15(M) Final', c15d15.Final, c15d15.FIN_LIMIT),
    ('C45A-15(M) Initial', c45a15.Initial, c45a15.INI_LIMIT),
    ('C45A-15(M) Final', c45a15.Final, c45a15.FIN_LIMIT),
    ('CMR-INI', cmrsbp.Initial, cmrsbp.LIMIT_DATA),
    ('CMR-SD', cmrsbp.SerialDate, cmrsbp.LIMIT_DATA),
    ('CMR8D-FIN', cmrsbp.Final, cmrsbp.LIMIT_DATA_8D),
    ('CMR13F-FIN', cmrsbp.Final, cmrsbp.LIMIT_DATA_13F),
    ('CMR17L-FIN', cmrsbp.Final, cmrsbp.LIMIT_DATA_17L),
    ('CN101 Initial', cn101.Initial, cn101.INI_LIMIT),
    ('Drifter Initial', drifter.Initial, drifter.INI_LIMIT),
    ('Drifter Final', drifter.Final, drifter.FIN_LIMIT),
    ('Drifter BM Initial', drifter.Initial, drifter.INI_LIMIT_BM),
    ('Drifter BM Final', drifter.Final, drifter.FIN_LIMIT_BM),
    ('Etrac-II Initial', etrac.Initial, etrac.INI_LIMIT),
    ('GEN8 Final', gen8.Final, ()),
    ('GEN8 Initial', gen8.Initial, gen8.INI_LIMIT),
    ('GENIUS-II Final', genius2.Final, genius2.FIN_LIMIT),
    ('GENIUS-II-H Final', genius2.Final, genius2.FIN_LIMIT_H),
    ('GENIUS-II Initial', genius2.Initial, genius2.INI_LIMIT),
    ('GENIUS-II-H Initial', genius2.Initial, genius2.INI_LIMIT_H),
    ('GSU360-1TA Initial', gsu360.Initial, gsu360.INI_LIMIT),
    ('GSU360-1TA Final', gsu360.Final, gsu360.FIN_LIMIT),
    ('IDS500 Initial Micro', ids500.InitialMicro, ids500.INI_MIC_LIMIT),
    ('IDS500 Initial Aux', ids500.InitialAux, ids500.INI_AUX_LIMIT),
    ('IDS500 Initial Bias', ids500.InitialBias, ids500.INI_BIAS_LIMIT),
    ('IDS500 Initial Bus', ids500.InitialBus, ids500.INI_BUS_LIMIT),
    ('IDS500 Initial Syn', ids500.InitialSyn, ids500.INI_SYN_LIMIT),
    ('IDS500 Initial Main', ids500.InitialMain, ids500.INI_MAIN_LIMIT),
    ('IDS500 Final', ids500.Final, ids500.FIN_LIMIT),
    ('J35A Initial', j35.Initial, j35.INI_LIMIT_A),
    ('J35B Initial', j35.Initial, j35.INI_LIMIT_B),
    ('J35C Initial', j35.Initial, j35.INI_LIMIT_C),
    ('J35A Final', j35.Final, j35.FIN_LIMIT_A),
    ('J35B Final', j35.Final, j35.FIN_LIMIT_B),
    ('J35C Final', j35.Final, j35.FIN_LIMIT_C),
    ('MK7-400-1 Final', mk7400.Final, mk7400.FIN_LIMIT),
    ('Opto Test', opto_test.Main, opto_test.LIMIT),
    ('RVVIEW Initial', rvview.Initial, rvview.INI_LIMIT),
    ('RM-50-24 Final', rm50.Final, rm50.FIN_LIMIT),
    ('SMU750-70 Final', smu75070.Final, smu75070.FIN_LIMIT),
    ('Spa Multi RGB', spa.InitialMulti, spa.RGB_LIMIT),
    ('Spa Multi TRI', spa.InitialMulti, spa.TRI_LIMIT),
    ('Spa Single', spa.InitialSingle, spa.SGL_LIMIT),
    ('ST20-III Final', st3.Final, st3.FIN20_LIMIT),
    ('ST35-III Final', st3.Final, st3.FIN35_LIMIT),
    ('SX-750 Initial', sx750.Initial, sx750.INI_LIMIT),
    ('SX-750 Final', sx750.Final, sx750.FIN_LIMIT),
    ('SX-750 Safety', sx750.Safety, sx750.SAF_LIMIT),
    ('Trek2 Initial', trek2.Initial, trek2.INI_LIMIT),
    ('Trek2 Final', trek2.Final, trek2.FIN_LIMIT),
    ('TRS1 Initial', trs1.Initial, trs1.INI_LIMIT),
    ('TS3020-H Initial', ts3020h.Initial, ts3020h.INI_LIMIT),
    ('TS3020-H Final', ts3020h.Final, ts3020h.FIN_LIMIT),
    ('TS3520 Final', ts3520.Final, ts3520.FIN_LIMIT),
    ('UNI-750 Final', uni750.Final, uni750.FIN_LIMIT),
    ('WTSI200 Final', wtsi200.Final, wtsi200.FIN_LIMIT),
    )

# Skip these programs when running 'ALL PROGRAMS' in main.py
#   because they will not pass in simulation mode.
ALL_SKIP = (
    # Due to use of the EV2200
    'CMR-INI', 'CMR-SD',
    # Unfinished programs
    'IDS500 Initial Main', 'IDS500 Final',
    # Done with unittest
    'BP35 Initial', 'GEN8 Initial', 'GEN8 Final',
    'GENIUS-II Initial', 'GENIUS-II-H Initial',
    'J35 Initial', 'J35C Final', 'RVVIEW Initial',
    # Obsolete and unused programs
    'Spa Multi RGB', 'Spa Multi TRI', 'Spa Single',
    'SX-750 Safety',
    # The voltage adjuster will not simulate
    'TS3020-H Initial',
    )
