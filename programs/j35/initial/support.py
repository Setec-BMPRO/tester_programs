#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""J35 Initial Test Program."""

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
        self.dcs_solar = tester.DCSource(devices['DCS4'])
        self.dcl_out = tester.DCLoad(devices['DCL1'])
        self.dcl_bat = tester.DCLoad(devices['DCL5'])
        self.rla_reset = tester.Relay(devices['RLA1'])
        self.rla_boot = tester.Relay(devices['RLA2'])
        self.rla_loadsw = tester.Relay(devices['RLA3'])
        # ARM device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        file = os.path.join(folder, limit.ARM_BIN)
        self.program_arm = share.ProgramARM(
            limit.ARM_PORT, file, crpmode=False,
            boot_relay=self.rla_boot, reset_relay=self.rla_reset)
        # Serial connection to the J35 console
        self.j35_ser = tester.SimSerial(
            simulation=fifo, baudrate=115200, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self.j35_ser.port = limit.ARM_PORT
        # J35 Console driver
        self.j35 = console.Console(self.j35_ser, fifo)

    def j35_puts(self, string_data, preflush=0, postflush=0, priority=False,
                 addprompt=True):
        """Push string data into the J35 buffer if FIFOs are enabled."""
        if self._fifo:
            if addprompt:
                string_data = string_data + '\r\n> '
            self.j35.puts(string_data, preflush, postflush, priority)

    def reset(self):
        """Reset instruments."""
        self.j35.close()
        # Switch off AC Source & discharge the unit
        self.acsource.output(voltage=0.0, output=False)
        self.dcl_out.output(2.0)
        time.sleep(1)
        self.discharge.pulse()
        for dcs in (self.dcs_vcom, self.dcs_vbat, self.dcs_vaux,
                        self.dcs_solar):
            dcs.output(0.0, False)
        for ld in (self.dcl_out, self.dcl_bat):
            ld.output(0.0, False)
        for rla in (self.rla_reset, self.rla_boot, ):
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
        j35 = logical_devices.j35
        self.mir_can = sensor.Mirror(rdgtype=sensor.ReadingString)
        self.olock = sensor.Res(dmm, high=17, low=8, rng=10000, res=0.1)
        self.oacin = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.1)
        self.ovbus = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.1)
        self.o12Vpri = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.01)
        self.ovbat = sensor.Vdc(dmm, high=4, low=4, rng=100, res=0.001)
        self.ovload = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self.oaux = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.001)
        self.oair = sensor.Vdc(dmm, high=7, low=3, rng=100, res=0.001)
        self.o3V3U = sensor.Vdc(dmm, high=8, low=3, rng=10, res=0.001)
        self.o3V3 = sensor.Vdc(dmm, high=9, low=3, rng=10, res=0.001)
        self.o15Vs = sensor.Vdc(dmm, high=10, low=3, rng=100, res=0.01)
        self.ofan = sensor.Vdc(dmm, high=12, low=5, rng=100, res=0.01)
        self.ocanpwr = sensor.Vdc(dmm, high=13, low=3, rng=100, res=0.01)
        self.sernum = sensor.DataEntry(
            message=tester.translate('j35_initial', 'msgSnEntry'),
            caption=tester.translate('j35_initial', 'capSnEntry'))
        self.arm_swver = console.Sensor(
            j35, 'SW_VER', rdgtype=sensor.ReadingString)
        self.arm_auxv = console.Sensor(j35, 'AUX_V')
        self.arm_auxi = console.Sensor(j35, 'AUX_I')
        self.arm_vout_ov = console.Sensor(j35, 'VOUT_OV')
        self.arm_acv = console.Sensor(j35, 'AC_V')
        self.arm_acf = console.Sensor(j35, 'AC_F')
        self.arm_sect = console.Sensor(j35, 'SEC_T')
        self.arm_vout = console.Sensor(j35, 'BUS_V')
        self.arm_fan = console.Sensor(j35, 'FAN')
        self.arm_bati = console.Sensor(j35, 'BATT_I')
        self.arm_canbind = console.Sensor(j35, 'CAN_BIND')
        # Generate load current sensors
        self.arm_loads = []
        for i in range(limit.LOAD_COUNT):
            s = console.Sensor(j35, 'LOAD_{}'.format(i + 1))
            self.arm_loads.append(s)
        self.ocp = sensor.Ramp(
            stimulus=logical_devices.dcl_bat, sensor=self.ovbat,
            detect_limit=(limits['InOCP'], ),
            start=4.0, stop=10.0, step=0.5, delay=0.2)

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
        Measurement = tester.Measurement
        self.dmm_lock = Measurement(limits['FixtureLock'], sense.olock)
        self.dmm_acin = Measurement(limits['ACin'], sense.oacin)
        self.dmm_vbus = Measurement(limits['Vbus'], sense.ovbus)
        self.dmm_12vpri = Measurement(limits['12Vpri'], sense.o12Vpri)
        self.dmm_vload = Measurement(limits['Vload'], sense.ovload)
        self.dmm_vloadoff = Measurement(limits['VloadOff'], sense.ovload)
        self.dmm_vbatin = Measurement(limits['VbatIn'], sense.ovbat)
        self.dmm_vbatout = Measurement(limits['VbatOut'], sense.ovbat)
        self.dmm_vair = Measurement(limits['Vair'], sense.oair)
        self.dmm_vaux = Measurement(limits['Vaux'], sense.oaux)
        self.dmm_vbat = Measurement(limits['Vbat'], sense.ovbat)
        self.dmm_3v3u = Measurement(limits['3V3U'], sense.o3V3U)
        self.dmm_3v3 = Measurement(limits['3V3'], sense.o3V3)
        self.dmm_15vs = Measurement(limits['15Vs'], sense.o15Vs)
        self.dmm_fanOn = Measurement(limits['FanOn'], sense.ofan)
        self.dmm_fanOff = Measurement(limits['FanOff'], sense.ofan)
        self.ui_sernum = Measurement(limits['SerNum'], sense.sernum)
        self.arm_swver = Measurement(limits['ARM-SwVer'], sense.arm_swver)
        self.arm_auxv = Measurement(limits['ARM-AuxV'], sense.arm_auxv)
        self.arm_auxi = Measurement(limits['ARM-AuxI'], sense.arm_auxi)
        self.arm_vout_ov = Measurement(limits['Vout_OV'], sense.arm_vout_ov)
        self.arm_acv = Measurement(limits['ARM-AcV'], sense.arm_acv)
        self.arm_acf = Measurement(limits['ARM-AcF'], sense.arm_acf)
        self.arm_secT = Measurement(limits['ARM-SecT'], sense.arm_sect)
        self.arm_vout = Measurement(limits['ARM-Vout'], sense.arm_vout)
        self.arm_fan = Measurement(limits['ARM-Fan'], sense.arm_fan)
        self.arm_battI = Measurement(limits['ARM-BattI'], sense.arm_bati)
        self.dmm_canpwr = Measurement(limits['CanPwr'], sense.ocanpwr)
        self.rx_can = Measurement(limits['CAN_RX'], sense.mir_can)
        self.arm_can_bind = Measurement(limits['CAN_BIND'], sense.arm_canbind)
        # Generate load current measurements
        self.arm_loads = ()
        for sen in sense.arm_loads:
            m = Measurement(limits['ARM-LoadI'], sen)
            self.arm_loads += (m, )
        self.ramp_ocp = Measurement(limits['OCP'], sense.ocp)


class SubTests():

    """SubTest Steps."""

    def __init__(self, dev, mes):
        """Create SubTest Step instances."""
        # RemoteSw: Activate sw, measure.
        self.remote_sw = tester.SubStep((
            tester.RelaySubStep(((dev.rla_loadsw, True), )),
            tester.MeasureSubStep((mes.dmm_vloadoff, ), timeout=5),
            tester.RelaySubStep(((dev.rla_loadsw, False), )),
            tester.MeasureSubStep((mes.dmm_vload, ), timeout=5),
            ))
        # OCP:
        self.ocp = tester.SubStep((
            tester.MeasureSubStep((mes.ramp_ocp, ), timeout=5),
            tester.LoadSubStep(((dev.dcl_out, 0.0), (dev.dcl_bat, 0.0), )),
            ))
