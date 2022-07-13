#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMN101x and RVMN5x Configuration."""

import logging

import attr
import tester

import share


def get(parameter, uut):
    """Select a configuration based on the parameter.

    @param parameter Type of unit
    @param uut setec.UUT instance
    @return configuration class

    """
    config = {
        '101A': RVMN101A,
        '101B': RVMN101B,
        '50': RVMN5x,
        '55': RVMN5x,
        }[parameter]
    config._configure(uut)    # Adjust for the revision
    return config


@attr.s
class _Values():

    """Adjustable configuration data values."""

    nordic_image = attr.ib(validator=attr.validators.instance_of(str))
    arm_image = attr.ib(validator=attr.validators.instance_of(str))
    product_rev = attr.ib(validator=attr.validators.instance_of(str))
    hardware_rev = attr.ib()
    reversed_output_dict = attr.ib(
        default={}, validator=attr.validators.instance_of(dict))
    nordic_projectfile = attr.ib(
        default='nrf52.jflash', validator=attr.validators.instance_of(str))
    arm_projectfile = attr.ib(
        default='lpc1519.jflash', validator=attr.validators.instance_of(str))


class Config():

    """Base configuration for RVMN101 and RVMN5x."""

    # These values get set per Product type & revision
    nordic_projectfile = None
    nordic_image = None
    arm_projectfile = None
    arm_image = None
    product_rev = None
    hardware_rev = None
    reversed_output_dict = None
    # General parameters used in testing the units
    #  Injected voltages
    vbatt_set = 12.5
    # Test limits common to both units and test types
    _base_limits = (
        tester.LimitRegExp('BleMac', '^[0-9a-f]{12}$',
            doc='Valid MAC address'),
        )
    # Initial Test limits common to both units
    _base_limits_initial = _base_limits + (
        tester.LimitDelta('Vbatt', vbatt_set - 0.5, 0.5, doc='Battery input'),
        tester.LimitPercent('3V3', 3.3, 6.0, doc='Internal 3V rail'),
        tester.LimitHigh('HSon', 10.0, doc='HS output on (high)'),
        tester.LimitLow('HSoff', 3.0, doc='All HS outputs off (low)'),
        tester.LimitLow('HBon', 2.0, doc='Reversed HBridge on (low)'),
        tester.LimitHigh('HBoff', 6.0, doc='Reversed HBridge off (high)'),
        tester.LimitLow('LSon', 1.0, doc='LS output on (low)'),
        tester.LimitHigh('LSoff', 10.0, doc='LS output off (high)'),
        tester.LimitBoolean('CANok', True, doc='CAN bus active'),
        )
    # Final Test limits common to both units
    _base_limits_final = _base_limits + (
        tester.LimitBoolean('ScanMac', True, doc='MAC address detected'),
        )

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut setec.UUT instance

        """
        try:
            rev = uut.lot.item.revision
        except AttributeError:
            rev = None
        logging.getLogger(__name__).debug('Revision detected as %s', rev)
        values = cls._rev_data[rev]
        cls.nordic_projectfile = values.nordic_projectfile
        cls.nordic_image = values.nordic_image
        cls.arm_projectfile = values.arm_projectfile
        cls.arm_image = values.arm_image
        cls.product_rev = values.product_rev
        cls.hardware_rev = values.hardware_rev
        cls.reversed_output_dict = values.reversed_output_dict

    @classmethod
    def limits_initial(cls):
        """Initial test limits.

        @return Tuple(limits)

        """
        return cls._base_limits_initial

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        return cls._base_limits_final


class RVMN101A(Config):

    """RVMN101A configuration."""

    # Initial Test parameters
    fixture = '033550'
    # Reversed outputs exist on Rev 7,8,9 units
    _reversed7to9 = {       # Key: any text, Value: Output index
            'HBRIDGE 1 EXTEND': 0,
            'HBRIDGE 1 RETRACT': 1,
            'HBRIDGE 2 EXTEND': 2,
            'HBRIDGE 2 RETRACT': 3,
            'HBRIDGE 3 EXTEND': 4,
            'HBRIDGE 3 RETRACT': 5,
            }
    # Software versions
    _nordic_3_0_4 = 'jayco_rvmn101_signed_3.0.4-0-gd3142626_factory_mcuboot.hex'
    _arm_image_1_13 = 'rvmn101_nxp_1.13.bin'
    _arm_image_2_5 = 'rvmn101_nxp_2.5.bin'
    _rev23_values = _Values(
            nordic_image=_nordic_3_0_4, arm_image=_arm_image_2_5,
            product_rev='23B', hardware_rev='21A',  # '21' in the ECO
            )
    _rev_data = {
        None: _rev23_values,
        '23': _rev23_values,
        '22': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_arm_image_2_5,
            product_rev='22B', hardware_rev='20A',  # Not in the ECO
            ),
        '21': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_arm_image_2_5,
            product_rev='21C', hardware_rev='20A',  # '20' in the ECO
            ),
        '20': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_arm_image_2_5,
            product_rev='20C', hardware_rev='14A',
            ),
        '19': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_arm_image_2_5,
            product_rev='19E', hardware_rev='13A',
            ),
        '18': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_arm_image_2_5,
            product_rev='18D', hardware_rev='13A',
            ),
        # Rev 17 No production
        '16': _Values(    # Note: ECO had wrong HW rev (15A instead of 12A)
            nordic_image=_nordic_3_0_4, arm_image=_arm_image_2_5,
            product_rev='16G', hardware_rev='15A',
            ),
        # Rev 15 No production
        '14': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_arm_image_2_5,
            product_rev='14H', hardware_rev='11A',
            ),
        '13': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_arm_image_2_5,
            product_rev='13E', hardware_rev='11A',
            ),
        '12': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_arm_image_2_5,
            product_rev='12F', hardware_rev='11A',
            ),
        # Rev 11 No production
        '10': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_arm_image_1_13,
            product_rev='10G', hardware_rev='10A',
            ),
        # MA-415: Rev <10 "Diagnose and then discard PCB""
        '9': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_arm_image_1_13,
            product_rev='09A', hardware_rev='08A',
            reversed_output_dict=_reversed7to9,
            ),
        '8': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_arm_image_1_13,
            product_rev='08A', hardware_rev='08A',
            reversed_output_dict=_reversed7to9,
            ),
        '7': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_arm_image_1_13,
            product_rev='07A', hardware_rev='07A',
            reversed_output_dict=_reversed7to9,
            ),
        '6': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_arm_image_1_13,
            product_rev='06A', hardware_rev='06A',
            ),
        # Rev 1-5 were Engineering protoype builds
        }

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut setec.UUT instance

        """
        super()._configure(uut)
        # PC-30067
        if uut and uut.lot.number in (
                'A222304', 'A222402', 'A222706', 'A222804'):
            cls.product_rev = '24A'

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        rssi = -70 if share.config.System.tester_type in (
            'ATE4', 'ATE5') else -85
        return cls._base_limits_final + (
            tester.LimitHigh('ScanRSSI', rssi, doc='Strong BLE signal'),
            )


class RVMN101B(Config):

    """RVMN101B configuration."""

    # Initial Test parameters
    fixture = '032871'
    # Software versions
    _nordic_2_4_4 = 'tmc_rvmn101_signed_2.4.4-0-g62755a87_factory_mcuboot.hex'
    _arm_image_3_0 = 'rvmn101_nxp_3.0.bin'
    _rev18_values = _Values(
            nordic_image=_nordic_2_4_4, arm_image=_arm_image_3_0,
            product_rev='18A', hardware_rev='18A',
            )
    _rev_data = {
        None: _rev18_values,
        '18': _rev18_values,
        '17': _Values(
            nordic_image=_nordic_2_4_4, arm_image=_arm_image_3_0,
            product_rev='17A', hardware_rev='08B',
            ),
        '16': _Values(
            nordic_image=_nordic_2_4_4, arm_image=_arm_image_3_0,
            product_rev='16B', hardware_rev='08B',
            ),
        '15': _Values(
            nordic_image=_nordic_2_4_4, arm_image=_arm_image_3_0,
            product_rev='15C', hardware_rev='8B',
            ),
        '14': _Values(
            nordic_image=_nordic_2_4_4, arm_image=_arm_image_3_0,
            product_rev='14E', hardware_rev='8A',
            ),
        '13': _Values(
            nordic_image=_nordic_2_4_4, arm_image=_arm_image_3_0,
            product_rev='13F', hardware_rev='8A',
            ),
        '12': _Values(
            nordic_image=_nordic_2_4_4, arm_image=_arm_image_3_0,
            product_rev='12G', hardware_rev='6A',
            ),
        '11': _Values(
            nordic_image=_nordic_2_4_4, arm_image=_arm_image_3_0,
            product_rev='11G', hardware_rev='6A',
            ),
        '10': _Values(
            nordic_image=_nordic_2_4_4, arm_image=_arm_image_3_0,
            product_rev='10H', hardware_rev='6A',
            ),
        '9': _Values(
            nordic_image=_nordic_2_4_4, arm_image=_arm_image_3_0,
            product_rev='09H', hardware_rev='6A',
            ),
        '8': _Values(
            nordic_image=_nordic_2_4_4, arm_image=_arm_image_3_0,
            product_rev='08I', hardware_rev='6A',
            ),
        '7': _Values(
            nordic_image=_nordic_2_4_4, arm_image=_arm_image_3_0,
            product_rev='07H', hardware_rev='6A',
            ),
        '6': _Values(
            nordic_image=_nordic_2_4_4, arm_image=_arm_image_3_0,
            product_rev='06I', hardware_rev='6A',
            ),
        '5': _Values(
            nordic_image=_nordic_2_4_4, arm_image=_arm_image_3_0,
            product_rev='05H', hardware_rev='6A',
            ),
        # Rev 1-4 were Engineering protoype builds
        }

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        # 3dB below the -A version
        rssi = -73 if share.config.System.tester_type in (
            'ATE4', 'ATE5') else -88
        return cls._base_limits_final + (
            tester.LimitHigh('ScanRSSI', rssi, doc='Strong BLE signal'),
            )


class RVMN5x(Config):

    """RVMN5x configuration."""

    # Initial Test parameters
    fixture = '034861'
    # Software versions
    _nordic_3_0_4 = 'jayco_rvmn5x_signed_3.0.4-0-gd3142626_factory_mcuboot.hex'
    _nxp_image_2_3 = 'rvmn5x_nxp_2.3.bin'
    _ra2_image_0_3_6 = 'rvmn5x_ra2_v0.3.6-0-g34e425b.hex'
    _rev13_values = _Values(
            nordic_image=_nordic_3_0_4, arm_image=_ra2_image_0_3_6,
            product_rev='13B', hardware_rev='10A',
            arm_projectfile='r7fa2l1a9.jflash',
            )
    _rev_data = {
        None: _rev13_values,
        '13': _rev13_values,
        '12': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_nxp_image_2_3,
            product_rev='12B', hardware_rev='08A',
            ),
        '10': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_nxp_image_2_3,
            product_rev='10C', hardware_rev='08A',
            ),
        '9': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_nxp_image_2_3,
            product_rev='09C', hardware_rev='07A',
            ),
        '8': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_nxp_image_2_3,
            product_rev='08E', hardware_rev='05A',
            ),
        '7': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_nxp_image_2_3,
            product_rev='07C', hardware_rev='05A',
            ),
        '6': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_nxp_image_2_3,
            product_rev='06E', hardware_rev='05A',
            ),
        '5': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_nxp_image_2_3,
            product_rev='05H', hardware_rev='05A',
            ),
        '4': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_nxp_image_2_3,
            product_rev='04E', hardware_rev='04A',
            ),
        '3': _Values(
            nordic_image=_nordic_3_0_4, arm_image=_nxp_image_2_3,
            product_rev='03I', hardware_rev='03A',
            ),
        # Rev 1-2 were Engineering protoype builds
        }

    @classmethod
    def _configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut setec.UUT instance

        """
        super()._configure(uut)
        # PC-30068 for RVMN50
        if uut and uut.lot.number in (
                'A222306', 'A222708', 'A222806', 'A222917', 'A223016'):
            cls.product_rev = '14A'

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        rssi = -70 if share.config.System.tester_type in (
            'ATE4', 'ATE5') else -85
        return cls._base_limits_final + (
            tester.LimitHigh('ScanRSSI', rssi, doc='Strong BLE signal'),
            )
