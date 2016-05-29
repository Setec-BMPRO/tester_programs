#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX-750 Initial Test Program."""

import os
import inspect
import time
from pydispatch import dispatcher

import share
import sensor
import tester
from . import limit
from . import arduino
from . import digpot
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
        self.dcl_5Vsb = tester.DCLoad(devices['DCL2'])
        self.dcl_12V = tester.DCLoad(devices['DCL1'])
        self.dcl_24V = tester.DCLoad(devices['DCL5'])
        self.rla_pic2 = tester.Relay(devices['RLA1'])
        self.rla_pic1 = tester.Relay(devices['RLA7'])
        self.rla_boot = tester.Relay(devices['RLA2'])
        self.rla_pson = tester.Relay(devices['RLA3'])
        self.rla_pot_ud = tester.Relay(devices['RLA6'])
        self.rla_pot_12 = tester.Relay(devices['RLA5'])
        self.rla_pot_24 = tester.Relay(devices['RLA4'])
        self.ocp_pot = digpot.OCPAdjust(
            self.rla_pot_ud, self.rla_pot_12, self.rla_pot_24)
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        file = os.path.join(folder, limit.ARM_BIN)
        self.programmer = share.ProgramARM(limit.ARM_PORT, file)
        # Serial connection to the ARM console
        arm_ser = share.SimSerial(
            simulation=fifo, baudrate=57600, timeout=2.0)
        # Set port separately, as we don't want it opened yet
        arm_ser.port = limit.ARM_PORT
        self.arm = console.Console(arm_ser, verbose=False)
        # Serial connection to the Arduino console
        ard_ser = share.SimSerial(
            simulation=fifo, baudrate=115200, timeout=2.0)
        # Set port separately, as we don't want it opened yet
        ard_ser.port = limit.ARDUINO_PORT
        self.ard = arduino.Arduino(ard_ser, verbose=False)

    def arm_puts(self,
                 string_data, preflush=0, postflush=0, priority=False,
                 addprompt=True):
        """Push string data into the buffer, if FIFOs are enabled."""
        if self._fifo:
            if addprompt:
                string_data = string_data + '\r> '
            self.arm.puts(string_data, preflush, postflush, priority)

    def ard_puts(self,
                 string_data, preflush=0, postflush=0, priority=False,
                 addprompt=True):
        """Push string data into the buffer, if FIFOs are enabled."""
        if self._fifo:
            if addprompt:
                string_data = string_data + '\r> '
            self.ard.puts(string_data, preflush, postflush, priority)

    def arm_calpfc(self, voltage):
        """Issue PFC calibration commands."""
        self.arm['CAL_PFC'] = voltage
        self.arm['NVWRITE'] = True

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
        for dcs in (self.dcs_PriCtl, self.dcs_Arduino, self.dcs_5Vsb):
            dcs.output(0.0, False)
        for rla in (
                self.rla_pic1, self.rla_pic2, self.rla_boot, self.rla_pson,
                self.rla_pot_ud, self.rla_pot_12, self.rla_pot_24):
            rla.set_off()
        self.ocp_pot.disable()


class Sensors():

    """SX-750 Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances."""
        d = logical_devices
        dmm = d.dmm
        # Mirror sensors for Programming result logging
        self.oMirPIC = sensor.Mirror()
        dispatcher.connect(
            self._reset,
            sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
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
        self.PGM_5Vsb = console.Sensor(
            d.ard, 'PGM_5VSB', rdgtype=sensor.ReadingString)
        self.PGM_PwrSw = console.Sensor(
            d.ard, 'PGM_PWRSW', rdgtype=sensor.ReadingString)
        self.PotMax = console.Sensor(
            d.ard, 'POT_MAX', rdgtype=sensor.ReadingString)
        self.Pot12Enable = console.Sensor(
            d.ard, '12_POT_ENABLE', rdgtype=sensor.ReadingString)
        self.Pot24Enable = console.Sensor(
            d.ard, '24_POT_ENABLE', rdgtype=sensor.ReadingString)
        self.PotStep = console.Sensor(
            d.ard, 'POT_STEP', rdgtype=sensor.ReadingString)
        self.PotDisable = console.Sensor(
            d.ard, 'POT_DISABLE', rdgtype=sensor.ReadingString)
        self.ARM_AcFreq = console.Sensor(d.arm, 'ARM-AcFreq')
        self.ARM_AcVolt = console.Sensor(d.arm, 'ARM-AcVolt')
        self.ARM_12V = console.Sensor(d.arm, 'ARM-12V')
        self.ARM_24V = console.Sensor(d.arm, 'ARM-24V')
        self.ARM_SwVer = console.Sensor(
            d.arm, 'ARM_SwVer', rdgtype=sensor.ReadingString)
        self.ARM_SwBld = console.Sensor(
            d.arm, 'ARM_SwBld', rdgtype=sensor.ReadingString)

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirPIC.flush()


class Measurements():

    """SX-750 Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        self._limits = limits
        self.pgmPIC = self._maker('Program', sense.oMirPIC)
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
        self.pgm_5vsb = self._maker('Reply', sense.PGM_5Vsb)
        self.pgm_pwrsw = self._maker('Reply', sense.PGM_PwrSw)
        self.pot_max = self._maker('Reply', sense.PotMax)
        self.pot12_enable = self._maker('Reply', sense.Pot12Enable)
        self.pot24_enable = self._maker('Reply', sense.Pot24Enable)
        self.pot_step = self._maker('Reply', sense.PotStep)
        self.pot_disable = self._maker('Reply', sense.PotDisable)
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
