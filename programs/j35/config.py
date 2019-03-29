#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""J35 Configuration."""

import math
import collections
import logging
from tester import (
    LimitLow, LimitHigh, LimitBetween, LimitDelta, LimitPercent,
    LimitInteger, LimitRegExp, LimitBoolean,
    )
import share


class J35():

    """Base configuration for J35."""

    # Available software versions
    sw_15 = '1.5.17467.1373'    # Current release
    sw_13 = '1.3.15775.997'     # For 'A' & 'B' < Rev 8
    # Adjustable configuration data values
    values = collections.namedtuple(
        'values',
        'sw_version, hw_version,'
        ' output_count, ocp_set,'
        ' solar, canbus'
        )
    # These values get set per Product type & revision
    sw_version = None
    hw_version = None
    output_count = None
    ocp_set = None
    solar = None
    canbus = None
    # General parameters used in testing the units
    # Injected voltages
    #  Battery bus
    vbat_inject = 12.6
    #  Aux or Solar inputs
    aux_solar_inject = 13.5
    # AC voltage powering the unit
    ac_volt = 240.0
    ac_freq = 50.0
    # Extra % error in OCP allowed before adjustment
    ocp_adjust_percent = 10.0
    # Output set points when running in manual mode
    vout_set = 12.8
    ocp_man_set = 35.0
    # Battery load current
    batt_current = 4.0
    # Load on each output channel
    load_per_output = 2.0
    # Test limits common to all tests and versions
    _base_limits_all = (
        LimitRegExp('SwVer', '', doc='Software version'),
        )
    # Initial Test limits common to all versions
    _base_limits_initial = _base_limits_all + (
        LimitDelta('ACin', ac_volt, delta=5.0, doc='AC input voltage'),
        LimitDelta('Vbus', ac_volt * math.sqrt(2), delta=10.0,
            doc='Peak of AC input'),
        LimitBetween('12Vpri', 11.5, 13.0, doc='12Vpri rail'),
        LimitPercent('Vload', vout_set, percent=3.0,
            doc='AC-DC convertor voltage setpoint'),
        LimitLow('VloadOff', 0.5, doc='When output is OFF'),
        LimitDelta('VbatIn', vbat_inject, delta=1.0,
            doc='Voltage at Batt when 12.6V is injected into Batt'),
        LimitDelta('VfuseIn', vbat_inject, delta=1.0,
            doc='Voltage after fuse when 12.6V is injected into Batt'),
        LimitDelta('VbatOut', aux_solar_inject, delta=0.5,
            doc='Voltage at Batt when 13.5V is injected into Aux'),
        LimitDelta('Vbat', vout_set, delta=0.2,
            doc='Voltage at Batt when unit is running'),
        LimitPercent('VbatLoad', vout_set, percent=5.0,
            doc='Voltage at Batt when unit is running under load'),
        LimitDelta('Vair', aux_solar_inject, delta=0.5,
            doc='Voltage at Air when 13.5V is injected into Solar'),
        LimitPercent('3V3U', 3.30, percent=1.5,
            doc='3V3 unswitched when 12.6V is injected into Batt'),
        LimitPercent('3V3', 3.30, percent=1.5, doc='3V3 internal rail'),
        LimitBetween('15Vs', 11.5, 13.0, doc='15Vs internal rail'),
        LimitDelta('FanOn', vout_set, delta=1.0, doc='Fan running'),
        LimitLow('FanOff', 0.5, doc='Fan not running'),
        LimitPercent('ARM-AuxV', aux_solar_inject, percent=2.0, delta=0.3,
            doc='ARM Aux voltage reading'),
        LimitBetween('ARM-AuxI', 0.0, 1.5,
            doc='ARM Aux current reading'),
        LimitInteger('Vout_OV', 0, doc='Over-voltage not triggered'),
        LimitPercent('ARM-AcV', ac_volt, percent=4.0, delta=1.0,
            doc='ARM AC voltage reading'),
        LimitPercent('ARM-AcF', ac_freq, percent=4.0, delta=1.0,
            doc='ARM AC frequency reading'),
        LimitBetween('ARM-SecT', 8.0, 70.0,
            doc='ARM secondary temperature sensor'),
        LimitPercent('ARM-Vout', vout_set, percent=2.0, delta=0.1,
            doc='ARM measured Vout'),
        LimitBetween('ARM-Fan', 0, 100, doc='ARM fan speed'),
        LimitPercent('ARM-BattI', batt_current, percent=1.7, delta=1.0,
            doc='ARM battery current reading'),
        LimitDelta('ARM-LoadI', load_per_output, delta=0.9,
            doc='ARM output current reading'),
        LimitInteger('ARM-RemoteClosed', 1),
        LimitDelta('CanPwr', vout_set, delta=1.8, doc='CAN bus power supply'),
        LimitInteger('LOAD_SET', 0x5555555,
            doc='ARM output load enable setting'),
        LimitInteger('CAN_BIND', 1 << 28,
            doc='ARM reports CAN bus operational'),
        LimitLow('InOCP', vout_set - 1.2, doc='Output is in OCP'),
        LimitPercent('SolarCutoffPre', 14.125, percent=6,
            doc='Solar Cut-Off voltage threshold uncertainty'),
        LimitBetween('SolarCutoff', 13.75, 14.5,
            doc='Solar Cut-Off voltage threshold range'),
        LimitLow('FixtureLock', 200, doc='Test fixture lid microswitch'),
        LimitBoolean('Solar-Status', True,
            doc='Solar Comparator Status is set'),
        LimitBoolean('DetectCal', True, doc='Solar comparator calibrated'),
        )
    # Final Test limits common to all versions
    _base_limits_final = _base_limits_all + (
        LimitLow('FanOff', 1.0, doc='No airflow seen'),
        LimitHigh('FanOn', 10.0, doc='Airflow seen'),
        LimitDelta('Can12V', 12.5, delta=2.0, doc='CAN_POWER rail'),
        LimitLow('Can0V', 0.5,  doc='CAN BUS removed'),
        LimitDelta('Vout', 12.8, delta=0.2, doc='No load output voltage'),
        LimitPercent('Vload', 12.8, percent=5,
            doc='Loaded output voltage'),
        LimitLow('InOCP', 11.6, doc='Output voltage to detect OCP'),
        )
    # Internal data storage
    _lot_rev = None         # Lot Number to Revision data
    _rev_data = None        # Revision data dictionary

    @staticmethod
    def select(parameter, uut):
        """Select a configuration based on the parameter and lot.

        @param parameter Type of unit (A/B/C)
        @param uut UUT to get Lot Number from
        @return configuration class

        """
# TODO: 469 x J35C were converted to J35B via PC 4885
#   J35C Rev 4, Lots: A164211 (x135), A164309 (x265)
#   ==> Should we change parameter from 'C' to 'B' ?...
        config = {
            'A': J35A,
            'B': J35B,
            'C': J35C,
            'D': J35D,
            }[parameter]
        config._configure(uut)    # Adjust for the Lot Number
        return config

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut storage.UUT instance

        """
        rev = None
        if uut:
            lot = uut.lot
            try:
                rev = cls._lot_rev.find(lot)
            except share.lots.LotError:
                pass
        logging.getLogger(__name__).debug('Revision detected as %s', rev)
        (cls.sw_version, cls.hw_version,
         cls.output_count, cls.ocp_set,
         cls.solar, cls.canbus, ) = cls._rev_data[rev]


class J35A(J35):

    """J35A configuration."""

    # Output set points when running in manual mode
    ocp_man_set = 20.0
    _lot_rev = share.lots.Revision((
        (share.lots.Range('A164809', 'A170404'), 1),    # 029622
        (share.lots.Range('A171704', 'A174711'), 2),    # 030061
        # No Rev 3 production                           # 031137
        # No Rev 4,5,6 created
        (share.lots.Range('A174510', 'A180408'), 8),    # 031190
        # Rev 8 Built as Rev 9
        (share.lots.Range('A181105', 'A182206'), 9),    # 031190
        # No Rev 9 production
        # Rev 10
        (share.lots.Range('A183703', 'A184502'), 10),   # 031924
        # Rev 11...                                     # 032434
        ))
    _rev_data = {
        None: J35.values(
            sw_version=J35.sw_15, hw_version=(11, 1, 'A'),
            output_count=7, ocp_set=20.0,
            solar=False, canbus=True,
            ),
        10: J35.values(
            sw_version=J35.sw_15, hw_version=(10, 1, 'A'),
            output_count=7, ocp_set=20.0,
            solar=False, canbus=True,
            ),
        9: J35.values(
            sw_version=J35.sw_15, hw_version=(9, 1, 'B'),
            output_count=7, ocp_set=20.0,
            solar=False, canbus=True,
            ),
        8: J35.values(
            sw_version=J35.sw_15, hw_version=(8, 1, 'C'),
            output_count=7, ocp_set=20.0,
            solar=False, canbus=True,
            ),
        # Rev <8 uses an older software version
        2: J35.values(
            sw_version=J35.sw_13, hw_version=(2, 1, 'B'),
            output_count=7, ocp_set=20.0,
            solar=False, canbus=False,
            ),
        1: J35.values(
            sw_version=J35.sw_13, hw_version=(1, 1, 'B'),
            output_count=7, ocp_set=20.0,
            solar=False, canbus=False,
            ),
        }

    @classmethod
    def limits_initial(cls):
        """J35-A initial test limits.

        @return Tuple of limits

        """
        return super()._base_limits_initial + (
            LimitPercent(
                'OCP_pre', cls.ocp_set,
                (cls.ocp_adjust_percent + 4.0, cls.ocp_adjust_percent + 10.0),
                doc='OCP trip range before adjustment'),
            LimitPercent('OCP', cls.ocp_set, (4.0, 10.0),
                doc='OCP trip range after adjustment'),
            )

    @classmethod
    def limits_final(cls):
        """J35-A final test limits.

        @return Tuple of limits

        """
        return super()._base_limits_final + (
            LimitPercent('OCP', cls.ocp_set, (4.0, 10.0),
                    doc='OCP trip current'),
            )


class J35B(J35):

    """J35B configuration."""

    _lot_rev = share.lots.Revision((
        (share.lots.Range('A164808'), 1),               # 029630
        (share.lots.Range('A170307', 'A174607'), 2),    # 029804
        # No Rev 3,4 production                         # 031051, 031133
        # No Rev 5,6 created
        (share.lots.Range('A174511', 'A180309'), 8),    # 031191
        # Rev 8 Built as Rev 9
        (share.lots.Range('A181011', 'A182405'), 9),    # 031191
        # No Rev 9 production
        # Rev 10
        (share.lots.Range('A183717', 'A184412'), 10),   # 031925
        # Rev 11...                                     # 032435
        ))
    _rev_data = {
        None: J35.values(
            sw_version=J35.sw_15, hw_version=(11, 2, 'A'),
            output_count=14, ocp_set=35.0,
            solar=True, canbus=True,
            ),
        10: J35.values(
            sw_version=J35.sw_15, hw_version=(10, 2, 'A'),
            output_count=14, ocp_set=35.0,
            solar=True, canbus=True,
            ),
        9: J35.values(
            sw_version=J35.sw_15, hw_version=(9, 2, 'B'),
            output_count=14, ocp_set=35.0,
            solar=True, canbus=True,
            ),
        8: J35.values(
            sw_version=J35.sw_15, hw_version=(8, 2, 'C'),
            output_count=14, ocp_set=35.0,
            solar=True, canbus=True,
            ),
        # Rev <8 uses an older software version
        2: J35.values(
            sw_version=J35.sw_13, hw_version=(2, 2, 'D'),
            output_count=14, ocp_set=35.0,
            solar=False, canbus=False,
            ),
        1: J35.values(
            sw_version=J35.sw_13, hw_version=(1, 2, 'B'),
            output_count=14, ocp_set=35.0,
            solar=False, canbus=False,
            ),
        }

    @classmethod
    def limits_initial(cls):
        """J35-B/C/D initial test limits.

        @return Tuple of limits

        """
        return super()._base_limits_initial + (
            LimitPercent(
                'OCP_pre', cls.ocp_set,
                (cls.ocp_adjust_percent + 4.0, cls.ocp_adjust_percent + 7.0),
                doc='OCP trip range before adjustment'),
            LimitPercent('OCP', cls.ocp_set, (4.0, 7.0),
                doc='OCP trip range after adjustment'),
            )

    @classmethod
    def limits_final(cls):
        """J35-B/C final test limits.

        @return Tuple of limits

        """
        return super()._base_limits_final + (
            LimitPercent('OCP', cls.ocp_set, (4.0, 7.0),
                    doc='OCP trip current'),
            )


class J35C(J35B):

    """J35C configuration."""

    _lot_rev = share.lots.Revision((
        # Rev 1-3 must be scrapped per MA-328
        #  There are no entries for Rev1-3 in _rev_data, so there will be
        #  a runtime error, producing a SystemError test result
        (share.lots.Range('A154411'), 1),               # 027745
        (share.lots.Range('A160306'), 2),               # 028388
        (share.lots.Range('A161211'), 3),               # 028861
        (share.lots.Range('A163710', 'A164309'), 4),    # 029129
        # No Rev 5 production                           # 029570
        (share.lots.Range('A164911', 'A171603'), 6),    # 029916
        (share.lots.Range('A171907', 'A173608'), 7),    # 030200
        (share.lots.Range('A174909', 'A180809'), 8),    # 031192
        # Rev 8 Built as Rev 9
        (share.lots.Range('A181409', 'A182207'), 9),    # 031192
        # No Rev 9 production
        # Rev 10
        (share.lots.Range('A184110', 'A184110'), 10),   # 031926
        # Rev 11...                                     # 032436
        ))
    _rev_data = {
        None: J35.values(
            sw_version=J35.sw_15, hw_version=(11, 3, 'A'),
            output_count=14, ocp_set=35.0,
            solar=True, canbus=True,
            ),
        10: J35.values(
            sw_version=J35.sw_15, hw_version=(10, 3, 'A'),
            output_count=14, ocp_set=35.0,
            solar=True, canbus=True,
            ),
        9: J35.values(
            sw_version=J35.sw_15, hw_version=(9, 3, 'B'),
            output_count=14, ocp_set=35.0,
            solar=True, canbus=True,
            ),
        8: J35.values(
            sw_version=J35.sw_15, hw_version=(8, 3, 'C'),
            output_count=14, ocp_set=35.0,
            solar=True, canbus=True,
            ),
        7: J35.values(
            sw_version=J35.sw_15, hw_version=(7, 3, 'C'),
            output_count=14, ocp_set=35.0,
            solar=True, canbus=True,
            ),
        6: J35.values(
            sw_version=J35.sw_15, hw_version=(6, 3, 'E'),
            output_count=14, ocp_set=35.0,
            solar=True, canbus=True,
            ),
        4: J35.values(
            sw_version=J35.sw_15, hw_version=(4, 3, 'B'),
            output_count=14, ocp_set=35.0,
            solar=True, canbus=True,
            ),
        }


class J35D(J35C):

    """J35D configuration."""

    _lot_rev = share.lots.Revision((
        # Rev 8 Built as Rev 9
        (share.lots.Range('A181410', 'A181917'), 9),    # 031193
        # No Rev 9 production
        # Rev 10
        (share.lots.Range('A184113', 'A184113'), 10),   # 031927
        # Rev 11...                                     # 032437
        ))
    _rev_data = {
        None: J35.values(
            sw_version=J35.sw_15, hw_version=(11, 4, 'A'),
            output_count=14, ocp_set=35.0,
            solar=True, canbus=True,
            ),
        10: J35.values(
            sw_version=J35.sw_15, hw_version=(10, 4, 'A'),
            output_count=14, ocp_set=35.0,
            solar=True, canbus=True,
            ),
        9: J35.values(
            sw_version=J35.sw_15, hw_version=(9, 4, 'B'),
            output_count=14, ocp_set=35.0,
            solar=True, canbus=True,
            ),
        }

    @classmethod
    def limits_initial(cls):
        """J35-D initial test limits.

        @return Tuple of limits

        """
        return super().limits_initial() + (
            LimitPercent('SolarCutoffPre', 14.3, percent=6,
                doc='Solar Cut-Off voltage threshold uncertainty'),
            LimitBetween('SolarCutoff', 14.0, 14.6,
                doc='Solar Cut-Off voltage threshold range'),
            )

    @classmethod
    def limits_final(cls):
        """J35-D final test limits.

        @return Tuple of limits

        """
        return super()._base_limits_final + (
            LimitDelta('Vout', 14.0, delta=0.2,
                doc='No load output voltage'),
            LimitPercent('Vload', 14.0, percent=5,
                doc='Loaded output voltage'),
            LimitPercent('OCP', cls.ocp_set * (12.8 / 14.0), (4.0, 7.0),
                    doc='OCP trip current'),
            )
