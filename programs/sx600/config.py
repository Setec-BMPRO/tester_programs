#!/usr/bin/env python3
# Copyright 2013 SETEC Pty Ltd
"""SX-600 Configuration."""

import logging

from attrs import define, field, validators

import libtester


@define
class Rail:
    """Rail data values."""

    full = field(validator=validators.instance_of(float))
    peak = field(validator=validators.instance_of(float))
    ocp = field(validator=validators.instance_of(float))


@define
class Ratings:
    """Ratings data values."""

    v12 = field(validator=validators.instance_of(Rail))
    v24 = field(validator=validators.instance_of(Rail))


@define
class _Values:
    """Adjustable configuration data values."""

    devicetype = field(validator=validators.instance_of(str))
    sw_image = field(validator=validators.instance_of(str))
    is_renesas = field(validator=validators.instance_of(bool))


class Config:
    """Configuration."""

    # These values get set per Product revision
    devicetype = None
    sw_image = None
    is_renesas = None
    # General parameters used in testing the units
    #  Injected voltages
    _5vsb_ext = 6.3
    prictl_ext = 13.0
    #  Post-adjustment PFC voltage
    pfc_target = 435.0
    #  Reading to reading difference for PFC voltage stability
    pfc_stable = 0.05
    # Final Test parameters
    #  Injected voltage at PS_ON via diode and 100R to prevent startup.
    disable_pwr = 5.5
    #  Injected voltage for fan and bracket detect circuits
    part_detect = 12.0
    fixture_fan = 12.0
    # PFC digital pot sensitivity (V/step)
    pfc_volt_per_step = 1.5
    # 12V & 24V output ratings (A)
    #  24V OCP spec is 12.1A to 16.2A == 14.15 ± 2.05A
    ratings = Ratings(
        v12=Rail(full=30.0, peak=32.0, ocp=33.0),
        v24=Rail(full=10.0, peak=12.0, ocp=14.15),
    )
    # Common Test limits common to both test types
    _limits_common = (
        # Outputs off
        libtester.LimitLow("5Voff", 0.5),
        libtester.LimitLow("12Voff", 0.5),
        libtester.LimitLow("24Voff", 0.5),
        # Full Load
        libtester.LimitPercent("5Vfl", 5.0, 4.5),
        libtester.LimitPercent("12Vfl", 12.0, 6.5),
        libtester.LimitPercent("24Vfl", 24.0, 9.0),
        # Signals
        libtester.LimitDelta("ACFAIL", 5.0, 0.5),
        libtester.LimitLow("ACOK", 0.5),
        libtester.LimitLow("PGOOD", 0.5),
        # Voltages
        libtester.LimitPercent("5Vnl", 5.08, 1.0),
        libtester.LimitPercent("12Vnl", 11.98, 1.3),
        libtester.LimitPercent("24Vnl", 24.03, 1.4),
        # Load regulation (values in %)
        libtester.LimitBetween("Reg12V", -0.05, 5.0),
        libtester.LimitBetween("Reg24V", -0.05, 7.5),
    )
    # Initial Test limits
    limits_initial = _limits_common + (
        # Load regulation (values in %)
        libtester.LimitLow("Reg5V", 3.0),
        libtester.LimitDelta("8.5V Arduino", 8.5, 0.4),
        libtester.LimitLow("FixtureLock", 200),
        libtester.LimitBetween("Snubber", 1000, 3000),  # Snubbing resistors
        libtester.LimitRegExp("Reply", "^OK$"),
        libtester.LimitInteger("Program", 0),
        libtester.LimitDelta("3V3", 3.3, 0.15),
        libtester.LimitDelta("ACin", 240, 10),
        libtester.LimitLow("ARM-AcFreq", 999),
        libtester.LimitLow("ARM-AcVolt", 999),
        libtester.LimitLow("ARM-12V", 999),
        libtester.LimitLow("ARM-24V", 999),
        libtester.LimitDelta("5Vext", _5vsb_ext - 0.8, 1.0),
        libtester.LimitDelta("5Vunsw", _5vsb_ext - 0.8 - 0.7, 1.0),
        libtester.LimitHigh("12V_inOCP", 4.0),  # Detect OCP when TP4 > 4V
        libtester.LimitHigh("24V_inOCP", 4.0),  # Detect OCP when TP5 > 4V
        libtester.LimitBetween("OCPset", 4, 63),  # Digital Pot setting
        libtester.LimitBetween("PriCtl", 12.0, 14.5),
        libtester.LimitDelta("PFCpre", pfc_target, 30),
        libtester.LimitDelta("PFCpost", pfc_target, 2.0),
        libtester.LimitDelta("12V_OCPchk", ratings.v12.ocp, 0.5),
        libtester.LimitDelta("24V_OCPchk", ratings.v24.ocp, 2.05),
    )
    # Final Test limits
    limits_final = _limits_common + (
        libtester.LimitLow("IECoff", 0.5),
        libtester.LimitDelta("IEC", 240, 5),
        libtester.LimitDelta("InRes", 70000, 10000),
        libtester.LimitHigh("FanOff", 3.0),
        libtester.LimitLow("FanOn", 2.0),
        libtester.LimitLow("BracketDetect", 1.0),
    )
    # Software images
    _renesas_values = _Values(
        devicetype="r7fa2e1a7",
        sw_image="sx600_renesas_1.0.0-0-gfd443df.hex",
        is_renesas=True,
    )
    _rev_data = {
        None: _renesas_values,
        "6": _renesas_values,
        "5": _renesas_values,
        "4": _Values(
            devicetype="lpc1113",
            sw_image="sx600_1.3.19535.1537.bin",
            is_renesas=False,
        ),
        # Rev 1-3 were Engineering protoype builds
    }

    @classmethod
    def configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut libtester.UUT instance

        """
        rev = uut.revision
        logging.getLogger(__name__).debug("Revision detected as %s", rev)
        values = cls._rev_data[rev]
        cls.devicetype = values.devicetype
        cls.sw_image = values.sw_image
        cls.is_renesas = values.is_renesas
