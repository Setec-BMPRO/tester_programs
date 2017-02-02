#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Initial Test Program."""

import os
import inspect
import time
import share
import tester
from . import limit
from . import arduino
from .. import console


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
        file = os.path.join(folder, limit.ARM_BIN)
        self.programmer = share.ProgramARM(
            limit.ARM_PORT, file, boot_relay=self.rla_boot)
        # Serial connection to the ARM console
        self.arm_ser = tester.SimSerial(
            simulation=fifo, baudrate=57600, timeout=2.0)
        # Set port separately, as we don't want it opened yet
        self.arm_ser.port = limit.ARM_PORT
        self.arm = console.Console(self.arm_ser, verbose=False)
        # Auto add prompt to puts strings
        self.arm.puts_prompt = '\r> '
        # Serial connection to the Arduino console
        self.ard_ser = tester.SimSerial(
            simulation=fifo, baudrate=115200, timeout=2.0)
        # Set port separately, as we don't want it opened yet
        self.ard_ser.port = limit.ARDUINO_PORT
        self.ard = arduino.Arduino(self.ard_ser, verbose=True)
        # Auto add prompt to puts strings
        self.ard.puts_prompt = '\r> '

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
