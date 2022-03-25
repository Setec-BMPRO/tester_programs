#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2013 SETEC Pty Ltd
"""SX-600 Configuration."""

import logging

import attr

import tester


@attr.s
class Rail():
    """Rail data values."""
    full = attr.ib(validator=attr.validators.instance_of(float))
    peak = attr.ib(validator=attr.validators.instance_of(float))
    ocp = attr.ib(validator=attr.validators.instance_of(float))


@attr.s
class Ratings():
    """Ratings data values."""
    v12 = attr.ib(validator=attr.validators.instance_of(Rail))
    v24 = attr.ib(validator=attr.validators.instance_of(Rail))


@attr.s
class _Values():

    """Adjustable configuration data values."""

    projectfile = attr.ib(validator=attr.validators.instance_of(str))
    sw_image = attr.ib(validator=attr.validators.instance_of(str))


class Config():

    """Configuration."""

    # These values get set per Product revision
    projectfile = None
    sw_image = None
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
        v24=Rail(full=10.0, peak=12.0, ocp=14.15)
        )
    # Common Test limits common to both test types
    _limits_common = (
        # Outputs off
        tester.LimitLow('5Voff', 0.5),
        tester.LimitLow('12Voff', 0.5),
        tester.LimitLow('24Voff', 0.5),
        # Full Load
        tester.LimitPercent('5Vfl', 5.0, 4.5),
        tester.LimitPercent('12Vfl', 12.0, 6.5),
        tester.LimitPercent('24Vfl', 24.0, 9.0),
        # Signals
        tester.LimitDelta('ACFAIL', 5.0, 0.5),
        tester.LimitLow('ACOK', 0.5),
        tester.LimitLow('PGOOD', 0.5),
        # Voltages
        tester.LimitPercent('5Vnl', 5.08, 1.0),
        tester.LimitPercent('12Vnl', 11.98, 1.3),
        tester.LimitPercent('24Vnl', 24.03, 1.4),
        # Load regulation (values in %)
        tester.LimitBetween('Reg12V', -0.05, 5.0),
        tester.LimitBetween('Reg24V', -0.05, 7.5),
        )
    # Initial Test limits
    limits_initial = _limits_common + (
        # Load regulation (values in %)
        tester.LimitLow('Reg5V', 3.0),
        tester.LimitDelta('8.5V Arduino', 8.5, 0.4),
        tester.LimitLow('FixtureLock', 200),
        tester.LimitBetween('Snubber', 1000, 3000), # Snubbing resistors
        tester.LimitRegExp('Reply', '^OK$'),
        tester.LimitInteger('Program', 0),
        tester.LimitDelta('3V3', 3.3, 0.1),
        tester.LimitDelta('ACin', 240, 10),
        tester.LimitLow('ARM-AcFreq', 999),
        tester.LimitLow('ARM-AcVolt', 999),
        tester.LimitLow('ARM-12V', 999),
        tester.LimitLow('ARM-24V', 999),
        tester.LimitDelta('5Vext', _5vsb_ext - 0.8, 1.0),
        tester.LimitDelta('5Vunsw', _5vsb_ext - 0.8 - 0.7, 1.0),
        tester.LimitHigh('12V_inOCP', 4.0),    # Detect OCP when TP405>4V
        tester.LimitHigh('24V_inOCP', 4.0),    # Detect OCP when TP404>4V
        tester.LimitBetween('12V_ocp', 4, 63), # Digital Pot setting
        tester.LimitBetween('24V_ocp', 4, 63), # Digital Pot setting
        tester.LimitBetween('PriCtl', 12.0, 14.5),
        tester.LimitDelta('PFCpre', pfc_target, 30),
        tester.LimitDelta('PFCpost', pfc_target, 2.0),
        tester.LimitDelta('12V_OCPchk', ratings.v12.ocp, 0.5),
        tester.LimitDelta('24V_OCPchk', ratings.v24.ocp, 2.05),
        )
    # Final Test limits
    limits_final = _limits_common + (
        tester.LimitLow('IECoff', 0.5),
        tester.LimitDelta('IEC', 240, 5),
        tester.LimitDelta('InRes', 70000, 10000),
        tester.LimitHigh('FanOff', 3.0),
        tester.LimitLow('FanOn', 2.0),
        tester.LimitLow('BracketDetect', 1.0),
        )
    # Software images
    _renesas_values = _Values(
        projectfile='r7fa2e1a7.jflash', sw_image='None')
    _rev_data = {
        None: _renesas_values,
        '5': _renesas_values,
        '4': _Values(
            projectfile='lpc1113.jflash',
            sw_image='sx600_1.3.19535.1537.bin'
            ),
        # Rev 1-3 were Engineering protoype builds
        }

    @classmethod
    def configure(cls, uut):
        """Adjust configuration based on UUT Lot Number.

        @param uut setec.UUT instance

        """
        try:
            rev = uut.lot.item.revision
        except AttributeError:
            rev = None
        logging.getLogger(__name__).debug('Revision detected as %s', rev)
        values = cls._rev_data[rev]
        cls.projectfile = values.projectfile
        cls.sw_image = values.sw_image
