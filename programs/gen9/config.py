#!/usr/bin/env python3
# Copyright 2023 SETEC Pty Ltd
"""GEN9-540 Configuration."""

import logging

from attrs import define, field, validators

import libtester


@define
class _Values:
    """Adjustable configuration data values."""

    devicetype = field(validator=validators.instance_of(str))
    sw_image = field(validator=validators.instance_of(str))
    pfc_trim = field(validator=validators.instance_of(bool))


class Config:
    """Configuration."""

    # These values get set per Product revision
    devicetype = None
    sw_image = None
    pfc_trim = None
    # Common Test limits common to both test types
    _limits_common = (
        libtester.LimitLow("5Voff", 0.5, doc="5V output off"),
        libtester.LimitPercent("5V", 5.10, 2.0, doc="5V output ok"),
        libtester.LimitLow("12Voff", 0.5, doc="12V output off"),
        libtester.LimitPercent("12V", 12.0, 2.5, doc="12V output ok"),
        libtester.LimitLow("24Voff", 0.5, doc="24V output off"),
        libtester.LimitPercent("24V", 24.0, 2.5, doc="24V output ok"),
        libtester.LimitLow("PwrFail", 0.4, doc="PFAIL asserted"),
        libtester.LimitHigh("PwrFailOff", 11.0, doc="PFAIL not asserted"),
    )
    # Initial Test limits
    limits_initial = _limits_common + (
        libtester.LimitHigh("FanShort", 500),
        libtester.LimitLow("FixtureLock", 200),
        libtester.LimitPercent("3V3", 3.30, 10.0),
        libtester.LimitPercent("5Vset", 5.137, 1.0),
        libtester.LimitDelta("ACin", 240, 10),
        libtester.LimitBetween("15Vccpri", 11.4, 17.0),
        libtester.LimitBetween("12Vpri", 11.4, 17.0),
        libtester.LimitBetween("PFCpre", 408, 450),
        libtester.LimitDelta("PFCpost1", 426.0, 2.9),
        libtester.LimitDelta("PFCpost2", 426.0, 2.9),
        libtester.LimitDelta("PFCpost3", 426.0, 2.9),
        libtester.LimitDelta("PFCpost4", 426.0, 2.9),
        libtester.LimitDelta("PFCpost", 426.0, 3.0),
        libtester.LimitBetween(
            "HoldUpTime", 0.050 * 1.2, 1, doc="50ms + 20% for ageing"
        ),
        libtester.LimitDelta("ARM-AcFreq", 50, 10),
        libtester.LimitDelta("ARM-AcVolt", 240, 20),
        libtester.LimitDelta("ARM-5V", 5.0, 1.0),
        libtester.LimitDelta("ARM-12V", 12.0, 1.0),
        libtester.LimitDelta("ARM-24V", 24.0, 2.0),
    )
    # Final Test limits
    limits_final = _limits_common + (
        libtester.LimitLow("FanOff", 9.0, doc="Airflow not present"),
        libtester.LimitHigh("FanOn", 11.0, doc="Airflow present"),
        libtester.LimitDelta("GPO1out", 240, 10, doc="Voltage present"),
        libtester.LimitDelta("GPO2out", 240, 10, doc="Voltage present"),
        libtester.LimitLow("12Vmax", 0.045, doc="12V transient ok"),
    )
    # Software image filename
    _silver_nxp_values = _Values(
        devicetype="lpc1113",
        sw_image="gen9_1.0.18392.2512.bin",
        pfc_trim=True,
    )
    _silver_renesas_values = _Values(
        devicetype="r7fa2e1a7",
        sw_image="gen9_renesas_1.1.0-0-g6d37938.hex",
        pfc_trim=False,
    )
    _gold_values = _Values(
        devicetype="r7fa2e1a7",
        sw_image="gen9g_1.2.0-0-g2d5106a.hex",
        pfc_trim=True,
    )
    _rev_data = {
        "G": {  # GEN9-540-G (Gold)
            None: _gold_values,
            "3": _gold_values,
            "2": _silver_renesas_values,
            # Rev 1 was Engineering protoype build
        },
        "S": {  # GEN9-540 (Silver)
            None: _silver_renesas_values,
            "8A": _silver_renesas_values,
            "7A": _silver_renesas_values,
            "6C": _silver_nxp_values,
            "6B": _silver_nxp_values,
            "6A": _silver_nxp_values,
            "5": _silver_nxp_values,
            # Rev 1-4 were Engineering protoype builds
        },
    }

    @classmethod
    def configure(cls, parameter, uut):
        """Adjust configuration based on UUT Lot Number.

        @param parameter Product selector
        @param uut libtester.UUT instance

        """
        rev = uut.revision
        logging.getLogger(__name__).debug("Revision detected as %s", rev)
        values = cls._rev_data[parameter][rev]
        cls.devicetype = values.devicetype
        cls.sw_image = values.sw_image
        cls.pfc_trim = values.pfc_trim
