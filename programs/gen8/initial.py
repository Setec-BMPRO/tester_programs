#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""GEN8 Initial Test Program."""

import os
import inspect
import time
import tester
import share
from share import teststep, SupportBase, AttributeDict
from . import console

BIN_VERSION = '1.4.645'     # Software binary version

# Reading to reading difference for PFC voltage stability
PFC_STABLE = 0.05
# Reading to reading difference for 12V voltage stability
V12_STABLE = 0.005
# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM6'}[os.name]
# Software image filename
ARM_BIN = 'gen8_{0}.bin'.format(BIN_VERSION)

LIMITS = tester.limitdict((
    tester.LimitLo('PartCheck', 100),   # uSwitches on C106, C107, D2
    tester.LimitHi('FanShort', 20),     # Short on fan connector
    tester.LimitLo('FixtureLock', 20),
    tester.LimitLo('5Voff', 0.5),
    tester.LimitHiLoPercent('5Vset', (5.10, 1.0)),
    tester.LimitHiLoPercent('5V', (5.10, 2.0)),
    tester.LimitLo('12Voff', 0.5),
    tester.LimitHiLoDelta('12Vpre', (12.1, 1.0)),
    tester.LimitHiLoDelta('12Vset', (12.18, 0.01)),
    tester.LimitHiLoPercent('12V', (12.18, 2.5)),
    tester.LimitLo('12V2off', 0.5),
    tester.LimitHiLoDelta('12V2pre', (12.0, 1.0)),
    tester.LimitHiLo('12V2', (11.8146, 12.4845)),   # 12.18 +2.5% -3.0%
    tester.LimitLo('24Voff', 0.5),
    tester.LimitHiLoDelta('24Vpre', (24.0, 2.0)),   # TestEng estimate
    tester.LimitHiLo('24V', (22.80, 25.68)),        # 24.0 +7% -5%
    tester.LimitLo('VdsQ103', 0.30),
    tester.LimitHiLoPercent('3V3', (3.30, 10.0)),   # TestEng estimate
    tester.LimitLo('PwrFail', 0.5),
    tester.LimitHiLoDelta('InputFuse', (240, 10)),
    tester.LimitHiLo('12Vpri', (11.4, 17.0)),
    tester.LimitHiLoDelta('PFCpre', (435, 15)),
    tester.LimitHiLoDelta('PFCpost1', (440.0, 0.8)),
    tester.LimitHiLoDelta('PFCpost2', (440.0, 0.8)),
    tester.LimitHiLoDelta('PFCpost3', (440.0, 0.8)),
    tester.LimitHiLoDelta('PFCpost4', (440.0, 0.8)),
    tester.LimitHiLoDelta('PFCpost', (440.0, 0.9)),
    tester.LimitHiLoDelta('ARM-AcFreq', (50, 10)),
    tester.LimitLo('ARM-AcVolt', 300),
    tester.LimitHiLoDelta('ARM-5V', (5.0, 1.0)),
    tester.LimitHiLoDelta('ARM-12V', (12.0, 1.0)),
    tester.LimitHiLoDelta('ARM-24V', (24.0, 2.0)),
    tester.LimitString(
        'SwVer', '^{0}$'.format(BIN_VERSION[:3].replace('.', r'\.'))),
    tester.LimitString(
        'SwBld', '^{0}$'.format(BIN_VERSION[4:])),
    ))

class Initial(tester.TestSequence):

    """GEN8 Initial Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence."""
        super().__init__(selection, None, fifo)
        self.devices = physical_devices
        self.support = None

    def open(self):
        """Prepare for testing."""
        self.support = Support(self.devices, self.fifo)
        # Define the (linear) Test Sequence
        sequence = (
            tester.TestStep('PartDetect', self._step_part_detect),
            tester.TestStep('Program', self._step_program, not self.fifo),
            tester.TestStep('Initialise', self._step_initialise_arm),
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('5V', self._step_reg_5v),
            tester.TestStep('12V', self._step_reg_12v),
            tester.TestStep('24V', self._step_reg_24v),
            )
        super().open(sequence)

    def close(self):
        """Finished testing."""
        self.support.close()
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self.support.reset()

    @teststep
    def _step_part_detect(self, sup, dev, mes):
        """Measure Part detection microswitches."""
        tester.MeasureGroup(
            (mes.dmm_lock, mes.dmm_part, mes.dmm_fanshort, ), timeout=2)

    @teststep
    def _step_program(self, sup, dev, mes):
        """Program the ARM device.

        5Vsb is injected to power the ARM for programming.
        Unit is left running the new code.

        """
        dev.dcs_5v.output(5.15, True)
        tester.MeasureGroup((mes.dmm_5v, mes.dmm_3v3, ), timeout=2)
        dev.programmer.program()
        # Reset micro, wait for ARM startup
        dev.rla_reset.pulse(0.1)
        time.sleep(1)

    @teststep
    def _step_initialise_arm(self, sup, dev, mes):
        """Initialise the ARM device.

        5V is already injected to power the ARM.
        The ARM is initialised via the serial port.

        Unit is left unpowered.

        """
        dev.arm.open()
        dev.arm['UNLOCK'] = True
        dev.arm['NVWRITE'] = True
        dev.dcs_5v.output(0.0, False)
        dev.loads(i5=0.1)
        time.sleep(0.5)
        dev.loads(i5=0)

    @teststep
    def _step_powerup(self, sup, dev, mes):
        """Power-Up the Unit.

        240Vac is applied.
        PFC voltage is calibrated.
        12V is calibrated.
        Unit is left running at 240Vac, no load.

        """
        dev.acsource.output(voltage=240.0, output=True)
        tester.MeasureGroup(
            (mes.dmm_acin, mes.dmm_5vset, mes.dmm_12vpri, mes.dmm_12voff,
             mes.dmm_12v2off, mes.dmm_24voff, mes.dmm_pwrfail, ), timeout=5)
        # Hold the 12V2 off
        dev.rla_12v2off.set_on()
        # A little load so 12V2 voltage falls when off
        dev.loads(i12=0.1)
        # Switch all outputs ON
        dev.rla_pson.set_on()
        tester.MeasureGroup(
            (mes.dmm_5vset, mes.dmm_12v2off, mes.dmm_24vpre, ), timeout=5)
        # Switch on the 12V2
        dev.rla_12v2off.set_off()
        mes.dmm_12v2.measure(timeout=5)
        # Unlock ARM
        dev.arm['UNLOCK'] = True
        # A little load so PFC voltage falls faster
        dev.loads(i12=1.0, i24=1.0)
        # Calibrate the PFC set voltage
        result, _, pfc = mes.dmm_pfcpre.stable(PFC_STABLE)
        dev.arm.calpfc(pfc)
        result, _, pfc = mes.dmm_pfcpost1.stable(PFC_STABLE)
        if not result:      # 1st retry
            dev.arm.calpfc(pfc)
            result, _, pfc = mes.dmm_pfcpost2.stable(PFC_STABLE)
        if not result:      # 2nd retry
            dev.arm.calpfc(pfc)
            result, _, pfc = mes.dmm_pfcpost3.stable(PFC_STABLE)
        if not result:      # 3rd retry
            dev.arm.calpfc(pfc)
            result, _, pfc = mes.dmm_pfcpost4.stable(PFC_STABLE)
        # A final PFC setup check
        mes.dmm_pfcpost.stable(PFC_STABLE)
        # no load for 12V calibration
        dev.loads(i12=0, i24=0)
        # Calibrate the 12V set voltage
        result, _, v12 = mes.dmm_12vpre.stable(V12_STABLE)
        dev.arm.cal12v(v12)
        # Prevent a limit fail from failing the unit
        mes.dmm_12vset.testlimit[0].position_fail = False
        result, _, v12 = mes.dmm_12vset.stable(V12_STABLE)
        # Allow a limit fail to fail the unit
        mes.dmm_12vset.testlimit[0].position_fail = True
        if not result:
            result, _, v12 = mes.dmm_12vpre.stable(V12_STABLE)
            dev.arm.cal12v(v12)
            mes.dmm_12vset.stable(V12_STABLE)
        tester.MeasureGroup(
            (mes.arm_acfreq, mes.arm_acvolt,
             mes.arm_5v, mes.arm_12v, mes.arm_24v, mes.arm_swver, mes.arm_swbld), )

    @teststep
    def _step_reg_5v(self, sup, dev, mes):
        """Check regulation of the 5V.

        Min = 0, Max = 2.0A, Peak = 2.5A
        Load = 3%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Unit is left running at no load.

        """
        dev.loads(i12=4.0, i24=0.1)
        self.reg_check(
            dmm_out=mes.dmm_5v, dcl_out=dev.dcl_5v, max_load=2.0, peak_load=2.5)
        dev.loads(i5=0, i12=0, i24=0)

    @teststep
    def _step_reg_12v(self, sup, dev, mes):
        """Check regulation and OCP of the 12V.

        Min = 4.0, Max = 22A, Peak = 24A
        Load = 5%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current
        (We use a parallel 12V / 12V2 load here)

        Unit is left running at no load.

        """
        dev.loads(i24=0.1)
        self.reg_check(
            dmm_out=mes.dmm_12v, dcl_out=dev.dcl_12v, max_load=22, peak_load=24)
        dev.loads(i12=0, i24=0)

    @teststep
    def _step_reg_24v(self, sup, dev, mes):
        """Check regulation and OCP of the 24V.

        Min = 0.1, Max = 5A, Peak = 6A
        Load = 7.5%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Unit is left running at no load.

        """
        dev.loads(i12=4.0)
        self.reg_check(
            dmm_out=mes.dmm_24v, dcl_out=dev.dcl_24v, max_load=5.0, peak_load=6.0,
            fet=True)
        dev.loads(i12=0, i24=0)

    def reg_check(self, dmm_out, dcl_out, max_load, peak_load, fet=False):
        """Check regulation of an output.

        dmm_out: Measurement instance for output voltage.
        dcl_out: DC Load instance.
        max_load: Maximum output load.
        peak_load: Peak output load.

        Unit is left running at peak load.

        """
        dmm_out.configure()
        dmm_out.opc()
        with tester.PathName('NoLoad'):
            dcl_out.output(0.0)
            dcl_out.opc()
            dmm_out.measure()
        with tester.PathName('MaxLoad'):
            dcl_out.binary(0.0, max_load, max(1.0, max_load / 16))
            dmm_out.measure()
            if fet:
                self.support.measurements['dmm_vdsfet'](timeout=5)
        with tester.PathName('PeakLoad'):
            dcl_out.output(peak_load)
            dcl_out.opc()
            dmm_out.measure()


class Support(SupportBase):

    """Supporting data."""

    def __init__(self, physical_devices, fifo):
        """Create all supporting classes."""
        super().__init__()
        self.devices = LogicalDevices(physical_devices, fifo)
        self.limits = LIMITS
        self.sensors = Sensors(self.devices)
        self.measurements = Measurements(self.sensors)


class LogicalDevices(AttributeDict):

    """Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        super().__init__()
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('discharge', tester.Discharge, 'DIS'),
                ('dcs_fixture', tester.DCSource, 'DCS1'),
                ('dcs_5v', tester.DCSource, 'DCS2'),
                ('dcl_24v', tester.DCLoad, 'DCL1'),
                ('dcl_5v', tester.DCLoad, 'DCL4'),
                ('rla_pson', tester.Relay, 'RLA1'),
                ('rla_12v2off', tester.Relay, 'RLA2'),
                ('rla_boot', tester.Relay, 'RLA3'),
                ('rla_reset', tester.Relay, 'RLA4'),
            ):
            self[name] = devtype(devices[phydevname])
        self['dcl_12v'] = tester.DCLoadParallel(
            ((tester.DCLoad(devices['DCL2']), 12),
             (tester.DCLoad(devices['DCL3']), 10)))
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self['programmer'] = share.ProgramARM(
            ARM_PORT, os.path.join(folder, ARM_BIN),
            boot_relay=self['rla_boot'], reset_relay=self['rla_reset'])
        # Serial connection to the ARM console
        self['arm_ser'] = tester.SimSerial(
            simulation=fifo, baudrate=57600, timeout=2.0)
        # Set port separately - don't open until after programming
        self['arm_ser'].port = ARM_PORT
        self['arm'] = console.Console(self['arm_ser'], verbose=False)
        # Switch on fixture power
        self['dcs_fixture'].output(10.0, output=True)

    def reset(self):
        """Reset instruments."""
        self['arm'].close()
        # Switch off AC Source and discharge the unit
        self['acsource'].output(voltage=0.0, output=False)
        self.loads(i5=1.0, i12=5.0, i24=5.0)
        time.sleep(0.5)
        self['discharge'].pulse()
        self.loads(i5=0, i12=0, i24=0, output=False)
        self['dcs_5v'].output(0.0, False)
        for rla in ('rla_12v2off', 'rla_pson', 'rla_reset', 'rla_boot'):
            self[rla].set_off()

    def close(self):
        """Switch on fixture power."""
        self['dcs_fixture'].output(0.0, output=False)

    def loads(self, i5=None, i12=None, i24=None, output=True):
        """Set output loads.

        @param i5 5V load current
        @param i12 12V load current
        @param i24 24V load current
        @param output True to enable the load

        """
        if i5 is not None:
            self['dcl_5v'].output(i5, output)
        if i12 is not None:
            self['dcl_12v'].output(i12, output)
        if i24 is not None:
            self['dcl_24v'].output(i24, output)


class Sensors(AttributeDict):

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used

        """
        super().__init__()
        dmm = logical_devices['dmm']
        sensor = tester.sensor
        self['o5v'] = sensor.Vdc(dmm, high=7, low=4, rng=10, res=0.001)
        self['o12v'] = sensor.Vdc(dmm, high=9, low=4, rng=100, res=0.001)
        self['o12v2'] = sensor.Vdc(dmm, high=8, low=4, rng=100, res=0.001)
        self['o24v'] = sensor.Vdc(dmm, high=6, low=4, rng=100, res=0.001)
        self['pwrfail'] = sensor.Vdc(dmm, high=5, low=4, rng=100, res=0.01)
        self['o3v3'] = sensor.Vdc(dmm, high=11, low=4, rng=10, res=0.001)
        self['o12vpri'] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.01)
        self['pfc'] = sensor.Vdc(dmm, high=3, low=3, rng=1000, res=0.001)
        self['acin'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self['gpo'] = sensor.Vac(dmm, high=2, low=2, rng=1000, res=0.01)
        self['lock'] = sensor.Res(dmm, high=12, low=6, rng=10000, res=1)
        self['part'] = sensor.Res(dmm, high=10, low=5, rng=1000, res=0.01)
        self['fanshort'] = sensor.Res(dmm, high=13, low=7, rng=1000, res=0.1)
        self['vdsfet'] = sensor.Vdc(dmm, high=14, low=8, rng=100, res=0.001)
        arm = logical_devices['arm']
        for name, cmdkey in (
                ('arm_acfreq', 'AcFreq'),
                ('arm_acvolt', 'AcVolt'),
                ('arm_5v', '5V'),
                ('arm_12v', '12V'),
                ('arm_24v', '24V'),
            ):
            self[name] = console.Sensor(arm, cmdkey)
        for name, cmdkey in (
                ('arm_swver', 'SwVer'),
                ('arm_swbld', 'SwBld'),
            ):
            self[name] = console.Sensor(
                arm, cmdkey, rdgtype=sensor.ReadingString)


class Measurements(AttributeDict):

    """Measurements."""

    def __init__(self, sense):
        """Create all Measurement instances.

           @param sense Sensors used

        """
        super().__init__()
        for measurement_name, limit_name, sensor_name in (
                ('dmm_lock', 'FixtureLock', 'lock'),
                ('dmm_part', 'PartCheck', 'part'),
                ('dmm_fanshort', 'FanShort', 'fanshort'),
                ('dmm_acin', 'InputFuse', 'acin'),
                ('dmm_12vpri', '12Vpri', 'o12vpri'),
                ('dmm_5vset', '5Vset', 'o5v'),
                ('dmm_5v', '5V', 'o5v'),
                ('dmm_12voff', '12Voff', 'o12v'),
                ('dmm_12vpre', '12Vpre', 'o12v'),
                ('dmm_12vset', '12Vset', 'o12v'),
                ('dmm_12v', '12V', 'o12v'),
                ('dmm_12v2off', '12V2off', 'o12v2'),
                ('dmm_12v2pre', '12V2pre', 'o12v2'),
                ('dmm_12v2', '12V2', 'o12v2'),
                ('dmm_24voff', '24Voff', 'o24v'),
                ('dmm_24vpre', '24Vpre', 'o24v'),
                ('dmm_24v', '24V', 'o24v'),
                ('dmm_vdsfet', 'VdsQ103', 'vdsfet'),
                ('dmm_3v3', '3V3', 'o3v3'),
                ('dmm_pfcpre', 'PFCpre', 'pfc'),
                ('dmm_pfcpost1', 'PFCpost1', 'pfc'),
                ('dmm_pfcpost2', 'PFCpost2', 'pfc'),
                ('dmm_pfcpost3', 'PFCpost3', 'pfc'),
                ('dmm_pfcpost4', 'PFCpost4', 'pfc'),
                ('dmm_pfcpost', 'PFCpost', 'pfc'),
                ('dmm_pwrfail', 'PwrFail', 'pwrfail'),
                ('arm_acfreq', 'ARM-AcFreq', 'arm_acfreq'),
                ('arm_acvolt', 'ARM-AcVolt', 'arm_acvolt'),
                ('arm_5v', 'ARM-5V', 'arm_5v'),
                ('arm_12v', 'ARM-12V', 'arm_12v'),
                ('arm_24v', 'ARM-24V', 'arm_24v'),
                ('arm_swver', 'SwVer', 'arm_swver'),
                ('arm_swbld', 'SwBld', 'arm_swbld'),
            ):
            self[measurement_name] = tester.Measurement(
                LIMITS[limit_name], sense[sensor_name])
        # Prevent test failures on these limits.
        for limitname in ('PFCpost1', 'PFCpost2', 'PFCpost3', 'PFCpost4'):
            LIMITS[limitname].position_fail = False
