#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Initial Subboard Test Program."""

import os
import inspect
import time
import tester
import share
from . import console

# Serial port for the PIC.
PIC_PORT = {'posix': '/dev/ttyUSB0', 'nt': 'COM16'}[os.name]

PIC_HEX_MIC = 'ids_picMic_2.hex'
PIC_HEX_SYN = 'ids_picSyn_2.hex'

LIMITS_MIC = tester.testlimit.limitset((
    ('5V', 1, 4.95, 5.05, None, None),
    ('SwRev', 1, None, None, r'2', None),
    ('MicroTemp', 1, None, None, r'MICRO Temp', None),
    ))

LIMITS_AUX = tester.testlimit.limitset((
    ('5V', 1, 4.90, 5.10, None, None),
    ('5VOff', 1, 0.5, None, None, None),
    ('15VpOff', 1, 0.5, None, None, None),
    ('15Vp', 1, 14.25, 15.75, None, None),
    ('15VpSwOff', 1, 0.5, None, None, None),
    ('15VpSw', 1, 14.25, 15.75, None, None),
    ('20VL', 1, 18.0, 25.0, None, None),
    ('-20V', 1, -25.0, -18.0, None, None),
    ('15V', 1, 14.25, 15.75, None, None),
    ('-15V', 1, -15.75, -14.25, None, None),
    ('PwrGoodOff', 1, 0.5, None, None, None),
    ('PwrGood', 1, 4.8, 5.1, None, None),
    ('ACurr_5V_1', 1, -0.1, 0.1, None, None),
    ('ACurr_5V_2', 1, 1.76, 2.15, None, None),
    ('ACurr_15V_1', 1, -0.1, 0.13, None, None),
    ('ACurr_15V_2', 1, 1.16, 1.42, None, None),
    ('AuxTemp', 1, 2.1, 4.3, None, None),
    ('InOCP5V', 1, 4.8, None, None, None),
    ('InOCP15Vp', 1, 14.2, None, None, None),
    ('OCP', 1, 7.0, 10.0, None, None),
    ('FixtureLock', 0, 20, None, None, None),
    ))

LIMITS_BIAS = tester.testlimit.limitset((
    ('400V', 1, 390, 410, None, None),
    ('PVcc', 1, 12.8, 14.5, None, None),
    ('12VsbRaw', 1, 12.7, 13.49, None, None),
    ('OCP Trip', 1, 12.6, None, None, None),
    ('InOCP', 1, 12.6, None, None, None),
    ('OCP', 1, 1.2, 2.1, None, None),
    ('FixtureLock', 0, 20, None, None, None),
    ))

LIMITS_BUS = tester.testlimit.limitset((
    ('400V', 1, 390, 410, None, None),
    ('20VT_load0_out', 1, 22.0, 24.0, None, None),
    ('9V_load0_out', 1, 10.8, 12.0, None, None),
    ('20VL_load0_out', 1, 22.0, 24.0, None, None),
    ('-20V_load0_out', 1, -25.0, -22.0, None, None),
    ('20VT_load1_out', 1, 22.0, 25.0, None, None),
    ('9V_load1_out', 1, 9.0, 11.0, None, None),
    ('20VL_load1_out', 1, 22.0, 25.0, None, None),
    ('-20V_load1_out', 1, -26.0, -22.0, None, None),
    ('20VT_load2_out', 1, 19.0, 24.0, None, None),
    ('9V_load2_out', 1, 9.0, 11.0, None, None),
    ('20VL_load2_out', 1, 19.0, 21.5, None, None),
    ('-20V_load2_out', 1, -22.2, -20.0, None, None),
    ('20VT_load3_out', 1, 17.5, 20.0, None, None),
    ('9V_load3_out', 1, 9.0, 12.0, None, None),
    ('20VL_load3_out', 1, 22.0, 24.0, None, None),
    ('-20V_load3_out', 1, -26.0, -22.0, None, None),
    ('FixtureLock', 0, 20, None, None, None),
    ))

LIMITS_SYN = tester.testlimit.limitset((
    ('20VT', 1, 18.5, 22.0, None, None),
    ('-20V', 1, -22.0, -18.0, None, None),
    ('9V', 1, 8.0, 11.5, None, None),
    ('TecOff', 1, -0.5, 0.5, None, None),
    ('Tec0V', 1, -0.5, 1.0, None, None),
    ('Tec2V5', 1, 7.3, 7.8, None, None),
    ('Tec5V', 1, 14.75, 15.5, None, None),
    ('Tec5V_Rev', 1, -15.5, -14.5, None, None),
    ('LddOff', 1, -0.5, 0.5, None, None),
    ('Ldd0V', 1, -0.5, 0.5, None, None),
    ('Ldd0V6', 1, 0.6, 1.8, None, None),
    ('Ldd5V', 1, 1.0, 2.5, None, None),
    ('LddVmonOff', 1, -0.5, 0.5, None, None),
    ('LddImonOff', 1, -0.5, 0.5, None, None),
    ('LddImon0V', 1, -0.05, 0.05, None, None),
    ('LddImon0V6', 1, 0.55, 0.65, None, None),
    ('LddImon5V', 1, 4.9, 5.1, None, None),
    ('ISIout0A', 1, -1.0, 1.0, None, None),
    ('ISIout6A', 1, 5.0, 7.0, None, None),
    ('ISIout50A', 1, 49.0, 51.0, None, None),
    ('ISIset5V', 1, 4.95, 5.05, None, None),
    ('AdjLimits', 1, 49.9, 50.1, None, None),
    ('TecVmonOff', 1, -0.5, 0.5, None, None),
    ('TecVmon0V', 1, -0.5, 0.8, None, None),
    ('TecVmon2V5', 1, 2.4375, 2.5625, None, None),
    ('TecVmon5V', 1, 4.925, 5.075, None, None),
    ('TecVsetOff', 1, -0.5, 0.5, None, None),
    ('FixtureLock', 0, 20, None, None, None),
    ('Notify', 2, None, None, None, True),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class _Main(tester.TestSequence):

    """IDS-500 Base Subboard Test Program."""

    def close(self):
        """Finished testing."""
        global m, d, s, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()


class InitialMicro(_Main):

    """IDS-500 Initial Micro Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('Program', self._step_program, not self.fifo),
            tester.TestStep('Comms', self._step_comms),
            )
        self._limits = LIMITS_MIC
        global d, m, s
        d = LogicalDevMicro(self.physical_devices, self.fifo)
        s = SensorMicro(d, self._limits)
        m = MeasureMicro(s, self._limits)
        d.rla_comm.set_on()

    def close(self):
        """Finished testing."""
        d.rla_comm.set_off()
        super().close()

    def _step_program(self):
        """Apply Vcc and program the board."""
        self.fifo_push(((s.oVsec5VuP, 5.0), ))

        d.dcs_vcc.output(5.0, True)
        m.dmm_vsec5VuP.measure(timeout=5)
        d.program_picMic.program()

    def _step_comms(self):
        """Communicate with the PIC console."""
        for str in (
                ('', ) +
                ('M,1,Incorrectformat!Type?.?forhelp', ) +
                ('M,3,UnknownCommand!Type?.?forhelp', ) +
                ('2', ) +
                ('MICRO Temp', )
                ):
            d.pic.puts(str)

        d.pic.open()
        d.pic.clear_port()
        d.pic.exp_cnt = 1
        tester.MeasureGroup((m.swrev, m.microtemp, ))


class InitialAux(_Main):

    """IDS-500 Initial Aux Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerUp', self._step_pwrup),
            tester.TestStep('KeySwitch', self._step_key_switches12),
            tester.TestStep('ACurrent', self._step_acurrent),
            tester.TestStep('OCP', self._step_ocp),
            )
        self._limits = LIMITS_AUX
        global d, m, s, t
        d = LogicalDevAux(self.physical_devices, self.fifo)
        s = SensorAux(d, self._limits)
        m = MeasureAux(s, self._limits)
        t = SubTestAux(d, m)

    def close(self):
        """Finished testing."""
        super().close()

    def _step_pwrup(self):
        """Check Fixture Lock, power up internal IDS-500 for 20VL, -20V rails."""
        self.fifo_push(
            ((s.olock, 0.0), (s.o20VL, 21.0), (s.o_20V, -21.0), (s.o5V, 0.0),
             (s.o15V, 15.0), (s.o_15V, -15.0), (s.o15Vp, 0.0),
             (s.o15VpSw, 0.0), (s.oPwrGood, 0.0), ))

        t.pwrup.run()

    def _step_key_switches12(self):
        """Apply 5V to ENABLE_Aux, ENABLE +15VPSW and measure voltages."""
        self.fifo_push(
            ((s.o5V, 5.0), (s.o15V, 15.0), (s.o_15V, -15.0), (s.o15Vp, 15.0),
             (s.o15VpSw, (0.0, 15.0)), (s.oPwrGood, 5.0), ))

        t.key_sws.run()

    def _step_acurrent(self):
        """Test ACurrent: No load, 5V load, 5V load + 15Vp load """
        self.fifo_push(
            ((s.oACurr5V, (0.0, 2.0, 2.0)), (s.oACurr15V, (0.1, 0.1, 1.3)), ))

        t.acurr.run()

    def _step_ocp(self):
        """Measure OCP and voltage a/c R657 with 5V applied via a 100k."""
        self.fifo_push(
            ((s.o5V, (5.0, ) * 20 + (4.7, ), ),
             (s.o15Vp, (15.0, ) * 30 + (14.1, ), ), (s.oAuxTemp, 3.5)))

        t.ocp.run()


class InitialBias(_Main):

    """IDS-500 Initial Bias Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerUp', self._step_pwrup),
            tester.TestStep('OCP', self._step_ocp),
            )
        self._limits = LIMITS_BIAS
        global d, m, s
        d = LogicalDevBias(self.physical_devices, self.fifo)
        s = SensorBias(d, self._limits)
        m = MeasureBias(s, self._limits)

    def close(self):
        """Finished testing."""
        super().close()

    def _step_pwrup(self):
        """Check Fixture Lock, power up internal IDS-500 for 400V rail."""
        self.fifo_push(((s.olock, 0.0), (s.o400V, 400.0), (s.oPVcc, 14.0), ))

        m.dmm_lock.measure(timeout=5)
        d.acsource.output(voltage=240.0, output=True)
        tester.MeasureGroup((m.dmm_400V, m.dmm_pvcc, ),timeout=5)

    def _step_ocp(self):
        """Measure OCP."""
        self.fifo_push(((s.o12Vsbraw, (13.0, ) * 4 + (12.5, 0.0), ), ))

        tester.MeasureGroup(
                (m.dmm_12Vsbraw, m.ramp_OCP, m.dmm_12Vsbraw2,),timeout=1)


class InitialBus(_Main):

    """IDS-500 Initial Bus Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerUp', self._step_pwrup),
            tester.TestStep('TecLddStartup', self._step_tec_ldd),
            )
        self._limits = LIMITS_BUS
        global d, m, s, t
        d = LogicalDevBus(self.physical_devices, self.fifo)
        s = SensorBus(d, self._limits)
        m = MeasureBus(s, self._limits)
        t = SubTestBus(d, m)

    def close(self):
        """Finished testing."""
        super().close()

    def _step_pwrup(self):
        """Check Fixture Lock, power up internal IDS-500 for 400V rail."""
        self.fifo_push(((s.olock, 0.0), (s.o400V, 400.0), ))

        t.pwrup.run()

    def _step_tec_ldd(self):
        """ """
        self.fifo_push(
            ((s.o20VT, (23, 23, 22, 19)), (s.o9V, (11, 10, 10, 11 )),
             (s.o20VL, (23, 23, 21, 23)), (s.o_20V, (-23, -23, -21, -23)),))

        t.tl_startup.run()


class InitialSyn(_Main):

    """IDS-500 Initial SynBuck Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('Program', self._step_program, not self.fifo),
            tester.TestStep('PowerUp', self._step_pwrup),
            tester.TestStep('TecEnable', self._step_tec_enable),
            tester.TestStep('TecReverse', self._step_tec_rev),
            tester.TestStep('LddEnable', self._step_ldd_enable),
            tester.TestStep('ISSetAdj', self._step_ISset_adj),
            )
        self._limits = LIMITS_SYN
        global d, m, s, t
        d = LogicalDevSyn(self.physical_devices, self.fifo)
        s = SensorSyn(d, self._limits)
        m = MeasureSyn(s, self._limits)
        t = SubTestSyn(d, m)

    def close(self):
        """Finished testing."""
        super().close()

    def _step_program(self):
        """Check Fixture Lock, apply Vcc and program the board."""
        self.fifo_push(((s.olock, 0.0), ))

        m.dmm_lock.measure(timeout=5)
        d.dcs_vsec5Vlddtec.output(5.0, True)
        d.program_picSyn.program()

    def _step_pwrup(self):
        """Power up internal IDS-500 for 20VT,-20V, 9V rails and measure."""
        self.fifo_push(
            ((s.o20VT, 20.0), (s.o_20V, -20.0), (s.o9V, 11.0), (s.oTec, 0.0),
            (s.oLdd, 0.0), (s.oLddVmon, 0.0), (s.oLddImon, 0.0),
            (s.oTecVmon, 0.0), (s.oTecVset, 0.0), ))

        t.pwrup.run()

    def _step_tec_enable(self):
        """Enable TEC, set dc input and measure voltages."""
        self.fifo_push(
            ((s.oTecVmon, (0.5, 2.5, 5.0)), (s.oTec, (0.5, 7.5, 15.0)), ))

        t.tec_en.run()

    def _step_tec_rev(self):
        """Reverse TEC and measure voltages."""
        self.fifo_push(((s.oTecVmon, (5.0,) * 2), (s.oTec, (-15.0, 15.0)), ))

        t.tec_rv.run()

    def _step_ldd_enable(self):
        """Enable LDD, set dc input and measure voltages."""
        self.fifo_push(
            ((s.oLdd, (0.0, 0.65, 1.3)), (s.oLddShunt, (0.0, 0.006, 0.05)),
            (s.oLddImon, (0.0, 0.6, 5.0)), ))

        t.ldd_en.run()

    def _step_ISset_adj(self):
        """ISset adjustment.

         Set LDD current to 50A.
         Calculate adjustment limits from measured current setting.
         Adjust pot R489 for accuracy of LDD output current.
         Measure LDD output current with calculated limits.
         For FIFO testing, add delay to Adj sensor and make NoDelays False.

         """

        self.fifo_push(
            ((s.oLddIset, 5.01), (s.oAdjLdd, True),
             (s.oLddShunt, (0.0495, 0.0495, 0.05005)), ))

        d.dcs_lddiset.output(5.0, True)
        setI = m.dmm_ISIset5V.measure(timeout=5).reading1 * 10
        lo_lim = setI - (setI * 0.2/100)
        hi_lim = setI + (setI * 0.2/100)
        self._limits['AdjLimits'].limit = lo_lim, hi_lim
        s.oAdjLdd.low, s.oAdjLdd.high = lo_lim, hi_lim
        tester.MeasureGroup((m.ui_AdjLdd, m.dmm_ISIoutPost, ), timeout=2)


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
        self.rla_comm = tester.Relay(devices['RLA13'])
        # PIC device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self.program_picMic = share.ProgramPIC(
            PIC_HEX_MIC, folder, '18F4520', self.rla_mic)
        # Serial connection to the console to communicate with the PIC
        pic_ser = tester.SimSerial(
            simulation=self._fifo, baudrate=19200, timeout=2.0)
        # Set port separately, as we don't want it opened yet
        pic_ser.port = PIC_PORT
        self.pic = console.Console(pic_ser)

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
        self.discharge = tester.Discharge(devices['DIS'])
        self.dcs_5Vfix = tester.DCSource(devices['DCS1'])
        self.dcs_fan = tester.DCSource(devices['DCS5'])
        self.dcl_5V = tester.DCLoad(devices['DCL1'])
        self.dcl_15Vp = tester.DCLoad(devices['DCL2'])
        self.rla_enAux = tester.Relay(devices['RLA1'])
        self.rla_en15Vpsw = tester.Relay(devices['RLA2'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        time.sleep(2)
        self.discharge.pulse()
        for dcs in (self.dcs_5Vfix, self.dcs_fan, ):
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
        self.discharge = tester.Discharge(devices['DIS'])
        self.dcs_fan = tester.DCSource(devices['DCS5'])
        self.dcl_12Vsbraw = tester.DCLoad(devices['DCL1'])

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        time.sleep(2)
        self.discharge.pulse()
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
        self.discharge = tester.Discharge(devices['DIS'])
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
        time.sleep(2)
        self.discharge.pulse()
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
        self.discharge = tester.Discharge(devices['DIS'])
        self.dcs_vsec5Vlddtec = tester.DCSource(devices['DCS1'])
        self.dcs_lddiset = tester.DCSource(devices['DCS2'])
        self.dcs_tecvset = tester.DCSource(devices['DCS3'])
        self.dcs_fan = tester.DCSource(devices['DCS5'])
        self.rla_enTec = tester.Relay(devices['RLA1'])
        self.rla_enIs = tester.Relay(devices['RLA2'])
        self.rla_lddcrowbar = tester.Relay(devices['RLA3'])
        self.rla_interlock = tester.Relay(devices['RLA4'])
        self.rla_lddtest = tester.Relay(devices['RLA5'])
        self.rla_tecphase = tester.Relay(devices['RLA6'])
        self.rla_enable = tester.Relay(devices['RLA12'])
        self.rla_syn = tester.Relay(devices['RLA7'])
        # PIC device programmer
        folder = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        self.program_picSyn = share.ProgramPIC(
            PIC_HEX_SYN, folder, '18F4321', self.rla_syn)

    def reset(self):
        """Reset instruments."""
        self.acsource.output(voltage=0.0, output=False)
        time.sleep(2)
        self.discharge.pulse()
        for dcs in (self.dcs_vsec5Vlddtec, self.dcs_lddiset, self.dcs_tecvset,
                    self.dcs_fan):
            dcs.output(0.0, False)
        for rla in (self.rla_enTec, self.rla_enIs, self.rla_lddcrowbar,
                    self.rla_interlock, self.rla_lddtest, self.rla_tecphase,
                    self.rla_enable, self.rla_syn):
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
        sensor = tester.sensor
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
        sensor = tester.sensor
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
        sensor = tester.sensor
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
        sensor = tester.sensor
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
        sensor = tester.sensor
        self.olock = sensor.Res(dmm, high=18, low=5, rng=10000, res=0.1)
        self.oTec = sensor.Vdc(dmm, high=15, low=3, rng=100, res=0.001)
        self.oTecVmon = sensor.Vdc(dmm, high=24, low=1, rng=10, res=0.001)
        self.oTecVset = sensor.Vdc(dmm, high=14, low=1, rng=10, res=0.001)
        self.oLdd = sensor.Vdc(dmm, high=21, low=1, rng=10, res=0.001)
        self.oLddVmon = sensor.Vdc(dmm, high=5, low=1, rng=10, res=0.001)
        self.oLddImon = sensor.Vdc(dmm, high=6, low=1, rng=10, res=0.001)
        self.oLddShunt = sensor.Vdc(
            dmm, high=8, low=4, rng=0.1, res=0.0001, scale=1000, nplc=10)
        self.o20VT = sensor.Vdc(dmm, high=10, low=1, rng=100, res=0.001)
        self.o9V = sensor.Vdc(dmm, high=12, low=1, rng=100, res=0.001)
        self.o_20V = sensor.Vdc(dmm, high=13, low=1, rng=100, res=0.001)
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
        self.swrev = Measurement(limits['SwRev'], sense.oSwRev)
        self.microtemp = Measurement(limits['MicroTemp'], sense.oMicroTemp)


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
                m.dmm_tecVsetOff), timeout=2),
            ))
        # TecEnable: Enable, set, measure
        self.tec_en = tester.SubStep((
            tester.RelaySubStep(((d.rla_tecphase, True), ), delay=0.5),
            tester.RelaySubStep(((d.rla_enable, True), ), delay=0.5),
            tester.RelaySubStep(((d.rla_enTec, True), ), delay=0.5),
            tester.DcSubStep(setting=((d.dcs_tecvset, 0.0), ), output=True),
            tester.MeasureSubStep((m.dmm_tecVmon0V, m.dmm_tec0V,), timeout=2),
            tester.DcSubStep(setting=((d.dcs_tecvset, 2.5), )),
            tester.MeasureSubStep((m.dmm_tecVmon2V5, m.dmm_tec2V5,),timeout=2),
            tester.DcSubStep(setting=((d.dcs_tecvset, 5.0), )),
            tester.MeasureSubStep((m.dmm_tecVmon5V, m.dmm_tec5V,), timeout=2),
            ))
        # TecReverse: Reverse, measure
        self.tec_rv = tester.SubStep((
            tester.RelaySubStep(((d.rla_tecphase, False), )),
            tester.MeasureSubStep(
                        (m.dmm_tecVmon5V, m.dmm_tec5Vrev, ), timeout=2),
            tester.RelaySubStep(((d.rla_tecphase, True), )),
            tester.MeasureSubStep((m.dmm_tecVmon5V, m.dmm_tec5V,), timeout=2),
            ))
        # LddEnable: Enable, set, measure
        self.ldd_en = tester.SubStep((
            tester.RelaySubStep(((d.rla_interlock, True), (d.rla_enIs, True),
                    (d.rla_lddcrowbar, True), (d.rla_lddtest, True), )),
            tester.DcSubStep(setting=((d.dcs_lddiset, 0.0), ), output=True),
            tester.MeasureSubStep(
                (m.dmm_ldd0V, m.dmm_ISIout0A, m.dmm_lddImon0V,), timeout=2),
            tester.DcSubStep(setting=((d.dcs_lddiset, 0.6), )),
            tester.MeasureSubStep(
                (m.dmm_ldd0V6, m.dmm_ISIout6A, m.dmm_lddImon0V6,),timeout=2),
            tester.DcSubStep(setting=((d.dcs_lddiset, 5.0), )),
            tester.MeasureSubStep(
                (m.dmm_ldd5V, m.dmm_ISIout50A, m.dmm_lddImon5V,), timeout=2),
            tester.DcSubStep(setting=((d.dcs_lddiset, 0.0), )),
            ))
