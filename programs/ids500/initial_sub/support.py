#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Initial Subboard Test Program."""

import os
import inspect

import share
import tester
import sensor
from . import limit
from .. import console

class LogicalDevMicro():

    """Micro Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        self.dcs_vcc = tester.DCSource(devices['DCS1'])
        self.rla_mic = tester.Relay(devices['RLA10'])
        # PIC device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self.program_picMic = share.ProgramPIC(
            limit.PIC_HEX_MIC, folder, '18F4520', self.rla_mic)
        # Serial connection to the console to communicate with the PIC
        pic_ser = tester.SimSerial(
            simulation=self._fifo, baudrate=19200, timeout=0.1)
        # Set port separately, as we don't want it opened yet
        pic_ser.port = limit.PIC_PORT
        self.pic = console.Console(pic_ser)

    def pic_puts(self,
                 string_data, preflush=0, postflush=0, priority=False,
                 addprompt=True):
        """Push string data into the buffer, if FIFOs are enabled."""
        if self._fifo:
            if addprompt:
                string_data = string_data + '\r> '
            self.pic.puts(string_data, preflush, postflush, priority)

    def reset(self):
        """Reset instruments."""
        self.pic.close()
        self.dcs_vcc.output(0.0, False)
        self.rla_mic.set_off()


class LogicalDevAux():

    """Aux Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcs_5Vfix = tester.DCSource(devices['DCS1'])
        self.dcs_fan = tester.DCSource(devices['DCS5'])
        self.dcl_5V = tester.DCLoad(devices['DCL1'])
        self.dcl_15Vp = tester.DCLoad(devices['DCL2'])
        self.rla_enAux = tester.Relay(devices['RLA1'])
        self.rla_en15Vpsw = tester.Relay(devices['RLA2'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        for dcs in (self.dcs_5Vfix, self.dcs_fan):
            dcs.output(0.0, False)
        for dcl in (self.dcl_5V, self.dcl_15Vp, ):
            dcl.output(0.0, False)
        for rla in (self.rla_enAux, self.rla_en15Vpsw, ):
            rla.set_off()


class LogicalDevBias():

    """Bias Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcs_fan = tester.DCSource(devices['DCS5'])
        self.dcl_12Vsbraw = tester.DCLoad(devices['DCL1'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        self.dcs_fan.output(0.0, False)
        self.dcl_12Vsbraw.output(0.0, False)


class LogicalDevBus():

    """Bus Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcs_prictl = tester.DCSource(devices['DCS4'])
        self.dcs_fan = tester.DCSource(devices['DCS5'])
        self.dcl_20VT = tester.DCLoad(devices['DCL1'])
        self.dcl_9V = tester.DCLoad(devices['DCL2'])
        self.dcl_20VL = tester.DCLoad(devices['DCL3'])
        self.dcl__20 = tester.DCLoad(devices['DCL4'])
        self.rla_enT = tester.Relay(devices['RLA1'])
        self.rla_enBC9 = tester.Relay(devices['RLA2'])
        self.rla_enL = tester.Relay(devices['RLA3'])
        self.rla_enBC20 = tester.Relay(devices['RLA4'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        for dcs in (self.dcs_prictl, self.dcs_fan, ):
            dcs.output(0.0, False)
        for dcl in (self.dcl_20VT, self.dcl_9V, self.dcl_20VL,
                    self.dcl__20):
            dcl.output(0.0, False)
        for rla in (self.rla_enT, self.rla_enBC9, self.rla_enL,
                    self.rla_enBC20):
            rla.set_off()

class LogicalDevSyn():

    """Logical Devices."""

    def __init__(self, devices, fifo):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self._fifo = fifo
        self.dmm = tester.DMM(devices['DMM'])
        self.acsource = tester.ACSource(devices['ACS'])
        self.dcs_vsec5Vlddtec = tester.DCSource(devices['DCS1'])
        self.dcs_lddiset = tester.DCSource(devices['DCS2'])
        self.dcs_tecvset = tester.DCSource(devices['DCS3'])
        self.dcs_fan = tester.DCSource(devices['DCS5'])
        self.dcl_tecout = tester.DCLoad(devices['DCL5'])
        self.rla_enTec = tester.Relay(devices['RLA1'])
        self.rla_enIs = tester.Relay(devices['RLA2'])
        self.rla_lddcrowbar = tester.Relay(devices['RLA3'])
        self.rla_interlock = tester.Relay(devices['RLA4'])
        self.rla_lddtest = tester.Relay(devices['RLA5'])
        self.rla_tecphase = tester.Relay(devices['RLA6'])
        self.rla_fault = tester.Relay(devices['RLA11'])
        self.rla_enable = tester.Relay(devices['RLA12'])
        self.rla_syn = tester.Relay(devices['RLA7'])
        # PIC device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self.program_picSyn = share.ProgramPIC(
            limit.PIC_HEX_SYN, folder, '18F4321', self.rla_syn)

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        for dcs in (self.dcs_vsec5Vlddtec, self.dcs_lddiset, self.dcs_tecvset,
                    self.dcs_fan):
            dcs.output(0.0, False)
        self.dcl_tecout.output(0.0, False)
        for rla in (self.rla_enTec, self.rla_enIs, self.rla_lddcrowbar,
                    self.rla_interlock, self.rla_lddtest, self.rla_tecphase,
                    self.rla_fault, self.rla_enable, self.rla_syn):
            rla.set_off()


class SensorMicro():

    """Micro Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        pic = logical_devices.pic
        self.oVsec5VuP = sensor.Vdc(dmm, high=19, low=1, rng=10, res=0.001)
        self.oSwRev = console.Sensor(
                pic, 'PIC-SwRev', rdgtype=sensor.ReadingString)
        self.oMicroTemp = console.Sensor(
                pic, 'PIC-MicroTemp', rdgtype=sensor.ReadingString)


class SensorAux():

    """Aux Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        self.olock = sensor.Res(dmm, high=18, low=5, rng=10000, res=0.1)
        self.o5V = sensor.Vdc(dmm, high=1, low=1, rng=10, res=0.001)
        self.o15V = sensor.Vdc(dmm, high=23, low=1, rng=100, res=0.001)
        self.o_15V = sensor.Vdc(dmm, high=22, low=1, rng=100, res=0.001)
        self.o15Vp = sensor.Vdc(dmm, high=4, low=1, rng=100, res=0.001)
        self.o20VL = sensor.Vdc(dmm, high=11, low=1, rng=100, res=0.001)
        self.o_20V = sensor.Vdc(dmm, high=13, low=1, rng=100, res=0.001)
        self.o15VpSw = sensor.Vdc(dmm, high=14, low=1, rng=100, res=0.001)
        self.oACurr5V = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.001)
        self.oACurr15V = sensor.Vdc(dmm, high=16, low=1, rng=10, res=0.001)
        self.oAuxTemp = sensor.Vdc(dmm, high=17, low=1, rng=10, res=0.001)
        self.oPwrGood = sensor.Vdc(dmm, high=18, low=1, rng=10, res=0.001)
        self.oOCP5V = sensor.Ramp(
            stimulus=logical_devices.dcl_5V, sensor=self.o5V,
            detect_limit=(limits['InOCP5V'], ),
            start=6.0, stop=11.0, step=0.1, delay=0.1)
        self.oOCP15Vp = sensor.Ramp(
            stimulus=logical_devices.dcl_15Vp, sensor=self.o15Vp,
            detect_limit=(limits['InOCP15Vp'], ),
            start=6.0, stop=11.0, step=0.1, delay=0.1)


class SensorBias():

    """Bias Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        self.olock = sensor.Res(dmm, high=18, low=5, rng=10000, res=0.1)
        self.o400V = sensor.Vdc(dmm, high=9, low=2, rng=1000, res=0.001)
        self.oPVcc = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.001)
        self.o12Vsbraw = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self.oOCP = sensor.Ramp(
            stimulus=logical_devices.dcl_12Vsbraw, sensor=self.o12Vsbraw,
            detect_limit=(limits['InOCP'], ),
            start=1.5, stop=2.3, step=0.1, delay=0.1, reset=False)


class SensorBus():

    """Bus Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        self.olock = sensor.Res(dmm, high=18, low=5, rng=10000, res=0.1)
        self.o400V = sensor.Vdc(dmm, high=9, low=2, rng=1000, res=0.001)
        self.o20VT = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self.o9V = sensor.Vdc(dmm, high=3, low=1, rng=100, res=0.001)
        self.o20VL = sensor.Vdc(dmm, high=2, low=1, rng=100, res=0.001)
        self.o_20V = sensor.Vdc(dmm, high=20, low=1, rng=100, res=0.001)


class SensorSyn():

    """SynBuck Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used
           @param limits Product test limits

        """
        dmm = logical_devices.dmm
        self.olock = sensor.Res(dmm, high=18, low=5, rng=10000, res=0.1)
        self.oTec = sensor.Vdc(dmm, high=15, low=3, rng=100, res=0.001)
        self.oTecVmon = sensor.Vdc(dmm, high=24, low=1, rng=10, res=0.001)
        self.oTecVset = sensor.Vdc(dmm, high=14, low=1, rng=10, res=0.001)
        self.oLdd = sensor.Vdc(dmm, high=21, low=1, rng=10, res=0.001)
        self.oLddVmon = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.001)
        self.oLddImon = sensor.Vdc(dmm, high=6, low=1, rng=10, res=0.001)
        self.oLddShunt = sensor.Vdc(dmm, high=8, low=4, rng=0.1, res=0.0001,
                                                            scale=1000)
        self.o20VT = sensor.Vdc(dmm, high=10, low=1, rng=100, res=0.001)
        self.o9V = sensor.Vdc(dmm, high=12, low=1, rng=100, res=0.001)
        self.o_20V = sensor.Vdc(dmm, high=13, low=1, rng=100, res=0.001)
        self.oFault = sensor.Vdc(dmm, high=4, low=1, rng=10, res=0.001)
        self.oLddIset = sensor.Vdc(dmm, high=7, low=1, rng=10, res=0.001)
        lo_lim, hi_lim = limits['AdjLimits'].limit
        self.oAdjLdd = sensor.AdjustAnalog(
            sensor=self.oLddShunt,
            low=lo_lim, high=hi_lim,
            message=tester.translate('IDS500 Initial Syn', 'AdjR489'),
            caption=tester.translate('IDS500 Initial Syn', 'capAdjLdd'))


class MeasureMicro():

    """Micro Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.dmm_vsec5VuP = Measurement(limits['5V'], sense.oVsec5VuP)
        self.swrev = Measurement(limits['Comms'], sense.oSwRev)
        self.microtemp = Measurement(limits['Comms'], sense.oMicroTemp)


class MeasureAux():

    """Aux Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.dmm_lock = Measurement(limits['FixtureLock'], sense.olock)
        self.dmm_5Voff = Measurement(limits['5VOff'], sense.o5V)
        self.dmm_5V = Measurement(limits['5V'], sense.o5V)
        self.dmm_15Vpoff = Measurement(limits['15VpOff'], sense.o15Vp)
        self.dmm_15Vp = Measurement(limits['15Vp'], sense.o15Vp)
        self.dmm_15Vpswoff = Measurement(limits['15VpSwOff'], sense.o15VpSw)
        self.dmm_15Vpsw = Measurement(limits['15VpSw'], sense.o15VpSw)
        self.dmm_20VL = Measurement(limits['20VL'], sense.o20VL)
        self.dmm__20V = Measurement(limits['-20V'], sense.o_20V)
        self.dmm_15V = Measurement(limits['15V'], sense.o15V)
        self.dmm__15V = Measurement(limits['-15V'], sense.o_15V)
        self.dmm_pwrgoodoff = Measurement(limits['PwrGoodOff'], sense.oPwrGood)
        self.dmm_pwrgood = Measurement(limits['PwrGood'], sense.oPwrGood)
        self.dmm_ac5V_1 = Measurement(limits['ACurr_5V_1'], sense.oACurr5V)
        self.dmm_ac5V_2 = Measurement(limits['ACurr_5V_2'], sense.oACurr5V)
        self.dmm_ac15V_1 = Measurement(limits['ACurr_15V_1'], sense.oACurr15V)
        self.dmm_ac15V_2 = Measurement(limits['ACurr_15V_2'], sense.oACurr15V)
        self.dmm_auxtemp = Measurement(limits['AuxTemp'], sense.oAuxTemp)
        self.ramp_OCP5V = Measurement(limits['OCP'], sense.oOCP5V)
        self.ramp_OCP15Vp = Measurement(limits['OCP'], sense.oOCP15Vp)


class MeasureBias():

    """Bias Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.dmm_lock = Measurement(limits['FixtureLock'], sense.olock)
        self.dmm_400V = Measurement(limits['400V'], sense.o400V)
        self.dmm_pvcc = Measurement(limits['PVcc'], sense.oPVcc)
        self.dmm_12Vsbraw = Measurement(limits['12VsbRaw'], sense.o12Vsbraw)
        self.dmm_12Vsbraw2 = Measurement(limits['OCP Trip'], sense.o12Vsbraw)
        self.ramp_OCP = Measurement(limits['OCP'], sense.oOCP)


class MeasureBus():

    """Bus Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.dmm_lock = Measurement(limits['FixtureLock'], sense.olock)
        self.dmm_400V = Measurement(limits['400V'], sense.o400V)
        self.dmm_20VT_0 = Measurement(limits['20VT_load0_out'], sense.o20VT)
        self.dmm_9V_0 = Measurement(limits['9V_load0_out'], sense.o9V)
        self.dmm_20VL_0 = Measurement(limits['20VL_load0_out'], sense.o20VL)
        self.dmm__20V_0 = Measurement(limits['-20V_load0_out'], sense.o_20V)
        self.dmm_20VT_1 = Measurement(limits['20VT_load1_out'], sense.o20VT)
        self.dmm_9V_1 = Measurement(limits['9V_load1_out'], sense.o9V)
        self.dmm_20VL_1 = Measurement(limits['20VL_load1_out'], sense.o20VL)
        self.dmm__20V_1 = Measurement(limits['-20V_load1_out'], sense.o_20V)
        self.dmm_20VT_2 = Measurement(limits['20VT_load2_out'], sense.o20VT)
        self.dmm_9V_2 = Measurement(limits['9V_load2_out'], sense.o9V)
        self.dmm_20VL_2 = Measurement(limits['20VL_load2_out'], sense.o20VL)
        self.dmm__20V_2 = Measurement(limits['-20V_load2_out'], sense.o_20V)
        self.dmm_20VT_3 = Measurement(limits['20VT_load3_out'], sense.o20VT)
        self.dmm_9V_3 = Measurement(limits['9V_load3_out'], sense.o9V)
        self.dmm_20VL_3 = Measurement(limits['20VL_load3_out'], sense.o20VL)
        self.dmm__20V_3 = Measurement(limits['-20V_load3_out'], sense.o_20V)


class MeasureSyn():

    """SynBuck Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.dmm_lock = Measurement(limits['FixtureLock'], sense.olock)
        self.dmm_20VT = Measurement(limits['20VT'], sense.o20VT)
        self.dmm__20V = Measurement(limits['-20V'], sense.o_20V)
        self.dmm_9V = Measurement(limits['9V'], sense.o9V)
        self.dmm_tecOff = Measurement(limits['TecOff'], sense.oTec)
        self.dmm_tec0V = Measurement(limits['Tec0V'], sense.oTec)
        self.dmm_tec2V5 = Measurement(limits['Tec2V5'], sense.oTec)
        self.dmm_tec5V = Measurement(limits['Tec5V'], sense.oTec)
        self.dmm_tec5Vrev = Measurement(limits['Tec5V_Rev'], sense.oTec)
        self.dmm_tecVmonOff = Measurement(limits['TecVmonOff'], sense.oTecVmon)
        self.dmm_tecVmon0V = Measurement(limits['TecVmon0V'], sense.oTecVmon)
        self.dmm_tecVmon2V5 = Measurement(limits['TecVmon2V5'], sense.oTecVmon)
        self.dmm_tecVmon5V = Measurement(limits['TecVmon5V'], sense.oTecVmon)
        self.dmm_tecVsetOff = Measurement(limits['TecVsetOff'], sense.oTecVset)
        self.dmm_lddOff = Measurement(limits['LddOff'], sense.oLdd)
        self.dmm_ldd0V = Measurement(limits['Ldd0V'], sense.oLdd)
        self.dmm_ldd0V6 = Measurement(limits['Ldd0V6'], sense.oLdd)
        self.dmm_ldd5V = Measurement(limits['Ldd5V'], sense.oLdd)
        self.dmm_lddVmonOff = Measurement(limits['LddVmonOff'], sense.oLddVmon)
        self.dmm_lddImonOff = Measurement(limits['LddImonOff'], sense.oLddImon)
        self.dmm_lddImon0V = Measurement(limits['LddImon0V'], sense.oLddImon)
        self.dmm_lddImon0V6 = Measurement(limits['LddImon0V6'], sense.oLddImon)
        self.dmm_lddImon5V = Measurement(limits['LddImon5V'], sense.oLddImon)
        self.dmm_ISIout0A = Measurement(limits['ISIout0A'], sense.oLddShunt)
        self.dmm_ISIout6A = Measurement(limits['ISIout6A'], sense.oLddShunt)
        self.dmm_ISIout50A = Measurement(limits['ISIout50A'], sense.oLddShunt)
        self.dmm_ISIset5V = Measurement(limits['ISIset5V'], sense.oLddIset)
        self.ui_AdjLdd = Measurement(limits['Notify'], sense.oAdjLdd)
        self.dmm_ISIoutPost = Measurement(limits['AdjLimits'], sense.oLddShunt)


class SubTestAux():

    """Aux SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # PowerUp:  Measure fixture lock, AC input, measure
        self.pwrup = tester.SubStep((
            tester.MeasureSubStep((m.dmm_lock, ), timeout=5),
            tester.DcSubStep(setting=((d.dcs_fan, 12.0), ), output=True),
            tester.AcSubStep(
                acs=d.acsource, voltage=240.0, output=True, delay=3.0),
            tester.MeasureSubStep(
                (m.dmm_20VL, m.dmm__20V, m.dmm_5Voff, m.dmm_15V, m.dmm__15V,
              m.dmm_15Vpoff, m.dmm_15Vpswoff, m.dmm_pwrgoodoff, ), timeout=5),
            ))
        # KeySwitch: Enable Aux, measure, enable +15Vpsw, measure.
        self.key_sws = tester.SubStep((
            tester.DcSubStep(setting=((d.dcs_5Vfix, 5.0), ), output=True),
            tester.RelaySubStep(((d.rla_enAux, True), )),
            tester.MeasureSubStep(
                (m.dmm_5V, m.dmm_15V, m.dmm__15V, m.dmm_15Vp, m.dmm_15Vpswoff,
                m.dmm_pwrgood, ), timeout=5),
            tester.RelaySubStep(((d.rla_en15Vpsw, True), )),
            tester.MeasureSubStep((m.dmm_15Vpsw, ), timeout=5),
            ))
        # ACurrent: Load, measure.
        self.acurr = tester.SubStep((
            tester.LoadSubStep(
                ((d.dcl_5V, 0.0), (d.dcl_15Vp, 0.0), ), output=True),
            tester.MeasureSubStep((m.dmm_ac5V_1, m.dmm_ac15V_1, ), timeout=5),
            tester.LoadSubStep(((d.dcl_5V, 6.0), )),
            tester.MeasureSubStep((m.dmm_ac5V_2, m.dmm_ac15V_1, ), timeout=5),
            tester.LoadSubStep(((d.dcl_15Vp, 4.0), )),
            tester.MeasureSubStep((m.dmm_ac5V_2, m.dmm_ac15V_2, ), timeout=5),
            tester.LoadSubStep(((d.dcl_5V, 0.0), (d.dcl_15Vp, 0.0), )),
            ))
        # OCP:  OCP, AuxTemp.
        self.ocp = tester.SubStep((
            tester.MeasureSubStep((m.dmm_5V, m.ramp_OCP5V, ), timeout=5),
            tester.LoadSubStep(((d.dcl_5V, 0.0), ), output=False),
            tester.RelaySubStep(((d.rla_enAux, False), ), delay=1),
            tester.RelaySubStep(((d.rla_enAux, True), )),
            tester.MeasureSubStep(
                    (m.dmm_15Vp, m.ramp_OCP15Vp, m.dmm_auxtemp,), timeout=5),
            ))


class SubTestBus():

    """Bus SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # PowerUp:  Measure fixture lock, AC input, measure
        self.pwrup = tester.SubStep((
            tester.MeasureSubStep((m.dmm_lock, ), timeout=5),
            tester.DcSubStep(
            setting=((d.dcs_prictl, 13.0), (d.dcs_fan, 12.0),), output=True),
            tester.AcSubStep(
                acs=d.acsource, voltage=240.0, output=True, delay=0.5),
            tester.MeasureSubStep((m.dmm_400V, ), timeout=5),
            ))
        # TecLddStartup: Enable, load, measure.
        self.tl_startup = tester.SubStep((
            tester.RelaySubStep(((d.rla_enBC20, True), (d.rla_enT, True),
                    (d.rla_enBC9, True), (d.rla_enL, True), )),
            tester.LoadSubStep(((d.dcl_20VT, 0.0), (d.dcl_9V, 0.0),
                        (d.dcl_20VL, 0.0), (d.dcl__20, 0.0), ), output=True),
            tester.MeasureSubStep((m.dmm_20VT_0, m.dmm_9V_0, m.dmm_20VL_0,
                                m.dmm__20V_0, ), timeout=5),
            tester.LoadSubStep(((d.dcl_9V, 10.0), )),
            tester.MeasureSubStep((m.dmm_20VT_1, m.dmm_9V_1, m.dmm_20VL_1,
                                m.dmm__20V_1, ), timeout=5),
            tester.LoadSubStep(((d.dcl_20VL, 2.0), (d.dcl__20, 0.4), )),
            tester.MeasureSubStep((m.dmm_20VT_2, m.dmm_9V_2, m.dmm_20VL_2,
                                m.dmm__20V_2, ), timeout=5),
            tester.LoadSubStep(((d.dcl_20VT, 15.0), (d.dcl_9V, 0.0),
                                (d.dcl_20VL, 0.0), (d.dcl__20, 0.0), )),
            tester.MeasureSubStep((m.dmm_20VT_3, m.dmm_9V_3, m.dmm_20VL_3,
                                m.dmm__20V_3, ), timeout=5),
            ))


class SubTestSyn():

    """Syn SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # PowerUp:  AC input, measure
        self.pwrup = tester.SubStep((
            tester.DcSubStep(setting=((d.dcs_fan, 12.0), ), output=True),
            tester.AcSubStep(
                acs=d.acsource, voltage=240.0, output=True, delay=1.0),
            tester.MeasureSubStep(
                (m.dmm_20VT, m.dmm__20V, m.dmm_9V, m.dmm_tecOff, m.dmm_lddOff,
                m.dmm_lddVmonOff, m.dmm_lddImonOff, m.dmm_tecVmonOff,
                m.dmm_tecVsetOff), timeout=5),
            ))
        # TecEnable: Enable, set, measure
        self.tec_en = tester.SubStep((
            tester.RelaySubStep(((d.rla_tecphase, True), ), delay=0.5),
            tester.RelaySubStep(((d.rla_enable, True), ), delay=0.5),
            tester.RelaySubStep(((d.rla_enTec, True), ), delay=0.5),
            tester.DcSubStep(setting=((d.dcs_tecvset, 0.0), ), output=True),
            tester.MeasureSubStep((m.dmm_tecVmon0V, m.dmm_tec0V,), timeout=5),
            tester.DcSubStep(setting=((d.dcs_tecvset, 2.5), )),
            tester.MeasureSubStep((m.dmm_tecVmon2V5, m.dmm_tec2V5,),timeout=5),
            tester.DcSubStep(setting=((d.dcs_tecvset, 5.0), )),
            tester.MeasureSubStep((m.dmm_tecVmon5V, m.dmm_tec5V,), timeout=5),
            ))
        # TecReverse: Reverse, measure
        self.tec_rv = tester.SubStep((
            tester.RelaySubStep(((d.rla_tecphase, False), )),
            tester.MeasureSubStep(
                        (m.dmm_tecVmon5V, m.dmm_tec5Vrev, ), timeout=5),
            tester.RelaySubStep(((d.rla_tecphase, True), )),
            tester.MeasureSubStep((m.dmm_tecVmon5V, m.dmm_tec5V,), timeout=5),
            ))
        # LddEnable: Enable, set, measure
        self.ldd_en = tester.SubStep((
            tester.RelaySubStep(((d.rla_interlock, True), (d.rla_enIs, True),
                    (d.rla_lddcrowbar, True), (d.rla_lddtest, True), )),
            tester.DcSubStep(setting=((d.dcs_lddiset, 0.0), ), output=True),
            tester.MeasureSubStep(
                (m.dmm_ldd0V, m.dmm_ISIout0A, m.dmm_lddImon0V,), timeout=5),
            tester.DcSubStep(setting=((d.dcs_lddiset, 0.6), )),
            tester.MeasureSubStep(
                (m.dmm_ldd0V6, m.dmm_ISIout6A, m.dmm_lddImon0V6,),timeout=5),
            tester.DcSubStep(setting=((d.dcs_lddiset, 5.0), )),
            tester.MeasureSubStep(
                (m.dmm_ldd5V, m.dmm_ISIout50A, m.dmm_lddImon5V,), timeout=5),
            tester.DcSubStep(setting=((d.dcs_lddiset, 0.0), )),
            ))
