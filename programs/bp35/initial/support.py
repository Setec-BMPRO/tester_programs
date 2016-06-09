#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BP35 Initial Test Program."""

import os
import inspect
import time
from pydispatch import dispatcher

import tester
import share
import sensor
from . import limit
from .. import console


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.discharge = tester.Discharge(devices['DIS'])
        self.dcs_vcom = tester.DCSource(devices['DCS1'])
        self.dcs_vbat = tester.DCSource(devices['DCS2'])
        self.dcs_vaux = tester.DCSource(devices['DCS3'])
        self.dcs_sreg = tester.DCSource(devices['DCS4'])
        self.dcl_out = tester.DCLoad(devices['DCL1'])
        self.dcl_bat = tester.DCLoad(devices['DCL5'])
        self.rla_reset = tester.Relay(devices['RLA1'])
        self.rla_boot = tester.Relay(devices['RLA2'])
        self.rla_pic = tester.Relay(devices['RLA3'])
        self.rla_loadsw = tester.Relay(devices['RLA4'])
        self.rla_vbat = tester.Relay(devices['RLA5'])
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        file = os.path.join(folder, limit.ARM_BIN)
        self.program_arm = share.ProgramARM(
            limit.ARM_PORT, file, crpmode=False,
            boot_relay=self.rla_boot, reset_relay=self.rla_reset)
        # PIC device programmer
        self.program_pic = share.ProgramPIC(
            limit.PIC_HEX, folder, '33FJ16GS402', self.rla_pic)
        # Serial connection to the BP35 console
        self.bp35_ser = share.SimSerial(
            simulation=fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self.bp35_ser.port = limit.ARM_PORT
        # BP35 Console driver
        self.bp35 = console.Console(self.bp35_ser)

    def bp35_puts(self,
                  string_data, preflush=0, postflush=0, priority=False,
                  addprompt=True):
        """Push string data into the BP35 buffer if FIFOs are enabled."""
        if self._fifo:
            if addprompt:
                string_data = string_data + '\r\n> '
            self.bp35.puts(string_data, preflush, postflush, priority)

    def reset(self):
        """Reset instruments."""
        self.bp35.close()
        # Switch off AC Source & discharge the unit
        self.acsource.output(voltage=0.0, output=False)
        self.dcl_out.output(2.0)
        time.sleep(1)
        self.discharge.pulse()
        for dcs in (self.dcs_vbat, self.dcs_vaux, self.dcs_sreg):
            dcs.output(0.0, False)
        for ld in (self.dcl_out, self.dcl_bat):
            ld.output(0.0, False)
        for rla in (self.rla_reset, self.rla_boot, self.rla_pic,
                    self.rla_loadsw, self.rla_vbat):
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dispatcher.connect(self._reset, sender=tester.signals.Thread.tester,
                           signal=tester.signals.TestRun.stop)
        dmm = logical_devices.dmm
        bp35 = logical_devices.bp35
        self.mir_can = sensor.Mirror(rdgtype=sensor.ReadingString)
        self.acin = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self.vpfc = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.001)
        self.vload = sensor.Vdc(dmm, high=3, low=3, rng=100, res=0.001)
        self.vbat = sensor.Vdc(dmm, high=4, low=4, rng=100, res=0.001)
        self.vsreg = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self.pri12v = sensor.Vdc(dmm, high=5, low=2, rng=100, res=0.001)
        self.o3v3 = sensor.Vdc(dmm, high=6, low=3, rng=10, res=0.001)
        self.fan = sensor.Vdc(dmm, high=7, low=5, rng=100, res=0.01)
        self.hardware = sensor.Res(dmm, high=8, low=4, rng=1000000, res=1)
        self.o15Vs = sensor.Vdc(dmm, high=9, low=3, rng=100, res=0.01)
        self.lock = sensor.Res(dmm, high=10, low=6, rng=10000, res=1)
        self.o3v3prog = sensor.Vdc(dmm, high=11, low=3, rng=10, res=0.001)
        self.ocp = sensor.Ramp(
            stimulus=logical_devices.dcl_bat, sensor=self.vbat,
            detect_limit=(limits['InOCP'], ),
            start=4.0, stop=10.0, step=0.5, delay=0.1)
        self.sernum = sensor.DataEntry(
            message=tester.translate('bp35_initial', 'msgSnEntry'),
            caption=tester.translate('bp35_initial', 'capSnEntry'))
        self.arm_swver = console.Sensor(
            bp35, 'SW_VER', rdgtype=sensor.ReadingString)
        self.arm_acv = console.Sensor(bp35, 'AC_V')
        self.arm_acf = console.Sensor(bp35, 'AC_F')
        self.arm_sect = console.Sensor(bp35, 'SEC_T')
        self.arm_vout = console.Sensor(bp35, 'BUS_V')
        self.arm_fan = console.Sensor(bp35, 'FAN')
        self.arm_canbind = console.Sensor(bp35, 'CAN_BIND')
        # Generate 14 load current sensors
        self.arm_loads = []
        for i in range(1, 15):
            s = console.Sensor(bp35, 'LOAD_{}'.format(i))
            self.arm_loads.append(s)
        self.arm_bati = console.Sensor(bp35, 'BATT_I')
        self.arm_auxv = console.Sensor(bp35, 'AUX_V')
        self.arm_auxi = console.Sensor(bp35, 'AUX_I')
        self.arm_solar_alive = console.Sensor(bp35, 'SR_ALIVE')
        self.arm_solar_relay = console.Sensor(bp35, 'SR_RELAY')
        self.arm_solar_error = console.Sensor(bp35, 'SR_ERROR')
        self.arm_vout_ov = console.Sensor(bp35, 'VOUT_OV')

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.mir_can.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self._limits = limits
        self.hardware5 = self._maker('HwVer5', sense.hardware, False)
        self.rx_can = self._maker('CAN_RX', sense.mir_can)
        self.dmm_lock = self._maker('FixtureLock', sense.lock)
        self.dmm_acin = self._maker('ACin', sense.acin)
        self.dmm_vpfc = self._maker('Vpfc', sense.vpfc)
        self.dmm_pri12v = self._maker('12Vpri', sense.pri12v)
        self.dmm_15vs = self._maker('15Vs', sense.o15Vs)
        self.dmm_vload = self._maker('Vload', sense.vload)
        self.dmm_vloadOff = self._maker('VloadOff', sense.vload)
        self.dmm_vbatin = self._maker('VbatIn', sense.vbat)
        self.dmm_vbat = self._maker('Vbat', sense.vbat)
        self.dmm_vsregpre = self._maker('VsetPre', sense.vsreg)
        self.dmm_vsregpost = self._maker('VsetPost', sense.vsreg)
        self.dmm_vaux = self._maker('Vaux', sense.vbat)
        self.dmm_3v3 = self._maker('3V3', sense.o3v3)
        self.dmm_fanOn = self._maker('FanOn', sense.fan)
        self.dmm_fanOff = self._maker('FanOff', sense.fan)
        self.dmm_3v3prog = self._maker('3V3prog', sense.o3v3prog)
        self.ramp_ocp = self._maker('OCP', sense.ocp)
        self.ui_sernum = self._maker('SerNum', sense.sernum)
        self.arm_swver = self._maker('ARM-SwVer', sense.arm_swver)
        self.arm_acv = self._maker('ARM-AcV', sense.arm_acv)
        self.arm_acf = self._maker('ARM-AcF', sense.arm_acf)
        self.arm_secT = self._maker('ARM-SecT', sense.arm_sect)
        self.arm_vout = self._maker('ARM-Vout', sense.arm_vout)
        self.arm_fan = self._maker('ARM-Fan', sense.arm_fan)
        self.arm_can_bind = self._maker('CAN_BIND', sense.arm_canbind)
        # Generate 14 load current measurements
        self.arm_loads = ()
        for sen in sense.arm_loads:
            m = self._maker('ARM-LoadI', sen)
            self.arm_loads += (m, )
        self.arm_battI = self._maker('ARM-BattI', sense.arm_bati)
        self.arm_auxv = self._maker('ARM-AuxV', sense.arm_auxv)
        self.arm_auxi = self._maker('ARM-AuxI', sense.arm_auxi)
        self.arm_solar_alive = self._maker(
            'SOLAR_ALIVE', sense.arm_solar_alive)
        self.arm_solar_relay = self._maker(
            'SOLAR_RELAY', sense.arm_solar_relay)
        self.arm_solar_error = self._maker(
            'SOLAR_ERROR', sense.arm_solar_error)
        self.arm_vout_ov = self._maker('Vout_OV', sense.arm_vout_ov)

    def _maker(self, limitname, sensor, position_fail=True):
        """Create a Measurement.

        @param limitname Test Limit name
        @param sensor Sensor to use
        @return tester.Measurement instance

        """
        if not position_fail:
            self._limits[limitname].position_fail = False
        return tester.Measurement(self._limits[limitname], sensor)
