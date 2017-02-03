#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2016 SETEC Pty Ltd
"""SX-750 Initial Test Program."""

import os
import inspect
import time
import tester
from tester.testlimit import (
    lim_hilo_delta, lim_hilo_percent, lim_hilo, lim_hilo_int,
    lim_lo, lim_hi, lim_string
    )
import share
from share import oldteststep
from . import arduino
from . import console

BIN_VERSION = '3.1.2118'        # Software versions
PIC_HEX1 = 'sx750_pic5Vsb_1.hex'
PIC_HEX2 = 'sx750_picPwrSw_2.hex'

# Serial port for the ARM. Used by programmer and ARM comms module.
ARM_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM7'}[os.name]
# Serial port for the Arduino.
ARDUINO_PORT = {'posix': '/dev/ttyACM0', 'nt': 'COM5'}[os.name]
# Software image filenames
ARM_BIN = 'sx750_arm_{}.bin'.format(BIN_VERSION)

# Reading to reading difference for PFC voltage stability
PFC_STABLE = 0.05

LIMITS = tester.testlimit.limitset((
    lim_hilo('8.5V Arduino', 8.1, 8.9),
    lim_lo('5Voff', 0.5),
    lim_hilo('5Vext', 5.5, 5.9),
    lim_hilo_percent('5Vsb_set', 5.10, 1.5),
    lim_hilo_percent('5Vsb', 5.10, 5.5),
    lim_lo('5Vsb_reg', 3.0),        # Load Reg < 3.0%
    lim_lo('12Voff', 0.5),
    lim_hilo_percent('12V_set', 12.25, 2.0),
    lim_hilo_percent('12V', 12.25, 8.0),
    lim_lo('12V_reg', 3.0),         # Load Reg < 3.0%
    lim_hilo('12V_ocp', 4, 63),     # Digital Pot setting - counts up from MIN
    lim_hi('12V_inOCP', 4.0),       # Detect OCP when TP405 > 4V
    lim_hilo('12V_OCPchk', 36.2, 37.0),
    lim_lo('24Voff', 0.5),
    lim_hilo_percent('24V_set', 24.13, 2.0),
    lim_hilo_percent('24V', 24.13, 10.5),
    lim_lo('24V_reg', 7.5),         # Load Reg < 7.5%
    lim_hilo('24V_ocp', 4, 63),     # Digital Pot setting - counts up from MIN
    lim_hi('24V_inOCP', 4.0),       # Detect OCP when TP404 > 4V
    lim_hilo('24V_OCPchk', 18.1, 18.5),
    lim_hilo('PriCtl', 11.40, 17.0),
    lim_lo('PGOOD', 0.5),
    lim_hilo_delta('ACFAIL', 5.0, 0.5),
    lim_lo('ACOK', 0.5),
    lim_hilo_delta('3V3', 3.3, 0.1),
    lim_hilo_delta('ACin', 240, 10),
    lim_hilo_delta('PFCpre', 420, 20),
    lim_hilo_delta('PFCpost', 435, 1.0),
    lim_hilo_delta('OCP12pre', 36, 2),
    lim_hilo('OCP12post', 35.7, 36.5),
    lim_lo('OCP12step', 0.116),
    lim_hilo_delta('OCP24pre', 18, 1),
    lim_hilo_delta('OCP24post', 18.2, 0.1),
    lim_lo('OCP24step', 0.058),
    # Data reported by the ARM
    lim_lo('ARM-AcFreq', 999),
    lim_lo('ARM-AcVolt', 999),
    lim_lo('ARM-12V', 999),
    lim_lo('ARM-24V', 999),
    lim_string(
        'ARM-SwVer', '^{}$'.format(BIN_VERSION[:3].replace('.', r'\.'))),
    lim_string('ARM-SwBld', '^{}$'.format(BIN_VERSION[4:])),
    #
    lim_lo('FixtureLock', 20),
    lim_lo('PartCheck', 20),            # Microswitches on C612, C613, D404
    lim_hilo('Snubber', 1000, 3000),    # Snubbing resistors
    lim_string('Reply', '^OK$'),
    lim_hilo_int('Program', 0)
    ))


class Initial(tester.TestSequence):

    """SX-750 Initial Test Program."""

    def __init__(self, physical_devices):
        """Create the test program as a linear sequence."""
        super().__init__()
        self.devices = physical_devices
        self.limits = LIMITS
        self.logdev = None
        self.sensor = None
        self.meas = None
        self.subt = None

    def open(self, sequence=None):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('FixtureLock', self._step_fixture_lock),
            tester.TestStep('Program', self._step_program_micros),
            tester.TestStep('Initialise', self._step_initialise_arm),
            tester.TestStep('PowerUp', self._step_powerup),
            tester.TestStep('5Vsb', self._step_reg_5v),
            tester.TestStep('12V', self._step_reg_12v),
            tester.TestStep('24V', self._step_reg_24v),
            tester.TestStep('PeakPower', self._step_peak_power),
            )
        self.logdev = LogicalDevices(self.devices, self.fifo)
        self.sensor = Sensors(self.logdev, self.limits)
        self.meas = Measurements(self.sensor, self.limits)
        self.subt = SubTests(self.logdev, self.meas)
        self.logdev.dcs_Vcom.output(9.0, output=True)
        self.logdev.dcs_Arduino.output(12.0, output=True)
        time.sleep(2)   # Allow OS to detect the new ports

    def close(self):
        """Finished testing."""
        self.logdev.dcs_Arduino.output(0.0, output=False)
        self.logdev.dcs_Vcom.output(0.0, output=False)
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        self.logdev.reset()

    @oldteststep
    def _step_fixture_lock(self, dev, mes):
        """Check that Fixture Lock is closed.

        Measure Part detection microswitches.
        Check for presence of Snubber resistors.

        """
        tester.MeasureGroup(
            (mes.dmm_Lock, mes.dmm_Part, mes.dmm_R601, mes.dmm_R602,
             mes.dmm_R609, mes.dmm_R608),
            timeout=2)

    @oldteststep
    def _step_program_micros(self, dev, mes):
        """Program the ARM and PIC devices.

        5Vsb is injected to power the ARM and 5Vsb PIC. PriCtl is injected
        to power the PwrSw PIC and digital pots.
        The ARM is programmed.
        The PIC's are programmed and the digital pots are set for maximum OCP.
        Unit is left unpowered.

        """
        # Set BOOT active before power-on so the ARM boot-loader runs
        dev.rla_boot.set_on()
        # Apply and check injected rails
        self.subt.ext_pwron.run()
        if self.fifo:
            self._logger.info(
                '**** Programming skipped due to active FIFOs ****')
        else:
            dev.programmer.program()  # Program the ARM device
        dev.ard.open()
        time.sleep(2)        # Wait for Arduino to start
        dev.rla_pic1.set_on()
        dev.rla_pic1.opc()
        mes.dmm_5Vunsw.measure(timeout=2)
        mes.pgm_5vsb.measure()
        dev.rla_pic1.set_off()
        dev.rla_pic2.set_on()
        dev.rla_pic2.opc()
        mes.pgm_pwrsw.measure()
        dev.rla_pic2.set_off()
        mes.ocp_max.measure()
        # Switch off rails and discharge the 5Vsb to stop the ARM
        self.subt.ext_pwroff.run()

    @oldteststep
    def _step_initialise_arm(self, dev, mes):
        """Initialise the ARM device.

        5Vsb is injected to power the ARM.
        The ARM is initialised via the serial port.
        Unit is left unpowered.

        """
        dev.arm.open()
        dev.dcs_5Vsb.output(9.0, True)
        tester.MeasureGroup((mes.dmm_5Vext, mes.dmm_5Vunsw), 2)
        time.sleep(1)           # ARM startup delay
        dev.arm['UNLOCK'] = True
        dev.arm['NVWRITE'] = True
        # Switch everything off
        dev.dcs_5Vsb.output(0, False)
        dev.dcl_5Vsb.output(0.1)
        time.sleep(0.5)
        dev.dcl_5Vsb.output(0)

    @oldteststep
    def _step_powerup(self, dev, mes):
        """Power-Up the Unit.

        240Vac is applied.
        ARM data readings are logged.
        PFC voltage is calibrated.
        Unit is left running at 240Vac, no load.

        """
        dev.acsource.output(voltage=240.0, output=True)
        # A little load so PFC voltage falls faster
        dev.dcl_12V.output(1.0)
        dev.dcl_24V.output(1.0)
        tester.MeasureGroup(
            (mes.dmm_ACin, mes.dmm_PriCtl, mes.dmm_5Vsb_set, mes.dmm_12Voff,
             mes.dmm_24Voff, mes.dmm_ACFAIL), 2)
        # Switch all outputs ON
        dev.rla_pson.set_on()
        tester.MeasureGroup(
            (mes.dmm_12V_set, mes.dmm_24V_set, mes.dmm_PGOOD), 2)
        # ARM data readings
        dev.arm['UNLOCK'] = True
        tester.MeasureGroup(
            (mes.arm_AcFreq, mes.arm_AcVolt, mes.arm_12V, mes.arm_24V,
             mes.arm_SwVer, mes.arm_SwBld), )
        # Calibrate the PFC set voltage
        self._logger.info('Start PFC calibration')
        result, _, pfc = mes.dmm_PFCpre.stable(PFC_STABLE)
        dev.arm.calpfc(pfc)
        # Prevent a limit fail from failing the unit
        mes.dmm_PFCpost.testlimit[0].position_fail = False
        result, _, pfc = mes.dmm_PFCpost.stable(PFC_STABLE)
        # Allow a limit fail to fail the unit
        mes.dmm_PFCpost.testlimit[0].position_fail = True
        if not result:
            self._logger.info('Retry PFC calibration')
            result, _, pfc = mes.dmm_PFCpre.stable(PFC_STABLE)
            dev.arm.calpfc(pfc)
            mes.dmm_PFCpost.stable(PFC_STABLE)
        # Leave the loads at zero
        dev.dcl_12V.output(0)
        dev.dcl_24V.output(0)

    @oldteststep
    def _step_reg_5v(self, dev, mes):
        """Check regulation of the 5Vsb.

        Min = 0, Max = 2.0A, Peak = 2.5A
        Load = 3%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current
        Unit is left running at no load.

        """
        self.reg_check(
            dmm_out=mes.dmm_5Vsb, dcl_out=dev.dcl_5Vsb,
            reg_limit=self.limits['5Vsb_reg'], max_load=2.0, peak_load=2.5)
        dev.dcl_5Vsb.output(0)

    @oldteststep
    def _step_reg_12v(self, dev, mes):
        """Check regulation and OCP of the 12V.

        Min = 0, Max = 32A, Peak = 36A
        Load = 5%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Pre Adjustment Range    34.0 - 38.0A
        Post adjustment range   36.2 - 36.6A
        Adjustment resolution   116mA/step
        Unit is left running at no load.

        """
        self.reg_check(
            dmm_out=mes.dmm_12V, dcl_out=dev.dcl_12V,
            reg_limit=self.limits['12V_reg'], max_load=32.0, peak_load=36.0)
        self.ocp_set(
            target=36.6, load=dev.dcl_12V,
            dmm=mes.dmm_12V, detect=mes.dmm_12V_inOCP,
            enable=mes.ocp12_unlock, olimit=self.limits['12V_ocp'])
        with tester.PathName('OCPcheck'):
            dev.dcl_12V.binary(0.0, 36.6 * 0.9, 2.0)
            mes.rampOcp12V.measure()
            dev.dcl_12V.output(1.0)
            dev.dcl_12V.output(0.0)

    @oldteststep
    def _step_reg_24v(self, dev, mes):
        """Check regulation and OCP of the 24V.

        Min = 0, Max = 15A, Peak = 18A
        Load = 7.5%, Line = 0.5%, Temp = 1.0%
        Load regulation measured from 0A to 95% of rated current

        Pre Adjustment Range    17.0 - 19.0A
        Post adjustment range   18.1 - 18.3A
        Adjustment resolution   58mA/step
        Unit is left running at no load.

        """
        self.reg_check(
            dmm_out=mes.dmm_24V, dcl_out=dev.dcl_24V,
            reg_limit=self.limits['24V_reg'], max_load=15.0, peak_load=18.0)
        self.ocp_set(
            target=18.3, load=dev.dcl_24V,
            dmm=mes.dmm_24V, detect=mes.dmm_24V_inOCP,
            enable=mes.ocp24_unlock, olimit=self.limits['24V_ocp'])
        with tester.PathName('OCPcheck'):
            dev.dcl_24V.binary(0.0, 18.3 * 0.9, 2.0)
            mes.rampOcp24V.measure()
            dev.dcl_24V.output(1.0)
            dev.dcl_24V.output(0.0)

    @oldteststep
    def _step_peak_power(self, dev, mes):
        """Check operation at Peak load.

        5Vsb @ 2.5A, 12V @ 36.0A, 24V @ 18.0A
        Unit is left running at no load.

        """
        dev.dcl_5Vsb.binary(start=0.0, end=2.5, step=1.0)
        dev.dcl_12V.binary(start=0.0, end=36.0, step=2.0)
        dev.dcl_24V.binary(start=0.0, end=18.0, step=2.0)
        tester.MeasureGroup(
            (mes.dmm_5Vsb, mes.dmm_12V, mes.dmm_24V, mes.dmm_PGOOD), 2)
        dev.dcl_24V.output(0)
        dev.dcl_12V.output(0)
        dev.dcl_5Vsb.output(0)

    def ocp_set(self, target, load, dmm, detect, enable, olimit):
        """Set OCP of an output.

        target: Target setpoint in Amp.
        load: Load instrument.
        dmm: Measurement of output voltage.
        detect: Measurement of 'In OCP'.
        enable: Measurement to call to enable digital pot.
        olimit: Limit to check OCP pot setting.

        OCP has been set to maximum in the programming step.
        Apply the desired load current, then lower the OCP setting until
        OCP triggers. The unit is left running at no load.

        """
        with tester.PathName('OCPset'):
            load.output(target)
            dmm.measure()
            detect.configure()
            detect.opc()
            enable.measure()
            setting = 0
            for setting in range(63, 0, -1):
                self.meas.ocp_step_dn.measure()
                if detect.measure().result:
                    break
            self.meas.ocp_lock.measure()
            load.output(0.0)
            olimit.check(setting, 1)

    @staticmethod
    def reg_check(dmm_out, dcl_out, reg_limit, max_load, peak_load):
        """Check regulation of an output.

        dmm_out: Measurement instance for output voltage.
        dcl_out: DC Load instance.
        reg_limit: TestLimit for Load Regulation.
        max_load: Maximum output load.
        peak_load: Peak output load.
        Unit is left running at peak load.

        """
        dmm_out.configure()
        dmm_out.opc()
        with tester.PathName('NoLoad'):
            dcl_out.output(0.0)
            dcl_out.opc()
            volt00 = dmm_out.measure().reading1
        with tester.PathName('MaxLoad'):
            dcl_out.binary(0.0, max_load, max(1.0, max_load / 16))
            dmm_out.measure()
        with tester.PathName('LoadReg'):
            dcl_out.output(peak_load * 0.95)
            dcl_out.opc()
            volt = dmm_out.measure().reading1
            load_reg = 100.0 * (volt00 - volt) / volt00
            reg_limit.check(load_reg, 1)
        with tester.PathName('PeakLoad'):
            dcl_out.output(peak_load)
            dcl_out.opc()
            dmm_out.measure()


class LogicalDevices():

    """SX-750 Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments."""
        self._fifo = fifo
        self.acsource = tester.ACSource(devices['ACS'])
        self.dmm = tester.DMM(devices['DMM'])
        self.discharge = tester.Discharge(devices['DIS'])
        self.dcs_PriCtl = tester.DCSource(devices['DCS1'])
        self.dcs_Arduino = tester.DCSource(devices['DCS2'])
        self.dcs_5Vsb = tester.DCSource(devices['DCS3'])
        self.dcs_Vcom = tester.DCSource(devices['DCS4'])
        self.dcl_5Vsb = tester.DCLoad(devices['DCL2'])
        self.dcl_12V = tester.DCLoad(devices['DCL1'])
        self.dcl_24V = tester.DCLoad(devices['DCL3'])
        self.rla_pic1 = tester.Relay(devices['RLA1'])
        self.rla_pic2 = tester.Relay(devices['RLA2'])
        self.rla_pson = tester.Relay(devices['RLA3'])
        self.rla_boot = tester.Relay(devices['RLA4'])
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        file = os.path.join(folder, ARM_BIN)
        self.programmer = share.ProgramARM(
            ARM_PORT, file, boot_relay=self.rla_boot)
        # Serial connection to the ARM console
        self.arm_ser = tester.SimSerial(
            simulation=fifo, baudrate=57600, timeout=2.0)
        # Set port separately, as we don't want it opened yet
        self.arm_ser.port = ARM_PORT
        self.arm = console.Console(self.arm_ser, verbose=False)
        # Serial connection to the Arduino console
        self.ard_ser = tester.SimSerial(
            simulation=fifo, baudrate=115200, timeout=2.0)
        # Set port separately, as we don't want it opened yet
        self.ard_ser.port = ARDUINO_PORT
        self.ard = arduino.Arduino(self.ard_ser, verbose=False)

    def reset(self):
        """Reset instruments."""
        self.arm.close()
        self.ard.close()
        self.acsource.output(voltage=0.0, output=False)
        self.dcl_5Vsb.output(1.0)
        self.dcl_12V.output(5.0)
        self.dcl_24V.output(5.0)
        time.sleep(1)
        self.discharge.pulse()
        for ld in (self.dcl_5Vsb, self.dcl_12V, self.dcl_24V):
            ld.output(0.0)
        for dcs in (self.dcs_PriCtl, self.dcs_5Vsb):
            dcs.output(0.0, False)
        for rla in (
                self.rla_pic1, self.rla_pic2, self.rla_boot, self.rla_pson):
            rla.set_off()


class Sensors():

    """SX-750 Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        d = logical_devices
        dmm = d.dmm
        sensor = tester.sensor
        self.o5Vsb = sensor.Vdc(dmm, high=5, low=3, rng=10, res=0.001)
        self.o5Vsbunsw = sensor.Vdc(dmm, high=18, low=3, rng=10, res=0.001)
        self.o8V5Ard = sensor.Vdc(dmm, high=19, low=3, rng=100, res=0.001)
        self.o12V = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.o12VinOCP = sensor.Vdc(dmm, high=10, low=2, rng=100, res=0.01)
        self.o24V = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.o24VinOCP = sensor.Vdc(dmm, high=11, low=2, rng=100, res=0.01)
        self.PriCtl = sensor.Vdc(dmm, high=8, low=2, rng=100, res=0.01)
        self.PFC = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self.PGOOD = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.01)
        self.ACFAIL = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.01)
        self.o3V3 = sensor.Vdc(dmm, high=9, low=3, rng=10, res=0.001)
        self.ACin = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.Lock = sensor.Res(dmm, high=12, low=4, rng=1000, res=1)
        self.Part = sensor.Res(dmm, high=13, low=4, rng=1000, res=1)
        self.R601 = sensor.Res(dmm, high=14, low=5, rng=10000, res=1)
        self.R602 = sensor.Res(dmm, high=15, low=5, rng=10000, res=1)
        self.R609 = sensor.Res(dmm, high=16, low=6, rng=10000, res=1)
        self.R608 = sensor.Res(dmm, high=17, low=6, rng=10000, res=1)
        self.OCP12V = sensor.Ramp(
            stimulus=d.dcl_12V, sensor=self.o12VinOCP,
            detect_limit=(limits['12V_inOCP'], ),
            start=36.6 * 0.9, stop=36.6 * 1.1, step=0.1, delay=0,
            reset=True, use_opc=True)
        self.OCP24V = sensor.Ramp(
            stimulus=d.dcl_24V, sensor=self.o24VinOCP,
            detect_limit=(limits['24V_inOCP'], ),
            start=18.3 * 0.9, stop=18.3 * 1.1, step=0.1, delay=0,
            reset=True, use_opc=True)
        self.pgm5Vsb = console.Sensor(
            d.ard, 'PGM_5VSB', rdgtype=sensor.ReadingString)
        self.pgmPwrSw = console.Sensor(
            d.ard, 'PGM_PWRSW', rdgtype=sensor.ReadingString)
        self.ocpMax = console.Sensor(
            d.ard, 'OCP_MAX', rdgtype=sensor.ReadingString)
        self.ocp12Unlock = console.Sensor(
            d.ard, '12_OCP_UNLOCK', rdgtype=sensor.ReadingString)
        self.ocp24Unlock = console.Sensor(
            d.ard, '24_OCP_UNLOCK', rdgtype=sensor.ReadingString)
        self.ocpStepDn = console.Sensor(
            d.ard, 'OCP_STEP_DN', rdgtype=sensor.ReadingString)
        self.ocpLock = console.Sensor(
            d.ard, 'OCP_LOCK', rdgtype=sensor.ReadingString)
        self.ARM_AcFreq = console.Sensor(d.arm, 'ARM-AcFreq')
        self.ARM_AcVolt = console.Sensor(d.arm, 'ARM-AcVolt')
        self.ARM_12V = console.Sensor(d.arm, 'ARM-12V')
        self.ARM_24V = console.Sensor(d.arm, 'ARM-24V')
        self.ARM_SwVer = console.Sensor(
            d.arm, 'ARM_SwVer', rdgtype=sensor.ReadingString)
        self.ARM_SwBld = console.Sensor(
            d.arm, 'ARM_SwBld', rdgtype=sensor.ReadingString)


class Measurements():

    """SX-750 Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self._limits = limits
        self.dmm_5Voff = self._maker('5Voff', sense.o5Vsb)
        self.dmm_5Vext = self._maker('5Vext', sense.o5Vsb)
        self.dmm_5Vunsw = self._maker('5Vsb', sense.o5Vsbunsw)
        self.dmm_5Vsb_set = self._maker('5Vsb_set', sense.o5Vsb)
        self.dmm_5Vsb = self._maker('5Vsb', sense.o5Vsb)
        self.dmm_12V_set = self._maker('12V_set', sense.o12V)
        self.dmm_12V = self._maker('12V', sense.o12V)
        self.dmm_12Voff = self._maker('12Voff', sense.o12V)
        self.dmm_12V_inOCP = self._maker(
            '12V_inOCP', sense.o12VinOCP, silent=True)
        self.dmm_24V = self._maker('24V', sense.o24V)
        self.dmm_24V_set = self._maker('24V_set', sense.o24V)
        self.dmm_24Voff = self._maker('24Voff', sense.o24V)
        self.dmm_24V_inOCP = self._maker(
            '24V_inOCP', sense.o24VinOCP, silent=True)
        self.dmm_PriCtl = self._maker('PriCtl', sense.PriCtl)
        self.dmm_PFCpre = self._maker('PFCpre', sense.PFC)
        self.dmm_PFCpost = self._maker('PFCpost', sense.PFC)
        self.dmm_ACin = self._maker('ACin', sense.ACin)
        self.dmm_PGOOD = self._maker('PGOOD', sense.PGOOD)
        self.dmm_ACFAIL = self._maker('ACFAIL', sense.ACFAIL)
        self.dmm_ACOK = self._maker('ACOK', sense.ACFAIL)
        self.dmm_3V3 = self._maker('3V3', sense.o3V3)
        self.dmm_Lock = self._maker('FixtureLock', sense.Lock)
        self.dmm_Part = self._maker('PartCheck', sense.Part)
        self.dmm_R601 = self._maker('Snubber', sense.R601)
        self.dmm_R602 = self._maker('Snubber', sense.R602)
        self.dmm_R609 = self._maker('Snubber', sense.R609)
        self.dmm_R608 = self._maker('Snubber', sense.R608)
        self.rampOcp12V = self._maker('12V_OCPchk', sense.OCP12V)
        self.rampOcp24V = self._maker('24V_OCPchk', sense.OCP24V)
        self.dmm_8V5Ard = self._maker('8.5V Arduino', sense.o8V5Ard)
        self.pgm_5vsb = self._maker('Reply', sense.pgm5Vsb)
        self.pgm_pwrsw = self._maker('Reply', sense.pgmPwrSw)
        self.ocp_max = self._maker('Reply', sense.ocpMax)
        self.ocp12_unlock = self._maker('Reply', sense.ocp12Unlock)
        self.ocp24_unlock = self._maker('Reply', sense.ocp24Unlock)
        self.ocp_step_dn = self._maker('Reply', sense.ocpStepDn, silent=True)
        self.ocp_lock = self._maker('Reply', sense.ocpLock)
        self.arm_AcFreq = self._maker('ARM-AcFreq', sense.ARM_AcFreq)
        self.arm_AcVolt = self._maker('ARM-AcVolt', sense.ARM_AcVolt)
        self.arm_12V = self._maker('ARM-12V', sense.ARM_12V)
        self.arm_24V = self._maker('ARM-24V', sense.ARM_24V)
        self.arm_SwVer = self._maker('ARM-SwVer', sense.ARM_SwVer)
        self.arm_SwBld = self._maker('ARM-SwBld', sense.ARM_SwBld)

    def _maker(self, limitname, sensor, silent=False):
        """Helper to create a Measurement.

        @param limitname Test Limit name
        @param sensor Sensor to use
        @param silent True to suppress position_fail & send_signal
        @return tester.Measurement instance

        """
        lim = self._limits[limitname]
        if silent:
            lim.position_fail = False
            lim.send_signal = False
        return tester.Measurement(lim, sensor)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param logical_devices Logical instruments used
           @param measurements Measurements used

        """
        d = logical_devices
        m = measurements
        # ExtPowerOn: Apply and check injected rails.
        self.ext_pwron = tester.SubStep((
            tester.DcSubStep(
                setting=((d.dcs_5Vsb, 9.0), (d.dcs_PriCtl, 12.0), ),
                output=True),
            tester.MeasureSubStep(
                (m.dmm_5Vext, m.dmm_5Vunsw, m.dmm_3V3, m.dmm_PriCtl,
                 m.dmm_8V5Ard,), timeout=5),
        ))

        # ExtPowerOff: # Switch off rails, discharge the 5Vsb to stop the ARM.
        self.ext_pwroff = tester.SubStep((
            tester.DcSubStep(
                setting=((d.dcs_5Vsb, 0.0), (d.dcs_PriCtl, 0.0), ),
                output=False),
            tester.LoadSubStep(((d.dcl_5Vsb, 0.1), ), output=True, delay=0.5),
            # This will also enable all loads on an ATE3/4 tester.
            tester.LoadSubStep(
                ((d.dcl_5Vsb, 0.0), (d.dcl_12V, 0.0), (d.dcl_24V, 0.0), ),
                output=True),
        ))
