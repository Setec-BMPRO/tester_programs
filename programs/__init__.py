#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Product Test Programs."""

from . import dummy
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
from . import mk7400
from . import opto_test
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
#       NOTE: This name must match the entry in:
#           The ATE4 storage system (No size limit)
#           The ATE2 database (maximum of 50 characters)
#   2) The class to use to create a program instance,
#   3) Test limit data structure for testlimit.LimitSet()
#
#   Names listed in ALL_SKIP will not be run by the ALL PROGRAMS
#   option in main.py

PROGRAMS = (
    ('Dummy', dummy.Main, dummy.LIMIT_DATA),
    ('Self-Test', selftest.Main, selftest.LIMIT_DATA),
    ('2040 Final', _2040.final.Main, _2040.final.LIMIT_DATA),
    ('2040 Initial', _2040.initial.Main, _2040.initial.LIMIT_DATA),
    ('ATXG-450-2V Final', atxg450.final_2v.Main, atxg450.final_2v.LIMIT_DATA),
    ('BatteryCheck Initial', batterycheck.initial.Main,
     batterycheck.initial.LIMIT_DATA),
    ('BatteryCheck Final', batterycheck.final.Main,
     batterycheck.final.LIMIT_DATA),
    ('BC15 Initial', bc15.initial.Main, bc15.initial.LIMIT_DATA),
    ('BC15 Final', bc15.final.Main, bc15.final.LIMIT_DATA),
    ('BCE4 Final', bce4.final.Main, bce4.final.LIMIT_DATA4),
    ('BCE5 Final', bce4.final.Main, bce4.final.LIMIT_DATA5),
    ('BCE282-12 Initial', bce282.initial.Main, bce282.initial.LIMIT_DATA12),
    ('BCE282-12 Final', bce282.final.Main, bce282.final.LIMIT_DATA12),
    ('BCE282-24 Initial', bce282.initial.Main, bce282.initial.LIMIT_DATA24),
    ('BCE282-24 Final', bce282.final.Main, bce282.final.LIMIT_DATA24),
    ('BP35 Initial', bp35.initial.Main, bp35.initial.LIMIT_DATA),
    ('BP35 Final', bp35.final.Main, bp35.final.LIMIT_DATA),
    ('C15A-15 Initial', c15a15.initial.Main, c15a15.initial.LIMIT_DATA),
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
    ('TRS1 Initial', trs1.initial.Main, trs1.initial.LIMIT_DATA),
    ('TRS1 Final', trs1.final.Main, trs1.final.LIMIT_DATA),
    ('TS3020-H Initial', ts3020h.initial.Main, ts3020h.initial.LIMIT_DATA),
    ('TS3020-H Final', ts3020h.final.Main, ts3020h.final.LIMIT_DATA),
    ('TS3520 Final', ts3520.final.Main, ts3520.final.LIMIT_DATA),
    ('UNI-750 Final', uni750.final.Main, uni750.final.LIMIT_DATA),
    ('WTSI200 Final', wtsi200.final.Main, wtsi200.final.LIMIT_DATA),
    )

# Skip these programs when running 'ALL PROGRAMS' in main.py
ALL_SKIP = (
    'CMR-INI', 'CMR-SD', 'CMR8D-FIN', 'CMR13F-FIN', 'CMR17L-FIN',
    'IDS500 Initial Micro', 'IDS500 Initial Main', 'IDS500 Final',
    'Spa Multi RGB', 'Spa Multi TRI', 'Spa Single',
    'SX-750 Safety',
    'Trek2 Final',
    'TS3020-H Initial',
    )
