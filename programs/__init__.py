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
from . import st3
from . import sx750
from . import trek2
from . import trs1
from . import ts3020h
from . import ts3520
from . import uni750
from . import wtsi200

# All the Test Programs
#   Each Dictionary entry is:
#       Key:
#           Name of the program,
#           Note that this name must match the entry in:
#               The ATE4 storage system (No size limit)
#               The ATE2 database (maximum of 50 characters)
#       Value: Tuple of 2 items:
#           1) The class to use to create a program instance,
#           2) Test limit data structure for testlimit.limitset()
#
#   Names listed in ALL_SKIP will not be run by the ALL PROGRAMS
#   option in main.py

PROGRAMS = {
    'Self-Test': selftest.Main,
    '2040 Final': _2040.Final,
    '2040 Initial': _2040.Initial,
    'ATXG-450-2V Final': atxg450.Final2V,
    'BatteryCheck Initial': batterycheck.Initial,
    'BatteryCheck Final': batterycheck.Final,
    'BC15 Initial': bc15.Initial,
    'BC15 Final': bc15.Final,
    'BCE4/5 Final': bce4.Final,
    'BCE282 Initial': bce282.Initial,
    'BCE282 Final': bce282.Final,
    'BP35 Initial': bp35.Initial,
    'BP35 Final': bp35.Final,
    'C15A-15 Initial': c15a15.Initial,
    'C15A-15 Final': c15a15.Final,
    'C15D-15(M) Initial': c15d15.Initial,
    'C15D-15(M) Final': c15d15.Final,
    'C45A-15(M) Initial': c45a15.Initial,
    'C45A-15(M) Final': c45a15.Final,
    'CMR-INI': cmrsbp.Initial,
    'CMR-SD': cmrsbp.SerialDate,
    'CMR-FIN': cmrsbp.Final,
    'CN101 Initial': cn101.Initial,
    'Drifter Initial': drifter.Initial,
    'Drifter Final': drifter.Final,
    'Etrac-II Initial': etrac.Initial,
    'GEN8 Final': gen8.Final,
    'GEN8 Initial': gen8.Initial,
    'GENIUS-II Final': genius2.Final,
    'GENIUS-II Initial': genius2.Initial,
    'GSU360-1TA Initial': gsu360.Initial,
    'GSU360-1TA Final': gsu360.Final,
    'IDS500 Initial Micro': ids500.InitialMicro,
    'IDS500 Initial Aux': ids500.InitialAux,
    'IDS500 Initial Bias': ids500.InitialBias,
    'IDS500 Initial Bus': ids500.InitialBus,
    'IDS500 Initial Syn': ids500.InitialSyn,
    'IDS500 Initial Main': ids500.InitialMain,
    'IDS500 Final': ids500.Final,
    'J35 Initial': j35.Initial,
    'J35 Final': j35.Final,
    'MK7-400-1 Final': mk7400.Final,
    'Opto Test': opto_test.Main,
    'RVVIEW Initial': rvview.Initial,
    'RM-50-24 Final': rm50.Final,
    'SMU750-70 Final': smu75070.Final,
    'STxx-III Final': st3.Final,
    'SX-750 Initial': sx750.Initial,
    'SX-750 Final': sx750.Final,
    'SX-750 Safety': sx750.Safety,
    'Trek2 Initial': trek2.Initial,
    'Trek2 Final': trek2.Final,
    'TRS1 Initial': trs1.Initial,
    'TS3020-H Initial': ts3020h.Initial,
    'TS3020-H Final': ts3020h.Final,
    'TS3520 Final': ts3520.Final,
    'UNI-750 Final': uni750.Final,
    'WTSI200 Final': wtsi200.Final,
    }

# Skip these programs when running 'ALL PROGRAMS' in main.py
ALL_SKIP = (
    # Due to use of the EV2200
    'CMR-INI', 'CMR-SD',
    # Unfinished programs

    # Done with unittest
    'BP35 Initial', 'BP35 Final', 'GEN8 Initial', 'GEN8 Final',
    'GENIUS-II Initial',
    'IDS500 Initial Main', 'IDS500 Final',
    'J35 Initial', 'J35 Final',
    'RVVIEW Initial', 'SX-750 Initial',
    # Obsolete and unused programs
    'SX-750 Safety',
    # The voltage adjuster will not simulate
    'TS3020-H Initial',
    )
