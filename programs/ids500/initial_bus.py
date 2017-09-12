#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDS-500 Bus Initial Test Program."""

import time
import tester


# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class InitialBus(tester.TestSequence):

    """IDS-500 Initial Bus Test Program."""

    # Test limits
    limitdata = tester.testlimit.limitset((
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

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerUp', self._step_pwrup),
            tester.TestStep('TecLddStartup', self._step_tec_ldd),
            )
        self._limits = self.limitdata
        global d, m, s, t
        d = LogicalDevBus(self.physical_devices, self.fifo)
        s = SensorBus(d, self._limits)
        m = MeasureBus(s, self._limits)
        t = SubTestBus(d, m)

    def close(self):
        """Finished testing."""
        global m, d, s, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _step_pwrup(self):
        """Check Fixture Lock, power up internal IDS-500 for 400V rail."""
#        self.fifo_push(((s.olock, 0.0), (s.o400V, 400.0), ))
        t.pwrup.run()

    def _step_tec_ldd(self):
        """ """
#        self.fifo_push(
#            ((s.o20VT, (23, 23, 22, 19)), (s.o9V, (11, 10, 10, 11 )),
#             (s.o20VL, (23, 23, 21, 23)), (s.o_20V, (-23, -23, -21, -23)),))
        t.tl_startup.run()


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
        self.acsource.reset()
        time.sleep(2)
        self.discharge.pulse()
        for dcs in (self.dcs_prictl, self.dcs_fan, ):
            dcs.output(0.0, False)
        for dcl in (self.dcl_20VT, self.dcl_9V, self.dcl_20VL, self.dcl__20):
            dcl.output(0.0, False)
        for rla in (self.rla_enT, self.rla_enBC9, self.rla_enL,
                    self.rla_enBC20):
            rla.set_off()

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
