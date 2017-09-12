#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 SynBuck Initial Test Program."""

import os
import inspect
import time
import tester
import share


# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class InitialSyn(tester.TestSequence):

    """IDS-500 Initial SynBuck Test Program."""

    # Firmware image
    pic_hex_syn = 'ids_picSyn_2.hex'
    # Test limits
    limitdata = tester.testlimit.limitset((
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
        self._limits = self.limitdata
        global d, m, s, t
        d = LogicalDevSyn(self.physical_devices, self.fifo)
        s = SensorSyn(d, self._limits)
        m = MeasureSyn(s, self._limits)
        t = SubTestSyn(d, m)

    def close(self):
        """Finished testing."""
        global m, d, s, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _step_program(self):
        """Check Fixture Lock, apply Vcc and program the board."""
#        self.fifo_push(((s.olock, 0.0), ))
        m.dmm_lock.measure(timeout=5)
        d.dcs_vsec5Vlddtec.output(5.0, True)
        d.program_picSyn.program()

    def _step_pwrup(self):
        """Power up internal IDS-500 for 20VT,-20V, 9V rails and measure."""
#        self.fifo_push(
#            ((s.o20VT, 20.0), (s.o_20V, -20.0), (s.o9V, 11.0), (s.oTec, 0.0),
#            (s.oLdd, 0.0), (s.oLddVmon, 0.0), (s.oLddImon, 0.0),
#            (s.oTecVmon, 0.0), (s.oTecVset, 0.0), ))
        t.pwrup.run()

    def _step_tec_enable(self):
        """Enable TEC, set dc input and measure voltages."""
#        self.fifo_push(
#            ((s.oTecVmon, (0.5, 2.5, 5.0)), (s.oTec, (0.5, 7.5, 15.0)), ))
        t.tec_en.run()

    def _step_tec_rev(self):
        """Reverse TEC and measure voltages."""
#        self.fifo_push(((s.oTecVmon, (5.0,) * 2), (s.oTec, (-15.0, 15.0)), ))
        t.tec_rv.run()

    def _step_ldd_enable(self):
        """Enable LDD, set dc input and measure voltages."""
#        self.fifo_push(
#            ((s.oLdd, (0.0, 0.65, 1.3)), (s.oLddShunt, (0.0, 0.006, 0.05)),
#            (s.oLddImon, (0.0, 0.6, 5.0)), ))
        t.ldd_en.run()

    def _step_ISset_adj(self):
        """ISset adjustment.

         Set LDD current to 50A.
         Calculate adjustment limits from measured current setting.
         Adjust pot R489 for accuracy of LDD output current.
         Measure LDD output current with calculated limits.
         For FIFO testing, add delay to Adj sensor and make NoDelays False.

         """
#        self.fifo_push(
#            ((s.oLddIset, 5.01), (s.oAdjLdd, True),
#             (s.oLddShunt, (0.0495, 0.0495, 0.05005)), ))
        d.dcs_lddiset.output(5.0, True)
        setI = m.dmm_ISIset5V.measure(timeout=5).reading1 * 10
        lo_lim = setI - (setI * 0.2/100)
        hi_lim = setI + (setI * 0.2/100)
        self._limits['AdjLimits'].limit = lo_lim, hi_lim
        s.oAdjLdd.low, s.oAdjLdd.high = lo_lim, hi_lim
        tester.MeasureGroup((m.ui_AdjLdd, m.dmm_ISIoutPost, ), timeout=2)


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
            InitialSyn.pic_hex_syn, folder, '18F4321', self.rla_syn)

    def reset(self):
        """Reset instruments."""
        self.acsource.reset()
        time.sleep(2)
        self.discharge.pulse()
        for dcs in (self.dcs_vsec5Vlddtec, self.dcs_lddiset, self.dcs_tecvset,
                    self.dcs_fan):
            dcs.output(0.0, False)
        for rla in (self.rla_enTec, self.rla_enIs, self.rla_lddcrowbar,
                    self.rla_interlock, self.rla_lddtest, self.rla_tecphase,
                    self.rla_enable, self.rla_syn):
            rla.set_off()


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
