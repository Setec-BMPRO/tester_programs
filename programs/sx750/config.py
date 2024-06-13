#!/usr/bin/env python3
# Copyright 2013 SETEC Pty Ltd
"""SX-750 Configuration."""

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


class Config:
    """Configuration."""

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
    # Initial Test parameters
    #  Software version
    _bin_version = "3.1.2118"
    #  Software image filenames
    arm_bin = "sx750_arm_{0}.bin".format(_bin_version)
    #  Fan ON threshold temperature (C)
    fan_threshold = 55.0
    # 12V & 24V output ratings (A)
    ratings = Ratings(
        v12=Rail(full=32.0, peak=36.0, ocp=36.6),
        v24=Rail(full=15.0, peak=18.0, ocp=18.3),
    )
    # Common Test limits common to both test types & units
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
        libtester.LimitPercent("5Vnl", 5.10, 1.5),
        libtester.LimitPercent("12Vnl", 12.25, 2.0),
        libtester.LimitPercent("24Vnl", 24.13, 2.0),
        # Load regulation (values in %)
        libtester.LimitBetween("Reg12V", 0.2, 5.0),
        libtester.LimitBetween("Reg24V", 0.2, 7.5),
    )
    # Initial Test limits common to both units
    limits_initial = _limits_common + (
        # Load regulation (values in %)
        libtester.LimitLow("Reg5V", 3.0),
        libtester.LimitDelta("8.5V Arduino", 8.5, 0.4),
        libtester.LimitLow("FixtureLock", 200),
        libtester.LimitLow("PartCheck", 1.0),  # Photo sensor on D404
        libtester.LimitBetween("Snubber", 1000, 3000),  # Snubbing resistors
        libtester.LimitRegExp("Reply", "^OK$"),
        libtester.LimitInteger("Program", 0),
        libtester.LimitDelta("3V3", 3.3, 0.1),
        libtester.LimitDelta("ACin", 240, 10),
        libtester.LimitLow("ARM-AcFreq", 999),
        libtester.LimitLow("ARM-AcVolt", 999),
        libtester.LimitLow("ARM-12V", 999),
        libtester.LimitLow("ARM-24V", 999),
        libtester.LimitDelta("5Vext", _5vsb_ext - 0.8, 1.0),
        libtester.LimitDelta("5Vunsw", _5vsb_ext - 0.8 - 0.7, 1.0),
        libtester.LimitHigh("12V_inOCP", 4.0),  # Detect OCP when TP405>4V
        libtester.LimitHigh("24V_inOCP", 4.0),  # Detect OCP when TP404>4V
        libtester.LimitBetween("12V_ocp", 4, 63),  # Digital Pot setting
        libtester.LimitBetween("24V_ocp", 4, 63),  # Digital Pot setting
        libtester.LimitBetween("PriCtl", 11.40, 17.0),
        libtester.LimitDelta("PFCpre", 420, 20),
        libtester.LimitDelta("PFCpost", pfc_target, 1.0),
        libtester.LimitDelta("12V_OCPchk", ratings.v12.ocp, 0.4),
        libtester.LimitDelta("24V_OCPchk", ratings.v24.ocp, 0.2),
        libtester.LimitRegExp(
            "ARM-SwVer", "^{0}$".format(r"\.".join(_bin_version.split(".")[:2]))
        ),
        libtester.LimitRegExp("ARM-SwBld", "^{0}$".format(_bin_version.split(".")[2])),
    )
    # Final Test limits common to both units
    limits_final = _limits_common + (
        libtester.LimitLow("IECoff", 0.5),
        libtester.LimitDelta("IEC", 240, 5),
        libtester.LimitDelta("InRes", 70000, 10000),
        libtester.LimitHigh("FanOff", 3.0),
        libtester.LimitLow("FanOn", 2.0),
        libtester.LimitLow("BracketDetect", 1.0),
    )
