#!/usr/bin/env python3
# Copyright 2023 SETEC Pty Ltd
"""GEN9-540 Configuration."""

import logging

from attrs import define, field, validators

import tester


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
        tester.LimitLow("5Voff", 0.5, doc="5V output off"),
        tester.LimitPercent("5V", 5.10, 2.0, doc="5V output ok"),
        tester.LimitLow("12Voff", 0.5, doc="12V output off"),
        tester.LimitPercent("12V", 12.0, 2.5, doc="12V output ok"),
        tester.LimitLow("24Voff", 0.5, doc="24V output off"),
        tester.LimitPercent("24V", 24.0, 2.5, doc="24V output ok"),
        tester.LimitLow("PwrFail", 0.4, doc="PFAIL asserted"),
        tester.LimitHigh("PwrFailOff", 11.0, doc="PFAIL not asserted"),
    )
    # Initial Test limits
    limits_initial = _limits_common + (
        tester.LimitHigh("FanShort", 500),
        tester.LimitLow("FixtureLock", 200),
        tester.LimitPercent("3V3", 3.30, 10.0),
        tester.LimitPercent("5Vset", 5.137, 1.0),
        tester.LimitDelta("ACin", 240, 10),
        tester.LimitBetween("15Vccpri", 11.4, 17.0),
        tester.LimitBetween("12Vpri", 11.4, 17.0),
        tester.LimitBetween("PFCpre", 408, 450),
        tester.LimitDelta("PFCpost1", 426.0, 2.9),
        tester.LimitDelta("PFCpost2", 426.0, 2.9),
        tester.LimitDelta("PFCpost3", 426.0, 2.9),
        tester.LimitDelta("PFCpost4", 426.0, 2.9),
        tester.LimitDelta("PFCpost", 426.0, 3.0),
        tester.LimitBetween("HoldUpTime", 0.050 * 1.2, 1, doc="50ms + 20% for ageing"),
        tester.LimitDelta("ARM-AcFreq", 50, 10),
        tester.LimitDelta("ARM-AcVolt", 240, 20),
        tester.LimitDelta("ARM-5V", 5.0, 1.0),
        tester.LimitDelta("ARM-12V", 12.0, 1.0),
        tester.LimitDelta("ARM-24V", 24.0, 2.0),
    )
    # Final Test limits
    limits_final = _limits_common + (
        tester.LimitLow("FanOff", 9.0, doc="Airflow not present"),
        tester.LimitHigh("FanOn", 11.0, doc="Airflow present"),
        tester.LimitDelta("GPO1out", 240, 10, doc="Voltage present"),
        tester.LimitDelta("GPO2out", 240, 10, doc="Voltage present"),
        tester.LimitLow("12Vmax", 0.045, doc="12V transient ok"),
    )
    # Software image filename
    _lpc_values = _Values(
        devicetype="lpc1113",
        sw_image="gen9_1.0.18392.2512.bin",
        pfc_trim=True,
    )
    _renesas_values = _Values(
        devicetype="r7fa2e1a7",
        sw_image="gen9_renesas_1.1.0-0-g6d37938.hex",
        pfc_trim=False,
    )
    _rev_data = {
        "G": {  # GEN9-540-G (Gold)
            None: _renesas_values,
            "2": _renesas_values,
            # Rev 1 was Engineering protoype build
        },
        "S": {  # GEN9-540 (Silver)
            None: _renesas_values,
            "8A": _renesas_values,
            "7A": _renesas_values,
            "6C": _lpc_values,
            "6B": _lpc_values,
            "6A": _lpc_values,
            "5": _lpc_values,
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
