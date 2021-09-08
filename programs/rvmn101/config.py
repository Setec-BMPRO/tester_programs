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
    banner_lines = attr.ib(validator=attr.validators.instance_of(int))
    reversed_output_dict = attr.ib(validator=attr.validators.instance_of(dict))


class Config():

    """Base configuration for RVMN101 and RVMN5x."""

    # These values get set per Product type & revision
    nordic_image = None
    arm_image = None
    product_rev = None
    hardware_rev = None
    banner_lines = None
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
        tester.LimitHigh('HBoff', 8.0, doc='Reversed HBridge off (high)'),
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
        cls.nordic_image = values.nordic_image
        cls.arm_image = values.arm_image
        cls.product_rev = values.product_rev
        cls.hardware_rev = values.hardware_rev
        cls.banner_lines = values.banner_lines
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
    _nordic_2_5_3 = 'jayco_rvmn101_signed_2.5.3-0-ga721738c_factory_mcuboot.hex'
    _nordic_2_6_4 = 'jayco_rvmn101_signed_2.6.4-0-gd1f9eb78_factory_mcuboot.hex'
    _arm_image_1_13 = 'rvmn101_nxp_1.13.bin'
    _arm_image_2_5 = 'rvmn101_nxp_2.5.bin'
    _rev19_values = _Values(    # PC-27477
            nordic_image=_nordic_2_6_4, arm_image=_arm_image_2_5,
            product_rev='19B', hardware_rev='13A', banner_lines=5,
            reversed_output_dict={},
            )
    _rev_data = {
        None: _rev19_values,
        '19': _rev19_values,
        '18': _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_5,
            product_rev='18A', hardware_rev='13A', banner_lines=5,
            reversed_output_dict={},
            ),
        # Rev 17 No production
        '16': _Values(    # Note: ECO had wrong HW rev (15A instead of 12A)
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_5,
            product_rev='16C', hardware_rev='15A', banner_lines=5,
            reversed_output_dict={},
            ),
        # Rev 15 No production
        '14': _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_5,
            product_rev='14D', hardware_rev='11A', banner_lines=5,
            reversed_output_dict={},
            ),
        '13': _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_5,
            product_rev='13B', hardware_rev='11A', banner_lines=5,
            reversed_output_dict={},
            ),
        '12': _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_5,
            product_rev='12C', hardware_rev='11A', banner_lines=5,
            reversed_output_dict={},
            ),
        # Rev 11 No production
        '10': _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_1_13,
            product_rev='10D', hardware_rev='10A', banner_lines=5,
            reversed_output_dict={},
            ),
        '9': _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_1_13,
            product_rev='09D', hardware_rev='08A', banner_lines=5,
            reversed_output_dict=_reversed7to9,
            ),
        '8': _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_1_13,
            product_rev='08D', hardware_rev='08A', banner_lines=5,
            reversed_output_dict=_reversed7to9,
            ),
        '7': _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_1_13,
            product_rev='07D', hardware_rev='07A', banner_lines=5,
            reversed_output_dict=_reversed7to9,
            ),
        '6': _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_1_13,
            product_rev='06H', hardware_rev='06A', banner_lines=5,
            reversed_output_dict={},
            ),
        # Rev 1-5 were Engineering protoype builds
        }

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
    _nordic_2_4_3 = 'tmc_rvmn101_signed_2.4.3-0-g6aa500f5_factory_mcuboot.hex'
    _arm_image_3_0 = 'rvmn101_nxp_3.0.bin'
    _rev16_values = _Values(
            nordic_image=_nordic_2_4_3, arm_image=_arm_image_3_0,
            product_rev='16A', hardware_rev='08B', banner_lines=5,
            reversed_output_dict={},
            )
    _rev_data = {
        None: _rev16_values,
        '16': _rev16_values,
        '15': _Values(
            nordic_image=_nordic_2_4_3, arm_image=_arm_image_3_0,
            product_rev='15A', hardware_rev='8B', banner_lines=5,
            reversed_output_dict={},
            ),
        '14': _Values(
            nordic_image=_nordic_2_4_3, arm_image=_arm_image_3_0,
            product_rev='14C', hardware_rev='8A', banner_lines=5,
            reversed_output_dict={},
            ),
        '13': _Values(
            nordic_image=_nordic_2_4_3, arm_image=_arm_image_3_0,
            product_rev='13D', hardware_rev='8A', banner_lines=5,
            reversed_output_dict={},
            ),
        '12': _Values(
            nordic_image=_nordic_2_4_3, arm_image=_arm_image_3_0,
            product_rev='12F', hardware_rev='6A', banner_lines=5,
            reversed_output_dict={},
            ),
        '11': _Values(
            nordic_image=_nordic_2_4_3, arm_image=_arm_image_3_0,
            product_rev='11F', hardware_rev='6A', banner_lines=5,
            reversed_output_dict={},
            ),
        '10': _Values(
            nordic_image=_nordic_2_4_3, arm_image=_arm_image_3_0,
            product_rev='10G', hardware_rev='6A', banner_lines=5,
            reversed_output_dict={},
            ),
        '9': _Values(
            nordic_image=_nordic_2_4_3, arm_image=_arm_image_3_0,
            product_rev='09G', hardware_rev='6A', banner_lines=5,
            reversed_output_dict={},
            ),
        '8': _Values(
            nordic_image=_nordic_2_4_3, arm_image=_arm_image_3_0,
            product_rev='08H', hardware_rev='6A', banner_lines=5,
            reversed_output_dict={},
            ),
        '7': _Values(
            nordic_image=_nordic_2_4_3, arm_image=_arm_image_3_0,
            product_rev='07G', hardware_rev='6A', banner_lines=5,
            reversed_output_dict={},
            ),
        '6': _Values(
            nordic_image=_nordic_2_4_3, arm_image=_arm_image_3_0,
            product_rev='06H', hardware_rev='6A', banner_lines=5,
            reversed_output_dict={},
            ),
        '5': _Values(
            nordic_image=_nordic_2_4_3, arm_image=_arm_image_3_0,
            product_rev='05G', hardware_rev='6A', banner_lines=5,
            reversed_output_dict={},
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
    _nordic_2_5_3 = 'jayco_rvmn5x_signed_2.5.3-0-ga721738c_factory_mcuboot.hex'
    _nordic_2_6_4 = 'jayco_rvmn5x_signed_2.6.4-0-gd1f9eb78_factory_mcuboot.hex'
    _arm_image_2_3 = 'rvmn5x_nxp_2.3.bin'
    _rev8_values = _Values(     # PC-27478
            nordic_image=_nordic_2_6_4, arm_image=_arm_image_2_3,
            product_rev='08B', hardware_rev='05A', banner_lines=5,
            reversed_output_dict={},
            )
    _rev_data = {
        None: _rev8_values,
        '8': _rev8_values,
        '7': _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_3,
            product_rev='07A', hardware_rev='05A', banner_lines=5,
            reversed_output_dict={},
            ),
        '6': _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_3,
            product_rev='06A', hardware_rev='05A', banner_lines=5,
            reversed_output_dict={},
            ),
        '5': _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_3,
            product_rev='05C', hardware_rev='05A', banner_lines=5,
            reversed_output_dict={},
            ),
        '4': _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_3,
            product_rev='04B', hardware_rev='04A', banner_lines=5,
            reversed_output_dict={},
            ),
        '3': _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_3,
            product_rev='03E', hardware_rev='03A', banner_lines=5,
            reversed_output_dict={},
            ),
        # Rev 1-2 were Engineering protoype builds
        }

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
