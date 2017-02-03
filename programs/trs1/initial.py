#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TRS1 Initial Test Program."""

import tester
from tester.testlimit import lim_hilo_delta, lim_boolean, lim_lo, lim_hi, lim_hilo

LOW_BATT_L = 10.85
LOW_BATT_U = 11.55

LIMITS = tester.testlimit.limitset((
    lim_lo('VinOff', 0.5),
    lim_hilo('Vin', 11.0, 12.0),
    lim_lo('5VOff', 0.1),
    lim_hilo_delta('5VOn', 5.0, 0.1),
    lim_lo('BrakeOff', 0.1),
    lim_hilo_delta('BrakeOn', 12.0, 0.1),
    lim_lo('LightOff', 0.3),
    lim_hilo_delta('LightOn', 12.0, 0.3),
    lim_lo('RemoteOff', 0.1),
    lim_hilo_delta('RemoteOn', 12.0, 0.1),
    lim_hi('RedLedOff', 9.0),
    lim_lo('RedLedOn', 0.1),
    lim_hilo_delta('FreqTP3', 0.56, 0.2),
    lim_boolean('Notify', True),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = t = None


class Initial(tester.TestSequence):

    """Trs1 Initial Test Program."""

    def __init__(self, physical_devices):
        """Create the test program as a linear sequence.

           @param physical_devices Physical instruments of the Tester

        """
        super().__init__()
        self._devices = physical_devices
        self._limits = LIMITS

    def open(self, parameter):
        """Prepare for testing."""
        super().open()
        self.steps = (
            tester.TestStep('PowerUp', self._step_power_up),
            tester.TestStep('BreakAway', self._step_breakaway),
            tester.TestStep('BattLow', self._step_batt_low),
            )
        global d, s, m, t
        d = LogicalDevices(self._devices)
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

    def _step_power_up(self):
        """Apply 12Vdc input and measure voltages."""
        self.fifo_push(
            ((s.oVin, 0.0), (s.o5V, 0.0), (s.oBrake, 0.0), (s.oLight, 0.0),
             (s.oRemote, 0.0), ))

        t.pwr_up.run()

    def _step_breakaway(self):
        """Measure voltages under 'breakaway' condition."""
        self.fifo_push(
            ((s.oVin, 12.0), (s.o5V, 5.0), (s.oBrake, 12.0), (s.oLight, 12.0),
             (s.oRemote, 12.0), (s.oRed, 10.0), (s.oYesNoGreen, True),
             (s.tp3, ((0.56,),)), ))

        t.brkaway.run()

    def _step_batt_low(self):
        """Check operation of Red Led under low battery condition."""
        self.fifo_push(
            ((s.oRed, (0.0, 10.0)), ))

        t.lowbatt.run()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

           @param devices Physical instruments of the Tester

        """
        self.dmm = tester.DMM(devices['DMM'])
        self.dso = tester.DSO(devices['DSO'])
        self.dcs_Vin = tester.DCSource(devices['DCS4'])
        # Pin for breakaway switch.
        self.rla_pin = tester.Relay(devices['RLA5'])   # ON == Asserted

    def reset(self):
        """Reset instruments."""
        self.dcs_Vin.output(0.0, False)
        self.rla_pin.set_off()


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices):
        """Create all Sensor instances.

           @param logical_devices Logical instruments used

        """
        dmm = logical_devices.dmm
        dso = logical_devices.dso
        sensor = tester.sensor
        self.oVin = sensor.Vdc(dmm, high=10, low=4, rng=100, res=0.01)
        self.o5V = sensor.Vdc(dmm, high=11, low=4, rng=10, res=0.01)
        self.oBrake = sensor.Vdc(dmm, high=12, low=4, rng=100, res=0.01)
        self.oLight = sensor.Vdc(dmm, high=13, low=4, rng=100, res=0.01)
        self.oRemote = sensor.Vdc(dmm, high=14, low=4, rng=100, res=0.01)
        self.oRed = sensor.Vdc(dmm, high=15, low=4, rng=100, res=0.01)
        self.oYesNoGreen = sensor.YesNo(
            message=tester.translate('trs1_initial', 'IsGreenLedOn?'),
            caption=tester.translate('trs1_initial', 'capGreenLed'))
        tbase = sensor.Timebase(
            range=3.0, main_mode=True, delay=0, centre_ref=False)
        trg = sensor.Trigger(
            ch=1, level=1.0, normal_mode=True, pos_slope=True)
        rdgs = (sensor.Freq(ch=1), )
        chan1 = (
            sensor.Channel(
                ch=1, mux=1, range=16.0, offset=0,
                dc_coupling=True, att=1, bwlim=True), )
        self.tp3 = sensor.DSO(dso, chan1, tbase, trg, rdgs)


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

           @param sense Sensors used
           @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.dmm_vinoff = Measurement(limits['VinOff'], sense.oVin)
        self.dmm_vin = Measurement(limits['Vin'], sense.oVin)
        self.dmm_5Voff = Measurement(limits['5VOff'], sense.o5V)
        self.dmm_5Von = Measurement(limits['5VOn'], sense.o5V)
        self.dmm_brakeoff = Measurement(limits['BrakeOff'], sense.oBrake)
        self.dmm_brakeon = Measurement(limits['BrakeOn'], sense.oBrake)
        self.dmm_lightoff = Measurement(limits['LightOff'], sense.oLight)
        self.dmm_lighton = Measurement(limits['LightOn'], sense.oLight)
        self.dmm_remoteoff = Measurement(limits['RemoteOff'], sense.oRemote)
        self.dmm_remoteon = Measurement(limits['RemoteOn'], sense.oRemote)
        self.dmm_redoff = Measurement(limits['RedLedOff'], sense.oRed)
        self.dmm_redon = Measurement(limits['RedLedOn'], sense.oRed)
        self.ui_YesNoGreen = Measurement(limits['Notify'], sense.oYesNoGreen)
        self.dso_tp3 = Measurement(limits['FreqTP3'], sense.tp3)


class SubTests():

    """SubTest Steps."""

    def __init__(self, logical_devices, measurements):
        """Create SubTest Step instances.

           @param measurements Measurements used
           @param logical_devices Logical instruments used

        """
        d = logical_devices
        m = measurements
        # PowerUp: Apply input voltage, measue.
        self.pwr_up = tester.SubStep((
            tester.RelaySubStep(((d.rla_pin, True), )),
            tester.DcSubStep(setting=((d.dcs_Vin, 12.0), ), output=True,
                                delay=0.8),
            tester.MeasureSubStep(
                (m.dmm_vinoff, m.dmm_5Voff, m.dmm_brakeoff, m.dmm_lightoff,
                 m.dmm_remoteoff), timeout=5),
            ))
        # BreakAway: Remove pin, measure.
        self.brkaway = tester.SubStep((
            tester.RelaySubStep(((d.rla_pin, False), )),
            tester.MeasureSubStep(
                (m.dmm_vin, m.dmm_5Von, m.dmm_brakeon, m.dmm_lighton,
                 m.dmm_remoteon, m.dmm_redoff, m.dso_tp3, m.ui_YesNoGreen),
                 timeout=5),
            ))
        # BattLow: Low batt voltage, measure.
        self.lowbatt = tester.SubStep((
            tester.DcSubStep(setting=((d.dcs_Vin, LOW_BATT_L), )),
            tester.MeasureSubStep((m.dmm_redon, ), timeout=5),
            tester.DcSubStep(setting=((d.dcs_Vin, LOW_BATT_U), )),
            tester.MeasureSubStep((m.dmm_redoff, ), timeout=5),
            ))
