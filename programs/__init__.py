#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Product Test Programs."""

from . import selftest
from . import _2040
from . import atxg450
from . import batterycheck
from . import bc2
from . import bc15_25
from . import bce4
from . import bce282
from . import ble2can
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
from . import mb2
from . import mk7400
from . import rvview
from . import rm50
from . import smu75070
from . import st3
from . import sx750
from . import trek2
from . import trek2_jcontrol
from . import trs1
from . import trs2
from . import trsrfm
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
#       Value:
#           The class to use to create a program instance

PROGRAMS = {
    'Self-Test': selftest.Main,
    '2040 Final': _2040.Final,
    '2040 Initial': _2040.Initial,
    'ATXG-450-2V Final': atxg450.Final2V,
    'BatteryCheck Initial': batterycheck.Initial,
    'BatteryCheck Final': batterycheck.Final,
    'BC2 Initial': bc2.Initial,
    'BC2 Final': bc2.Final,
    'BC15_25 Initial': bc15_25.Initial,
    'BC15_25 Final': bc15_25.Final,
    'BCE4_5 Final': bce4.Final,
    'BCE282 Initial': bce282.Initial,
    'BCE282 Final': bce282.Final,
    'BLE2CAN Initial': ble2can.Initial,
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
    'MB2 Final': mb2.Final,
    'MK7-400-1 Final': mk7400.Final,
    'RVVIEW Initial': rvview.Initial,
    'RM-50-24 Final': rm50.Final,
    'SMU750-70 Final': smu75070.Final,
    'SMU750-70 Initial': smu75070.Initial,
    'STxx-III Final': st3.Final,
    'SX-750 Initial': sx750.Initial,
    'SX-750 Final': sx750.Final,
    'SX-750 Safety': sx750.Safety,
    'Trek2 Initial': trek2.Initial,
    'Trek2 Final': trek2.Final,
    'Trek2JControl Initial': trek2_jcontrol.Initial,
    'Trek2JControl Final': trek2_jcontrol.Final,
    'TRS1 Initial': trs1.Initial,
    'TRS2 Initial': trs2.Initial,
    'TRS2 Final': trs2.Final,
    'TRSRFM Initial': trsrfm.Initial,
    'TS3020-H Initial': ts3020h.Initial,
    'TS3020-H Final': ts3020h.Final,
    'TS3520 Final': ts3520.Final,
    'UNI-750 Final': uni750.Final,
    'WTSI200 Final': wtsi200.Final,
    }
