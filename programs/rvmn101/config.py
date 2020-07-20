#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 SETEC Pty Ltd.
"""RVMN101x and RVMN5x Configuration."""

import logging

import attr
import tester

import share


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

    @staticmethod
    def get(parameter, uut):
        """Select a configuration based on the parameter.

        @param parameter Type of unit (A/B)
        @param uut UUT to get Lot Number from
        @return configuration class

        """
        config = {
            '101A': RVMN101A,
            '101B': RVMN101B,
            '50': RVMN5x,
            '55': RVMN5x,
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
    _nordic_133 = 'jayco_rvmn101_signed_1.3.3-0-g123e32e_factory_mcuboot.hex'
    _nordic_181 = 'jayco_rvmn101_signed_1.8.1-0-ge5395312_factory_mcuboot.hex'
    _nordic_1106 = 'jayco_rvmn101_signed_1.10.6-0-g2d00e43c_factory_mcuboot.hex'
    _nordic_1114 = 'jayco_rvmn101_signed_1.11.4-0-g9d4939df_factory_mcuboot.hex'
    _arm_image_19 = 'rvmn101_nxp_1.9.bin'
    _arm_image_113 = 'rvmn101_nxp_1.13.bin'
    # Lot number mapping
    _lot_rev = share.lots.Revision((
        # Rev 1-4 were Engineering protoype builds
        (share.lots.Range('A191913', 'A192407'), 5),    # 033363
        (share.lots.Range('A192709', 'A192904'), 6),    # 033620
        (share.lots.Range('A192815', 'A194129'), 7),    # 033489
        (share.lots.Range('A194210', 'A195015'), 8),    # 033585
        (share.lots.Range('A195129', 'A201109'), 9),    # 034079
        # Rev 10... A201218...                          # 034447
        ))
    _rev_data = {
        None: _Values(
            nordic_image=_nordic_1114, arm_image=_arm_image_113,
            product_rev='10A', hardware_rev='10A', banner_lines=6,
            reversed_output_dict={},
            ),
        9: _Values(
            nordic_image=_nordic_1106, arm_image=_arm_image_113,
            product_rev='09A', hardware_rev='08A', banner_lines=6,
            reversed_output_dict=_reversed7to9,
            ),
        8: _Values(
            nordic_image=_nordic_181, arm_image=_arm_image_19,
            product_rev='08A', hardware_rev='08A', banner_lines=4,
            reversed_output_dict=_reversed7to9,
            ),
        7: _Values(
            nordic_image=_nordic_133, arm_image=_arm_image_19,
            product_rev='07A', hardware_rev='07A', banner_lines=4,
            reversed_output_dict=_reversed7to9,
            ),
        6: _Values(
            nordic_image='dunno', arm_image=_arm_image_19,
            product_rev='06A', hardware_rev='06A', banner_lines=4,
            reversed_output_dict={},
            ),
        5: _Values(
            nordic_image='dunno', arm_image=_arm_image_19,
            product_rev='05A', hardware_rev='05A', banner_lines=4,
            reversed_output_dict={},
            ),
        }

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        rssi = -70 if share.config.System.tester_type == 'ATE4' else -85
        return cls._base_limits_final + (
            tester.LimitHigh('ScanRSSI', rssi, doc='Strong BLE signal'),
            )


class RVMN101B(Config):

    """RVMN101B configuration."""

    # Initial Test parameters
    fixture = '032871'
    # Software versions
    #   Firmware 0.88 does not support hardware_rev
    _nordic_088 = 'tmc_rvmn101_signed_0.88-0-g5f64a82_factory_mcuboot.hex'
    _nordic_089 = 'tmc_rvmn101_signed_0.89-0-g9fc6374f_factory_mcuboot.hex'
    _nordic_092 = 'tmc_rvmn101_signed_0.92-0-g015c3552_factory_mcuboot.hex'
    _arm_image_19 = 'rvmn101_nxp_1.9.bin'
    # Lot number mapping
    _lot_rev = share.lots.Revision((
        (share.lots.Range('A191809', 'A200510'), 5),    # 033280
        (share.lots.Range('A200820', 'A202704'), 6),    # 034229
        (share.lots.Range('A202722', 'A203113'), 7),    # 034940
        # Rev 8...                                      # 035120
        ))
    _rev_data = {
        None: _Values(
            nordic_image=_nordic_092, arm_image=_arm_image_19,
            product_rev='08A', hardware_rev=None, banner_lines=4,
            reversed_output_dict={},
            ),
        7: _Values(
            nordic_image=_nordic_089, arm_image=_arm_image_19,
            product_rev='07A', hardware_rev=None, banner_lines=4,
            reversed_output_dict={},
            ),
        6: _Values(
            nordic_image=_nordic_089, arm_image=_arm_image_19,
            product_rev='06B', hardware_rev=None, banner_lines=4,
            reversed_output_dict={},
            ),
        5: _Values(
            nordic_image=_nordic_088, arm_image=_arm_image_19,
            product_rev='05B', hardware_rev=None, banner_lines=4,
            reversed_output_dict={},
            ),
        }

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        # 3dB below the -A version
        rssi = -73 if share.config.System.tester_type == 'ATE4' else -88
        return cls._base_limits_final + (
            tester.LimitHigh('ScanRSSI', rssi, doc='Strong BLE signal'),
            )


class RVMN5x(Config):

    """RVMN5x configuration."""

    # Initial Test parameters
    fixture = '034861'
    # Software versions
    _nordic_206 = 'jayco_rvmn5x_signed_2.0.6-0-g85ac8960_factory_mcuboot.hex'
    _arm_image_23 = 'rvmn5x_nxp_2.3.bin'
    # Lot number mapping
    _lot_rev = share.lots.Revision((
        # Rev 1-2 were Engineering protoype builds
        (share.lots.Range('A201801', 'A202213'), 3),
        # Rev 4...
        ))
    _rev_data = {
        None: _Values(
            nordic_image=_nordic_206, arm_image=_arm_image_23,
            product_rev='04A', hardware_rev='04A', banner_lines=5,
            reversed_output_dict={},
            ),
        3: _Values(
            nordic_image=_nordic_206, arm_image=_arm_image_23,
            product_rev='03C', hardware_rev='03A', banner_lines=5,
            reversed_output_dict={},
            ),
        }

    @classmethod
    def limits_final(cls):
        """Final test limits.

        @return Tuple(limits)

        """
        rssi = -70 if share.config.System.tester_type == 'ATE4' else -88
        return cls._base_limits_final + (
            tester.LimitHigh('ScanRSSI', rssi, doc='Strong BLE signal'),
            )
