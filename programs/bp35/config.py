#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 - 2019 SETEC Pty Ltd
"""BP35 / BP35-II Configurations."""

import logging
import enum

import tester
import share


def get(parameter, uut):
    """Get a configuration based on the parameter and lot.

    @param parameter Type of unit (A/B/C)
    @param uut UUT to get Lot Number from
    @return configuration class

    """
    config = {
        'SR': BP35SR,
        'HA': BP35HA,
        'PM': BP35PM,
        'SR2': BP35IISR,
        'HA2': BP35IIHA,
        'SI2': BP35IISI,
        }[parameter]
    config._configure(uut)    # Adjust for the Lot Number
    return config


class Type(enum.IntEnum):

    """Product type numbers for hardware revisions."""

    SR = 1
    PM = 2
    SI = 2
    HA = 3


class BP35():

    """Base configuration. """

    is_2 = False
    # Software versions
    arm_sw_version = '2.0.17344.4603'       # Software Rev 14
    pic_sw_version = '1.5.19286.288'        # Software Rev 10
    pic_hw_version = 4
    # SR Solar Reg settings
    sr_vset = 13.650
    sr_vset_settle = 0.05
    sr_iset = 30.0
    sr_ical = 10.0
    sr_vin = 20.0
    sr_vin_pre_percent = 6.0
    sr_vin_post_percent = 1.5
    # This value is set per Product type & revision
    arm_hw_version = None
    # Injected Vbat & Vaux
    vbat_in = 12.4
    vaux_in = 13.5
    # PFC settling level
    pfc_stable = 0.05
    # Converter loading
    iload = 28.0
    ibatt = 4.0
    # Other settings
    vac = 240.0
    outputs = 14
    vout_set = 12.8
    ocp_set = 35.0
    # Extra % error in OCP allowed before adjustment
    ocp_adjust_percent = 10.0
    # Test limits common to all tests and versions
    _base_limits_all = (
        tester.LimitRegExp('ARM-SwVer', '', doc='Software version'),
        tester.LimitDelta('Vload', 12.45, 0.45, doc='Load output present'),
        tester.LimitLow('InOCP', 11.6, doc='Output voltage in OCP'),
        tester.LimitPercent('OCP', ocp_set, 4.0, doc='After adjustment'),
        )
    # Initial Test limits common to all versions
    _base_limits_initial = _base_limits_all + (
        tester.LimitLow('FixtureLock', 200, doc='Contacts closed'),
        tester.LimitDelta('HwVer8', 4400.0, 250.0, doc='Hardware Rev ≥8'),
        tester.LimitDelta('ACin', vac, 5.0, doc='Injected AC voltage present'),
        tester.LimitBetween('Vpfc', 401.0, 424.0, doc='PFC running'),
        tester.LimitBetween('12Vpri', 11.5, 13.0, doc='Control rail present'),
        tester.LimitBetween('15Vs', 11.5, 13.0, doc='Control rail present'),
        tester.LimitBetween('Vload', 12.0, 12.9, doc='Load output present'),
        tester.LimitLow('VloadOff', 0.5, doc='Load output off'),
        tester.LimitDelta('VbatIn', 12.0, 0.5, doc='Injected Vbatt present'),
        tester.LimitBetween('Vbat', 12.2, 13.0, doc='Vbatt present'),
        tester.LimitDelta('Vaux', 13.4, 0.4, doc='Vaux present'),
        tester.LimitDelta('3V3', 3.30, 0.05, doc='3V3 present'),
        tester.LimitDelta('FanOn', 12.5, 0.5, doc='Fans ON'),
        tester.LimitLow('FanOff', 0.5, doc='Fans OFF'),
        tester.LimitPercent('OCP_pre', ocp_set, 4.0 + ocp_adjust_percent,
            doc='Before adjustment'),
        tester.LimitDelta('ARM-AcV', vac, 10.0, doc='AC voltage'),
        tester.LimitDelta('ARM-AcF', 50.0, 1.0, doc='AC frequency'),
        tester.LimitBetween('ARM-SecT', 8.0, 70.0, doc='Reading ok'),
        tester.LimitDelta('ARM-Vout', 12.45, 0.45),
        tester.LimitBetween('ARM-Fan', 0, 100, doc='Fan running'),
        tester.LimitDelta('ARM-LoadI', 2.1, 0.9, doc='Load current flowing'),
        tester.LimitDelta('ARM-BattI', ibatt, 1.0,
            doc='Battery current flowing'),
        tester.LimitDelta('ARM-BusI', iload + ibatt, 3.0,
            doc='Bus current flowing'),
        tester.LimitPercent('ARM-AuxV', vaux_in, percent=2.0, delta=0.3,
            doc='AUX present'),
        tester.LimitBetween('ARM-AuxI', 0.0, 1.5, doc='AUX current flowing'),
        tester.LimitInteger('ARM-RemoteClosed', 1,
            doc='REMOTE input connected'),
        tester.LimitDelta('CanPwr', vout_set, delta=1.8,
            doc='CAN bus power present'),
        tester.LimitRegExp('CAN_RX', r'^RRQ,32,0', doc='Expected CAN message'),
        tester.LimitInteger('CAN_BIND', 1 << 28, doc='CAN comms established'),
        tester.LimitInteger('Vout_OV', 0, doc='Over-voltage not triggered'),
        )
    # Final Test limits common to all versions
    _base_limits_final = _base_limits_all + (
        tester.LimitDelta('Can12V', 12.0, delta=1.0, doc='CAN_POWER rail'),
        tester.LimitLow('Can0V', 0.5,  doc='CAN BUS removed'),
        tester.LimitHigh('FanOn', 10.0, doc='Fan running'),
        tester.LimitLow('FanOff', 1.0, doc='Fan not running'),
        tester.LimitBetween('Vout', 12.0, 12.9, doc='No load output voltage'),
        )
    # Internal data storage
    _lot_rev = None         # Lot Number to Revision data
    _rev_data = None        # Revision data dictionary

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
        cls.arm_hw_version = cls._rev_data[rev]

    @classmethod
    def limits_initial(cls):
        """Initial test limits.

        @return Tuple of limits

        """
        return cls._base_limits_initial + (
            # SR limits
            tester.LimitDelta('SolarVcc', 3.3, 0.1,
                doc='Vcc present'),
            tester.LimitDelta('SolarVin', cls.sr_vin, 0.5,
                doc='Input present'),
            tester.LimitPercent('VsetPre', cls.sr_vset, 6.0,
                doc='Vout before calibration'),
            tester.LimitPercent('VsetPost', cls.sr_vset, 1.5,
                doc='Vout after calibration'),
            tester.LimitPercent('ARM-IoutPre', cls.sr_ical, (9.0, 20.0),
                doc='Iout before calibration'),
            tester.LimitPercent('ARM-IoutPost', cls.sr_ical, 3.0,
                doc='Iout after calibration'),
            tester.LimitPercent(
                'ARM-SolarVin-Pre', cls.sr_vin, cls.sr_vin_pre_percent,
                doc='Vin before calibration'),
            tester.LimitPercent(
                'ARM-SolarVin-Post', cls.sr_vin, cls.sr_vin_post_percent,
                doc='Vin after calibration'),
            tester.LimitInteger('SR-Alive', 1, doc='Detected'),
            tester.LimitInteger('SR-Relay', 1, doc='Input relay ON'),
            tester.LimitInteger('SR-Error', 0, doc='No error'),
            # PM limits
            tester.LimitInteger('PM-Alive', 1, doc='Detected'),
            tester.LimitDelta('ARM-PmSolarIz-Pre', 0, 0.6,
                doc='Zero reading before cal'),
            tester.LimitDelta('ARM-PmSolarIz-Post', 0, 0.1,
                doc='Zero reading after cal'),
            )

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple of limits

        """
        return cls._base_limits_final


class BP35SR(BP35):

    """BP35SR configuration."""

    is_pm = False
    _lot_rev = share.lots.Revision((
        # Rev 1-5
        (share.lots.Range('A000000', 'A162007'), 'Scrap'),
        # Rev 6
        (share.lots.Range('A162008', 'A163007'), 6),
        # Rev 7
        (share.lots.Range('A163308', 'A163308'), 7),
        # Rev 8
        (share.lots.Range('A164401', 'A170809'), 8),
        # Rev 9
        (share.lots.Range('A171101', 'A172712'), 9),
        # Rev 10
        (share.lots.Range('A173011', 'A173603'), 10),
        # No Rev 11 created
        # Rev 12
        (share.lots.Range('A174403', 'A182506'), 12),
        # Rev 13...
        (share.lots.Range('A182906', 'A194809'), 13),
        # Rev 14...
        ))
    _rev_data = {
        None: (14, Type.SR.value, 'A'),
        13: (13, Type.SR.value, 'B'),
        12: (12, Type.SR.value, 'C'),
        10: (10, Type.SR.value, 'E'),
        9: (9, Type.SR.value, 'E'),
        8: (8, Type.SR.value, 'G'),
        7: (7, Type.SR.value, 'B'),
        6: (6, Type.SR.value, 'C'),
        'Scrap': None,       # This will cause a runtime error
        }


class BP35HA(BP35SR):

    """BP35HA configuration."""

    _lot_rev = share.lots.Revision((
        # No Rev 1-9 created
        # Rev 10
        (share.lots.Range('A173303', 'A173805'), 10),
        # No Rev 11 created
        # Rev 12
        (share.lots.Range('A174403', 'A182506'), 12),
        # Rev 13...
        (share.lots.Range('A182906', 'A194810'), 13),
        # Rev 14...
        ))
    _rev_data = {
        None: (14, Type.HA.value, 'A'),
        13: (13, Type.HA.value, 'B'),
        12: (12, Type.HA.value, 'C'),
        10: (10, Type.HA.value, 'E'),
        }


class BP35PM(BP35):

    """BP35PM configuration."""

    is_pm = True

    # PM Solar Reg settings
    pm_zero_wait = 30   # Settling delay for zero calibration
    _lot_rev = share.lots.Revision((
        # No Rev 1-9 created
        # Rev 10
        (share.lots.Range('A173205', 'A173206'), 10),
        # No Rev 11 created
        # Rev 12
        (share.lots.Range('A174210', 'A182609'), 12),
        # Rev 13...
        (share.lots.Range('A183109', 'A194512'), 13),
        # Rev 14...
        ))
    _rev_data = {
        None: (14, Type.PM.value, 'A'),
        13: (13, Type.PM.value, 'B'),
        12: (12, Type.PM.value, 'C'),
        10: (10, Type.PM.value, 'E'),
        }


class BP35II(BP35):

    """Base configuration for BP35-II."""

    is_2 = True
    # ARM software version
    arm_sw_version = '2.0.19924.5009'


class BP35IISR(BP35II):

    """BP35-IISR configuration."""

    is_pm = False
    _lot_rev = share.lots.Revision((
        ))
    _rev_data = {
        None: (15, Type.SR.value, 'A'),
        }


class BP35IIHA(BP35IISR):

    """BP35-IIHA configuration."""

    _lot_rev = share.lots.Revision((
        ))
    _rev_data = {
        None: (15, Type.HA.value, 'A'),
        }


class BP35IISI(BP35II):

    """BP35-IISI configuration."""

    is_pm = True
    # PM Solar Reg settings
    pm_zero_wait = 30   # Settling delay for zero calibration
    _lot_rev = share.lots.Revision((
        ))
    _rev_data = {
        None: (15, Type.SI.value, 'A'),
        }
