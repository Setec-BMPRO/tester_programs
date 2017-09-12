#!/usr/bin/e nv python3
"""WTSI200 Final Test Program."""

from pydispatch import dispatcher
import tester
from tester import TestStep, LimitBetween
import share


class Final(share.TestSequence):

    """WTSI200 Final Test Program."""

    limitdata = (
        LimitBetween('T1level1', 3.0, 3.5),
        LimitBetween('T2level1', 3.0, 3.5),
        LimitBetween('T3level1', 3.0, 3.5),
        LimitBetween('level1', 3.0, 3.5),
        LimitBetween('level2', 2.33, 2.58),
        LimitBetween('level3', 1.62, 1.79),
        LimitBetween('level4', 0.0, 0.5),
        )

    def open(self):
        """Create the test program as a linear sequence."""
        super().open(self.limitdata, LogicalDevices, Sensors, Measurements)
        self.steps = (
            TestStep('PowerOn', self._step_power_on),
            TestStep('Tank1', self._step_tank1),
            TestStep('Tank2', self._step_tank2),
            TestStep('Tank3', self._step_tank3),
            )

    @share.teststep
    def _step_power_on(self, dev, mes):
        """Power up with 12V and measure level1 for all tanks."""
        self.dcsource(
            (('dcs_12V', 12.0), ('dcs_3V3', 3.3), ), output=True, delay=1)
        mes['dso_TankLevel1']()

    @share.teststep
    def _step_tank1(self, dev, mes):
        """Vary levels for tank1 and measure."""
        dev['rla_tank1S3'].set_on()
        mes['dso_Tank1Level2']()
        dev['rla_tank1S2'].set_on()
        mes['dso_Tank1Level3']()
        dev['rla_tank1S1'].set_on()
        mes['dso_Tank1Level4']()
        self.relay(
            (('rla_tank1S3', False), ('rla_tank1S2', False),
             ('rla_tank1S1', False)))

    @share.teststep
    def _step_tank2(self, dev, mes):
        """Vary levels for tank2 and measure."""
        dev['rla_tank2S3'].set_on()
        mes['dso_Tank2Level2']()
        dev['rla_tank2S2'].set_on()
        mes['dso_Tank2Level3']()
        dev['rla_tank2S1'].set_on()
        mes['dso_Tank2Level4']()
        self.relay(
            (('rla_tank2S3', False), ('rla_tank2S2', False),
             ('rla_tank2S1', False)))

    @share.teststep
    def _step_tank3(self, dev, mes):
        """Vary levels for tank3 and measure."""
        dev['rla_tank3S3'].set_on()
        mes['dso_Tank3Level2']()
        dev['rla_tank3S2'].set_on()
        mes['dso_Tank3Level3']()
        dev['rla_tank3S1'].set_on()
        mes['dso_Tank3Level4']()
        self.relay(
            (('rla_tank3S3', False), ('rla_tank3S2', False),
             ('rla_tank3S1', False)))


class LogicalDevices(share.LogicalDevices):

    """Logical Devices."""

    def open(self):
        """Create all Logical Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dso', tester.DSO, 'DSO'),
                ('dcs_3V3', tester.DCSource, 'DCS2'),
                ('dcs_12V', tester.DCSource, 'DCS3'),
                ('rla_tank1S3', tester.Relay, 'RLA1'),
                ('rla_tank1S2', tester.Relay, 'RLA2'),
                ('rla_tank1S1', tester.Relay, 'RLA3'),
                ('rla_tank2S3', tester.Relay, 'RLA4'),
                ('rla_tank2S2', tester.Relay, 'RLA5'),
                ('rla_tank2S1', tester.Relay, 'RLA6'),
                ('rla_tank3S3', tester.Relay, 'RLA7'),
                ('rla_tank3S2', tester.Relay, 'RLA8'),
                ('rla_tank3S1', tester.Relay, 'RLA9'),
                ('rla_trigg', tester.Relay, 'RLA10'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        for dcs in ('dcs_12V', 'dcs_3V3'):
            self[dcs].output(0.0, False)
        for rla in (
                'rla_tank1S3', 'rla_tank1S2', 'rla_tank1S1',
                'rla_tank2S3', 'rla_tank2S2', 'rla_tank2S1',
                'rla_tank3S3', 'rla_tank3S2', 'rla_tank3S1',
                'rla_trigg',
                ):
            self[rla].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dso = self.devices['dso']
        sensor = tester.sensor
        tbase = sensor.Timebase(
            range=0.20, main_mode=True, delay=0, centre_ref=False)
        trg = sensor.Trigger(
            ch=4, level=1.0, normal_mode=True, pos_slope=True)
        rdgs = []
        for ch in range(1, 4):
            rdgs.append(sensor.Vtim(ch=ch, time_point=0.06))
        chans = []
        for ch in range(1, 5):
            chans.append(
                sensor.Channel(
                    ch=ch, mux=1, range=4.0, offset=(1.5 + ch * 0.1),
                    dc_coupling=True, att=1, bwlim=True))
        self['oTankLevels'] = sensor.DSO(
            dso, chans, tbase, trg, rdgs, single=True)
        dispatcher.connect(
            self.dso_trigger, sender=self['oTankLevels'], signal=tester.SigDso)

    def dso_trigger(self):
        """DSO Ready handler."""
        self.devices['rla_trigg'].pulse_on(duration=0.25)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        mes = tester.Measurement
        lim = self.limits
        lims = {
            'tankL1': (lim['T1level1'], lim['T2level1'], lim['T3level1']),
            'tank1L2': (lim['level2'], lim['level1'], lim['level1']),
            'tank1L3': (lim['level3'], lim['level1'], lim['level1']),
            'tank1L4': (lim['level4'], lim['level1'], lim['level1']),
            'tank2L2': (lim['level1'], lim['level2'], lim['level1']),
            'tank2L3': (lim['level1'], lim['level3'], lim['level1']),
            'tank2L4': (lim['level1'], lim['level4'], lim['level1']),
            'tank3L2': (lim['level1'], lim['level1'], lim['level2']),
            'tank3L3': (lim['level1'], lim['level1'], lim['level3']),
            'tank3L4': (lim['level1'], lim['level1'], lim['level4'])
            }
        sen = self.sensors['oTankLevels']
        self['dso_TankLevel1'] = mes(lims['tankL1'], sen)
        self['dso_Tank1Level2'] = mes(lims['tank1L2'], sen, autoconfig=False)
        self['dso_Tank1Level3'] = mes(lims['tank1L3'], sen, autoconfig=False)
        self['dso_Tank1Level4'] = mes(lims['tank1L4'], sen, autoconfig=False)
        self['dso_Tank2Level2'] = mes(lims['tank2L2'], sen, autoconfig=False)
        self['dso_Tank2Level3'] = mes(lims['tank2L3'], sen, autoconfig=False)
        self['dso_Tank2Level4'] = mes(lims['tank2L4'], sen, autoconfig=False)
        self['dso_Tank3Level2'] = mes(lims['tank3L2'], sen, autoconfig=False)
        self['dso_Tank3Level3'] = mes(lims['tank3L3'], sen, autoconfig=False)
        self['dso_Tank3Level4'] = mes(lims['tank3L4'], sen, autoconfig=False)
