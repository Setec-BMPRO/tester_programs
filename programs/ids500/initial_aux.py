#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Aux Initial Test Program."""

import time
import tester


# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class InitialAux(tester.TestSequence):

    """IDS-500 Initial Aux Test Program."""

    # Test limits
    limitdata = tester.testlimit.limitset((
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

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerUp', self._step_pwrup),
            tester.TestStep('KeySwitch', self._step_key_switches12),
            tester.TestStep('ACurrent', self._step_acurrent),
            tester.TestStep('OCP', self._step_ocp),
            )
        self._limits = self.limitdata
        global d, m, s, t
        d = LogicalDevAux(self.physical_devices, self.fifo)
        s = SensorAux(d, self._limits)
        m = MeasureAux(s, self._limits)
        t = SubTestAux(d, m)

    def close(self):
        """Finished testing."""
        global m, d, s, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _step_pwrup(self):
        """Check Fixture Lock, power up internal IDS-500 for 20VL, -20V rails."""
#        self.fifo_push(
#            ((s.olock, 0.0), (s.o20VL, 21.0), (s.o_20V, -21.0), (s.o5V, 0.0),
#             (s.o15V, 15.0), (s.o_15V, -15.0), (s.o15Vp, 0.0),
#             (s.o15VpSw, 0.0), (s.oPwrGood, 0.0), ))
        t.pwrup.run()

    def _step_key_switches12(self):
        """Apply 5V to ENABLE_Aux, ENABLE +15VPSW and measure voltages."""
#        self.fifo_push(
#            ((s.o5V, 5.0), (s.o15V, 15.0), (s.o_15V, -15.0), (s.o15Vp, 15.0),
#             (s.o15VpSw, (0.0, 15.0)), (s.oPwrGood, 5.0), ))
        t.key_sws.run()

    def _step_acurrent(self):
        """Test ACurrent: No load, 5V load, 5V load + 15Vp load """
#        self.fifo_push(
#            ((s.oACurr5V, (0.0, 2.0, 2.0)), (s.oACurr15V, (0.1, 0.1, 1.3)), ))
        t.acurr.run()

    def _step_ocp(self):
        """Measure OCP and voltage a/c R657 with 5V applied via a 100k."""
#        self.fifo_push(
#            ((s.o5V, (5.0, ) * 20 + (4.7, ), ),
#             (s.o15Vp, (15.0, ) * 30 + (14.1, ), ), (s.oAuxTemp, 3.5)))
        t.ocp.run()


class LogicalDevAux():

    """Aux Devices."""

    def __init__(self, devices, fifo):
        """Create all Instruments.

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
        self.acsource.reset()
        time.sleep(2)
        self.discharge.pulse()
        for dcs in (self.dcs_5Vfix, self.dcs_fan, ):
            dcs.output(0.0, False)
        for dcl in (self.dcl_5V, self.dcl_15Vp, ):
            dcl.output(0.0, False)
        for rla in (self.rla_enAux, self.rla_en15Vpsw, ):
            rla.set_off()


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
