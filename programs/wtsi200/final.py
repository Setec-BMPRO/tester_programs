#!/usr/bin/e nv python3
"""WTSI200 Final Test Program."""

import time
from pydispatch import dispatcher
import tester

LIMITS = tester.testlimit.limitset((
    ('T1level1', 1, 3.0, 3.5, None, None),
    ('T2level1', 1, 3.0, 3.5, None, None),
    ('T3level1', 1, 3.0, 3.5, None, None),
    ('level1', 1, 3.0, 3.5, None, None),
    ('level2', 1, 2.33, 2.58, None, None),
    ('level3', 1, 1.62, 1.79, None, None),
    ('level4', 1, 0.0, 0.5, None, None),
    ('Notify', 2, None, None, None, True),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Final(tester.TestSequence):

    """WTSI200 Final Test Program."""

    def open(self):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerOn', self._step_power_on),
            tester.TestStep('Tank1', self._step_tank1),
            tester.TestStep('Tank2', self._step_tank2),
            tester.TestStep('Tank3', self._step_tank3),
            )
        self._limits = LIMITS
        global m, d, s, t
        d = LogicalDevices(self.physical_devices)
        s = Sensors(d)
        m = Measurements(s, self._limits)
        t = SubTests(d, m)

    def close(self):
        """Finished testing."""
        global m, d, s, t
        m = d = s = t = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _step_power_on(self):
        """Power up with 12V and measure level1 for all tanks."""
        self.fifo_push(((s.oTankLevels, ((3.25, 3.25, 3.25),)), ))

        t.pwr_on.run()

    def _step_tank1(self):
        """Vary levels for tank1 and measure."""
        self.fifo_push(
            ((s.oTankLevels,
             ((2.4, 3.25, 3.25), (1.7, 3.25, 3.25), (0.25, 3.25, 3.25),)), ))

        t.tank1.run()

    def _step_tank2(self):
        """Vary levels for tank2 and measure."""
        self.fifo_push(
            ((s.oTankLevels,
             ((3.25, 2.4, 3.25), (3.25, 1.7, 3.25), (3.25, 0.25, 3.25),)), ))

        t.tank2.run()

    def _step_tank3(self):
        """Vary levels for tank3 and measure."""
        self.fifo_push(
            ((s.oTankLevels,
             ((3.25, 3.25, 2.4), (3.25, 3.25, 1.7), (3.25, 3.25, 0.25),)), ))

        t.tank3.run()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments."""
        self.dso = tester.DSO(devices['DSO'])
        self.dcs_12V = tester.DCSource(devices['DCS1'])
        self.dcs_3V3 = tester.DCSource(devices['DCS2'])
        self.rla_tank1S3 = tester.Relay(devices['RLA1'])
        self.rla_tank1S2 = tester.Relay(devices['RLA2'])
        self.rla_tank1S1 = tester.Relay(devices['RLA3'])
        self.rla_tank2S3 = tester.Relay(devices['RLA4'])
        self.rla_tank2S2 = tester.Relay(devices['RLA5'])
        self.rla_tank2S1 = tester.Relay(devices['RLA6'])
        self.rla_tank3S3 = tester.Relay(devices['RLA7'])
        self.rla_tank3S2 = tester.Relay(devices['RLA8'])
        self.rla_tank3S1 = tester.Relay(devices['RLA9'])
        self.rla_trigg = tester.Relay(devices['RLA10'])
        self._all_relays = (
            self.rla_tank1S3, self.rla_tank1S2, self.rla_tank1S1,
            self.rla_tank2S3, self.rla_tank2S2, self.rla_tank2S1,
            self.rla_tank3S3, self.rla_tank3S2, self.rla_tank3S1,
            self.rla_trigg)

    def reset(self):
        """Reset instruments."""
        for dcs in (self.dcs_12V, self.dcs_3V3):
            dcs.output(0.0, False)
        for rla in self._all_relays:
            rla.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances."""
        dso = logical_devices.dso
        sensor = tester.sensor
        tbase = sensor.Timebase(
            range=0.20, main_mode=True, delay=0, centre_ref=False)
        trg = sensor.Trigger(
            ch=4, level=1.0, normal_mode=True, pos_slope=True)
        rdgs = ()
        for ch in range(1, 4):
            rdgs += (sensor.Vtim(ch=ch, time_point=0.06), )
        chans = ()
        for ch in range(1, 5):
            chans += (sensor.Channel(
                ch=ch, mux=1, range=4.0, offset=(1.5 + ch * 0.1),
                dc_coupling=True, att=1, bwlim=True), )
        self.oTankLevels = sensor.DSO(
            dso, chans, tbase, trg, rdgs, single=True)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances."""
        Measurement = tester.Measurement
        lims = {
            'tankL1': (
                limits['T1level1'], limits['T2level1'], limits['T3level1']),
            'tank1L2': (
                limits['level2'], limits['level1'], limits['level1']),
            'tank1L3': (
                limits['level3'], limits['level1'], limits['level1']),
            'tank1L4': (
                limits['level4'], limits['level1'], limits['level1']),
            'tank2L2': (
                limits['level1'], limits['level2'], limits['level1']),
            'tank2L3': (
                limits['level1'], limits['level3'], limits['level1']),
            'tank2L4': (
                limits['level1'], limits['level4'], limits['level1']),
            'tank3L2': (
                limits['level1'], limits['level1'], limits['level2']),
            'tank3L3': (
                limits['level1'], limits['level1'], limits['level3']),
            'tank3L4': (
                limits['level1'], limits['level1'], limits['level4'])
            }
        self.dso_TankLevel1 = Measurement(
            lims['tankL1'], sense.oTankLevels)
        self.dso_Tank1Level2 = Measurement(
            lims['tank1L2'], sense.oTankLevels, autoconfig=False)
        self.dso_Tank1Level3 = Measurement(
            lims['tank1L3'], sense.oTankLevels, autoconfig=False)
        self.dso_Tank1Level4 = Measurement(
            lims['tank1L4'], sense.oTankLevels, autoconfig=False)
        self.dso_Tank2Level2 = Measurement(
            lims['tank2L2'], sense.oTankLevels, autoconfig=False)
        self.dso_Tank2Level3 = Measurement(
            lims['tank2L3'], sense.oTankLevels, autoconfig=False)
        self.dso_Tank2Level4 = Measurement(
            lims['tank2L4'], sense.oTankLevels, autoconfig=False)
        self.dso_Tank3Level2 = Measurement(
            lims['tank3L2'], sense.oTankLevels, autoconfig=False)
        self.dso_Tank3Level3 = Measurement(
            lims['tank3L3'], sense.oTankLevels, autoconfig=False)
        self.dso_Tank3Level4 = Measurement(
            lims['tank3L4'], sense.oTankLevels, autoconfig=False)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances."""
        d = logical_devices
        self.d = d
        m = measurements
        dispatcher.connect(
            self.dso_trigger,
            sender=m.dso_TankLevel1.sensor,
            signal=tester.SigDso)
        # PowerOn: Apply 12Vdc, measure.
        dcs = tester.DcSubStep(
            setting=((d.dcs_12V, 12.0), (d.dcs_3V3, 3.3), ),
            output=True, delay=1)
        msr = tester.MeasureSubStep((m.dso_TankLevel1, ))
        self.pwr_on = tester.SubStep((dcs, msr, ))
        # Tank1: Vary levels, measure.
        rly1 = tester.RelaySubStep(((d.rla_tank1S3, True), ))
        msr1 = tester.MeasureSubStep((m.dso_Tank1Level2, ))
        rly2 = tester.RelaySubStep(((d.rla_tank1S2, True), ))
        msr2 = tester.MeasureSubStep((m.dso_Tank1Level3, ))
        rly3 = tester.RelaySubStep(((d.rla_tank1S1, True), ))
        msr3 = tester.MeasureSubStep((m.dso_Tank1Level4, ))
        rly4 = tester.RelaySubStep(
            ((d.rla_tank1S3, False), (d.rla_tank1S2, False),
             (d.rla_tank1S1, False)))
        self.tank1 = tester.SubStep((rly1, msr1, rly2, msr2, rly3, msr3, rly4))
        # Tank2: Vary levels, measure.
        rly1 = tester.RelaySubStep(((d.rla_tank2S3, True), ))
        msr1 = tester.MeasureSubStep((m.dso_Tank2Level2, ))
        rly2 = tester.RelaySubStep(((d.rla_tank2S2, True), ))
        msr2 = tester.MeasureSubStep((m.dso_Tank2Level3, ))
        rly3 = tester.RelaySubStep(((d.rla_tank2S1, True), ))
        msr3 = tester.MeasureSubStep((m.dso_Tank2Level4, ))
        rly4 = tester.RelaySubStep(
            ((d.rla_tank2S3, False), (d.rla_tank2S2, False),
             (d.rla_tank2S1, False)))
        self.tank2 = tester.SubStep((rly1, msr1, rly2, msr2, rly3, msr3, rly4))
        # Tank3: Vary levels, measure.
        rly1 = tester.RelaySubStep(((d.rla_tank3S3, True), ))
        msr1 = tester.MeasureSubStep((m.dso_Tank3Level2, ))
        rly2 = tester.RelaySubStep(((d.rla_tank3S2, True), ))
        msr2 = tester.MeasureSubStep((m.dso_Tank3Level3, ))
        rly3 = tester.RelaySubStep(((d.rla_tank3S1, True), ))
        msr3 = tester.MeasureSubStep((m.dso_Tank3Level4, ))
        rly4 = tester.RelaySubStep(
            ((d.rla_tank3S3, False), (d.rla_tank3S2, False),
             (d.rla_tank3S1, False)))
        self.tank3 = tester.SubStep((rly1, msr1, rly2, msr2, rly3, msr3, rly4))

    def dso_trigger(self):
        """DSO Ready handler."""
        self.d.rla_trigg.set_on()
        time.sleep(0.25)
        self.d.rla_trigg.set_off()
