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
    _nordic_2_5_3 = 'jayco_rvmn101_signed_2.5.3-0-ga721738c_factory_mcuboot.hex'
    _arm_image_1_13 = 'rvmn101_nxp_1.13.bin'
    _arm_image_2_5 = 'rvmn101_nxp_2.5.bin'
    # Lot number mapping
    _lot_rev = share.lots.Revision((
        # Rev 1-5 were Engineering protoype builds
        (share.lots.Range('A192709', 'A192904'), 6),    # 033620 MA358
        (share.lots.Range('A192815', 'A194129'), 7),    # 033489 MA358
        (share.lots.Range('A194210', 'A195015'), 8),    # 033585 MA358
        (share.lots.Range('A195129', 'A201109'), 9),    # 034079 MA358
        (share.lots.Range('A201218', 'A203611'), 10),   # 034447 MA358/PC23237
        # Rev 11 No production                          # 035079
        (share.lots.Range('A203612', 'A204008'), 12.1), # 034879 PC23652
        (share.lots.Range('A204017', 'A204607'), 13),   # 035323
        (share.lots.Range('A204724', 'A210637'), 14),   # 035461
        # Rev 15 No production                          # 035611
        (share.lots.Range('A210735', 'A210903'), 16),   # 035639
        (share.lots.Range('A211027', 'A211411'), 14),   # 035461
        (share.lots.Range('A211718', 'A211718'), 16),   # 035639
        # Rev 17 No production                          # 035611
        # Rev 18...                                     # 036061
        ))
    _rev_data = {
        None: _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_5,
            product_rev='18A', hardware_rev='13A', banner_lines=5,
            reversed_output_dict={},
            ),
        16: _Values(    # Note: ECO had wrong HW rev (15A)
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_5,
            product_rev='16C', hardware_rev='15A', banner_lines=5,
            reversed_output_dict={},
            ),
        14: _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_5,
            product_rev='14D', hardware_rev='11A', banner_lines=5,
            reversed_output_dict={},
            ),
        13: _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_5,
            product_rev='13B', hardware_rev='11A', banner_lines=5,
            reversed_output_dict={},
            ),
        12.1: _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_5,
            product_rev='12C', hardware_rev='11A', banner_lines=5,
            reversed_output_dict={},
            ),
        10: _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_1_13,
            product_rev='10D', hardware_rev='10A', banner_lines=5,
            reversed_output_dict={},
            ),
        9: _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_1_13,
            product_rev='09D', hardware_rev='08A', banner_lines=5,
            reversed_output_dict=_reversed7to9,
            ),
        8: _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_1_13,
            product_rev='08D', hardware_rev='08A', banner_lines=5,
            reversed_output_dict=_reversed7to9,
            ),
        7: _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_1_13,
            product_rev='07D', hardware_rev='07A', banner_lines=5,
            reversed_output_dict=_reversed7to9,
            ),
        6: _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_1_13,
            product_rev='06H', hardware_rev='06A', banner_lines=5,
            reversed_output_dict={},
            ),
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
    _nordic_2_4_2 = 'tmc_rvmn101_signed_2.4.2-0-g72f2a9c7_factory_mcuboot.hex'
    _arm_image_3_0 = 'rvmn101_nxp_3.0.bin'
    # Lot number mapping
    _lot_rev = share.lots.Revision((
        (share.lots.Range('A191809', 'A200510'), 5),    # 033280
        (share.lots.Range('A200820', 'A202704'), 6),    # 034229
        (share.lots.Range('A202722', 'A202809'), 7),    # 034940
        (share.lots.Range('A202907', 'A203113'), 7.1),  # 034940 PC-22885
        (share.lots.Range('A203303', 'A203303'), 8.1),  # 035120 PC-23228
        (share.lots.Range('A203508', 'A203717'), 9),    # 035231
        (share.lots.Range('A204007', 'A204106'), 10),   # 035280
        (share.lots.Range('A204116', 'A204307'), 11),   # 035332
        (share.lots.Range('A204722', 'A204722'), 12),   # 035416
        (share.lots.Range('A204931', 'A211012'), 13),   # 035213 PC-25789 MA???
        # 035814 PC-25789
        ))
    _rev_data = {
        None: _Values(
            nordic_image=_nordic_2_4_2, arm_image=_arm_image_3_0,
            product_rev='14B', hardware_rev='8A', banner_lines=5,
            reversed_output_dict={},
            ),
        13: _Values(
            nordic_image=_nordic_2_4_2, arm_image=_arm_image_3_0,
            product_rev='13D', hardware_rev='8A', banner_lines=5,
            reversed_output_dict={},
            ),
        12: _Values(
            nordic_image=_nordic_2_4_2, arm_image=_arm_image_3_0,
            product_rev='12F', hardware_rev='6A', banner_lines=5,
            reversed_output_dict={},
            ),
        11: _Values(
            nordic_image=_nordic_2_4_2, arm_image=_arm_image_3_0,
            product_rev='11F', hardware_rev='6A', banner_lines=5,
            reversed_output_dict={},
            ),
        10: _Values(
            nordic_image=_nordic_2_4_2, arm_image=_arm_image_3_0,
            product_rev='10G', hardware_rev='6A', banner_lines=5,
            reversed_output_dict={},
            ),
        9: _Values(
            nordic_image=_nordic_2_4_2, arm_image=_arm_image_3_0,
            product_rev='09F', hardware_rev='6A', banner_lines=5,
            reversed_output_dict={},
            ),
        8.1: _Values(
            nordic_image=_nordic_2_4_2, arm_image=_arm_image_3_0,
            product_rev='08H', hardware_rev='6A', banner_lines=5,
            reversed_output_dict={},
            ),
        7.1: _Values(
            nordic_image=_nordic_2_4_2, arm_image=_arm_image_3_0,
            product_rev='08H', hardware_rev='6A', banner_lines=5,
            reversed_output_dict={},
            ),
        7: _Values(
            nordic_image=_nordic_2_4_2, arm_image=_arm_image_3_0,
            product_rev='07G', hardware_rev='6A', banner_lines=5,
            reversed_output_dict={},
            ),
        6: _Values(
            nordic_image=_nordic_2_4_2, arm_image=_arm_image_3_0,
            product_rev='06H', hardware_rev='6A', banner_lines=5,
            reversed_output_dict={},
            ),
        5: _Values(
            nordic_image=_nordic_2_4_2, arm_image=_arm_image_3_0,
            product_rev='05G', hardware_rev='6A', banner_lines=5,
            reversed_output_dict={},
            ),
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
    _arm_image_2_3 = 'rvmn5x_nxp_2.3.bin'
    # Lot number mapping
    _lot_rev = share.lots.Revision((
        # Rev 1-2 were Engineering protoype builds
        (share.lots.Range('A201801', 'A202412'), 3),    # 034789, 035009
        (share.lots.Range('A202507', 'A203003'), 4),    # 035090, 035091
        (share.lots.Range('A203118', 'A211611'), 5),    # 035224, 035225
        (share.lots.Range('A211612', 'A211903'), 6),    # 035818, 035819
#        (share.lots.Range('A211904', 'Axxxxxx'), 7),    # 036075, 036076
        # Rev 7...
        ))
    _rev_data = {
        None: _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_3,
            product_rev='07A', hardware_rev='05A', banner_lines=5,
            reversed_output_dict={},
            ),
        6: _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_3,
            product_rev='06A', hardware_rev='05A', banner_lines=5,
            reversed_output_dict={},
            ),
        5: _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_3,
            product_rev='05C', hardware_rev='05A', banner_lines=5,
            reversed_output_dict={},
            ),
        4: _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_3,
            product_rev='04B', hardware_rev='04A', banner_lines=5,
            reversed_output_dict={},
            ),
        3: _Values(
            nordic_image=_nordic_2_5_3, arm_image=_arm_image_2_3,
            product_rev='03E', hardware_rev='03A', banner_lines=5,
            reversed_output_dict={},
            ),
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
