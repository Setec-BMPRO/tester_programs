#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BP35 Initial Test Program."""

import os
import inspect
import time
from pydispatch import dispatcher

import sensor
import tester
from tester.devlogical import *
from tester.measure import *
from share import SimSerial, ProgramARM
from . import limit
from ..console import Console, Sensor as ConSensor

translate = tester.translate


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._devices = devices
        self._fifo = fifo
        self.dmm = dmm.DMM(devices['DMM'])
        self.acsource = acsource.ACSource(devices['ACS'])
        self.discharge = discharge.Discharge(devices['DIS'])
        self.dcs_vcom = dcsource.DCSource(devices['DCS1'])
        self.dcs_vbat = dcsource.DCSource(devices['DCS2'])
        self.dcs_vaux = dcsource.DCSource(devices['DCS3'])
        self.dcs_sreg = dcsource.DCSource(devices['DCS4'])
        self.dcl_out = dcload.DCLoad(devices['DCL1'])
        self.dcl_bat = dcload.DCLoad(devices['DCL5'])
        self.rla_reset = relay.Relay(devices['RLA1'])
        self.rla_boot = relay.Relay(devices['RLA2'])
        self.rla_pic = relay.Relay(devices['RLA3'])     # PIC programmer
        self.rla_loadsw = relay.Relay(devices['RLA4'])
        self.rla_vbat = relay.Relay(devices['RLA5'])
        # ARM device programmer
        file = os.path.join(os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe()))),
            limit.ARM_BIN)
        self.programmer = ProgramARM(limit.ARM_PORT, file, crpmode=False)
        # Serial connection to the BP35 console
        self.bp35_ser = SimSerial(
            simulation=fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self.bp35_ser.port = limit.ARM_PORT
        # BP35 Console driver
        self.bp35 = Console(self.bp35_ser)

    def bp35_puts(self,
                  string_data, preflush=0, postflush=0, priority=False,
                  addprompt=True):
        """Push string data into the BP35 buffer if FIFOs are enabled."""
        if self._fifo:
            if addprompt:
                string_data = string_data + '\r\n> '
            self.bp35.puts(string_data, preflush, postflush, priority)

    def error_check(self):
        """Check instruments for errors."""
        self._devices.error()

    def reset(self):
        """Reset instruments."""
        self.bp35.close()
        # Switch off AC Source & discharge the unit
        self.acsource.output(voltage=0.0, output=False)
        self.dcl_out.output(2.0)
        time.sleep(1)
        self.discharge.pulse()
        # Switch off DC Sources
        for dcs in (self.dcs_vbat, self.dcs_vaux, self.dcs_sreg):
            dcs.output(0.0, False)
        # Switch off DC Loads
        for ld in (self.dcl_out, self.dcl_bat):
            ld.output(0.0, False)
        # Switch off all Relays
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
        self.mir_pic = sensor.Mirror()
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
            message=translate('bp35_initial', 'msgSnEntry'),
            caption=translate('bp35_initial', 'capSnEntry'))
        self.arm_swver = ConSensor(
            bp35, 'SW_VER', rdgtype=sensor.ReadingString)
        self.arm_acv = ConSensor(bp35, 'AC_V')
        self.arm_acf = ConSensor(bp35, 'AC_F')
        self.arm_sect = ConSensor(bp35, 'SEC_T')
        self.arm_vout = ConSensor(bp35, 'BUS_V')
        self.arm_fan = ConSensor(bp35, 'FAN')
        self.arm_canbind = ConSensor(bp35, 'CAN_BIND')
        # Generate 14 load current sensors
        self.arm_loads = []
        for i in range(1, 15):
            s = ConSensor(bp35, 'LOAD_{}'.format(i))
            self.arm_loads.append(s)
        self.arm_bati = ConSensor(bp35, 'BATT_I')
        self.arm_auxv = ConSensor(bp35, 'AUX_V')
        self.arm_auxi = ConSensor(bp35, 'AUX_I')
        self.arm_solar_alive = ConSensor(bp35, 'SR_ALIVE')
        self.arm_vout_ov = ConSensor(bp35, 'VOUT_OV')

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.mir_pic.flush()
        self.mir_can.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        self.hardware5 = Measurement(limits['HwVer5'], sense.hardware)
        limits['HwVer5'].position_fail = False
        self.pgmpic = Measurement(limits['Program'], sense.mir_pic)
        self.rx_can = Measurement(limits['CAN_RX'], sense.mir_can)
        self.dmm_lock = Measurement(limits['FixtureLock'], sense.lock)
        self.dmm_acin = Measurement(limits['ACin'], sense.acin)
        self.dmm_vpfc = Measurement(limits['Vpfc'], sense.vpfc)
        self.dmm_pri12v = Measurement(limits['12Vpri'], sense.pri12v)
        self.dmm_15vs = Measurement(limits['15Vs'], sense.o15Vs)
        self.dmm_vload = Measurement(limits['Vload'], sense.vload)
        self.dmm_vloadOff = Measurement(limits['VloadOff'], sense.vload)
        self.dmm_vbatin = Measurement(limits['VbatIn'], sense.vbat)
        self.dmm_vbat = Measurement(limits['Vbat'], sense.vbat)
        self.dmm_vsregpre = Measurement(limits['VsetPre'], sense.vsreg)
        self.dmm_vsregpost = Measurement(limits['VsetPost'], sense.vsreg)
        self.dmm_vaux = Measurement(limits['Vaux'], sense.vbat)
        self.dmm_3v3 = Measurement(limits['3V3'], sense.o3v3)
        self.dmm_fanOn = Measurement(limits['FanOn'], sense.fan)
        self.dmm_fanOff = Measurement(limits['FanOff'], sense.fan)
        self.dmm_3v3prog = Measurement(limits['3V3prog'], sense.o3v3prog)
        self.ramp_ocp = Measurement(limits['OCP'], sense.ocp)
        self.ui_sernum = Measurement(limits['SerNum'], sense.sernum)
        self.arm_swver = Measurement(limits['ARM-SwVer'], sense.arm_swver)
        self.arm_acv = Measurement(limits['ARM-AcV'], sense.arm_acv)
        self.arm_acf = Measurement(limits['ARM-AcF'], sense.arm_acf)
        self.arm_secT = Measurement(limits['ARM-SecT'], sense.arm_sect)
        self.arm_vout = Measurement(limits['ARM-Vout'], sense.arm_vout)
        self.arm_fan = Measurement(limits['ARM-Fan'], sense.arm_fan)
        self.arm_can_bind = Measurement(limits['CAN_BIND'], sense.arm_canbind)
        # Generate 14 load current measurements
        self.arm_loads = ()
        for sen in sense.arm_loads:
            m = Measurement(limits['ARM-LoadI'], sen)
            self.arm_loads += (m, )
        self.arm_battI = Measurement(limits['ARM-BattI'], sense.arm_bati)
        self.arm_auxv = Measurement(limits['ARM-AuxV'], sense.arm_auxv)
        self.arm_auxi = Measurement(limits['ARM-AuxI'], sense.arm_auxi)
        self.arm_solar_alive = Measurement(
            limits['SOLAR_ALIVE'], sense.arm_solar_alive)
        self.arm_vout_ov = Measurement(limits['Vout_OV'], sense.arm_vout_ov)
