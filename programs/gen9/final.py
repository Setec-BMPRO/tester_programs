#!/usr/bin/env python3
# Copyright 2018 SETEC Pty Ltd
"""GEN9-540 Final Test Program."""

from pydispatch import dispatcher

import tester

import share
from . import config


class Final(share.TestSequence):
    """GEN9-540 Final Test Program."""

    def open(self, uut):
        """Create the test program as a linear sequence."""
        self.cfg = config.Config
        self.cfg.configure(self.parameter, uut)
        Sensors.callback = self._dso_callback
        super().configure(self.cfg.limits_final, Devices, Sensors, Measurements)
        super().open(uut)
        self.steps = (
            tester.TestStep("PowerUp", self._step_pwrup),
            tester.TestStep("PowerOn", self._step_pwron),
            tester.TestStep("Transient", self._step_transient),
            tester.TestStep("FullLoad", self._step_fullload),
            tester.TestStep("115V", self._step_fullload115),
        )

    @share.teststep
    def _step_pwrup(self, dev, mes):
        """Power Up step."""
        mes["dmm_fanoff"](timeout=5)
        dev["acsource"].output(240.0, output=True)
        self.dcload(
            (("dcl_5v", 0.1), ("dcl_24v", 1.0), ("dcl_12v", 1.0)),
            output=True,
            delay=0.5,
        )
        self.measure(("dmm_5v", "dmm_12voff", "dmm_24voff", "dmm_pwrfail"), timeout=10)

    @share.teststep
    def _step_pwron(self, dev, mes):
        """Power On step."""
        self.dcload((("dcl_5v", 0.0), ("dcl_24v", 0.0), ("dcl_12v", 0.0)))
        dev["rla_pson"].set_on()
        mes["dmm_fanon"](timeout=15)
        self.measure(
            ("dmm_12v", "dmm_24v", "dmm_pwrfailoff", "dmm_gpo1", "dmm_gpo2"), timeout=5
        )

    @share.teststep
    def _step_transient(self, dev, mes):
        """12V Transient Response.

        To detect U104 pin-9 to pin-10 short.

        Verification data:
            Unit        Ok      Faulty_1    Faulty_2
        ---------------------------------------------
        A2152270010     11      83          77
        A2152270011     13      61          58
        A2152270012     23      73          70
        A2152270013     16      64          61
        A2152270014     13      69          72
        A1927040011     20      x           x

        """
        # Wait long enough for DSO AC coupling to settle
        dev["dcl_12v"].output(2.0, delay=2)
        # This DSO measurement will callback to _dso_callback()
        # to apply the higher load
        mes["dso_12v"]()
        dev["dcl_12v"].output(2.0, delay=0.5)

    def _dso_callback(self):
        """This load step should trigger the DSO as the 12V dips."""
        self.devices["dcl_12v"].output(20.0, delay=0.1)

    @share.teststep
    def _step_fullload(self, dev, mes):
        """Full Load step."""
        self.dcload((("dcl_5v", 2.0), ("dcl_24v", 10.0), ("dcl_12v", 24.0)), delay=0.5)
        self.measure(("dmm_5v", "dmm_24v", "dmm_12v"), timeout=5)

    @share.teststep
    def _step_fullload115(self, dev, mes):
        """115Vac step."""
        dev["acsource"].output(voltage=115.0, delay=0.5)
        self.measure(
            (
                "dmm_5v",
                "dmm_24v",
                "dmm_12v",
            ),
            timeout=5,
        )


class Devices(share.Devices):
    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname, doc in (
            ("dmm", tester.DMM, "DMM", ""),
            ("dso", tester.DSO, "DSO", ""),
            ("acsource", tester.ACSource, "ACS", "AC Input"),
            ("dcl_12v", tester.DCLoad, "DCL1", "12V Load"),
            ("dcl_24v", tester.DCLoad, "DCL3", "24V Load"),
            ("dcl_5v", tester.DCLoad, "DCL4", "5V Load"),
            ("rla_pson", tester.Relay, "RLA3", "PSON control"),
            ("dcs_airflow", tester.DCSource, "DCS3", "Power to airflow detector"),
        ):
            self[name] = devtype(self.physical_devices[phydevname], doc)
        self["dcs_airflow"].output(12.0, True)
        self.add_closer(lambda: self["dcs_airflow"].output(0.0, False))

    def reset(self):
        """Reset instruments."""
        # Switch off AC Source and discharge the unit
        self["acsource"].reset()
        self["dcl_5v"].output(1.0)
        self["dcl_12v"].output(5.0)
        self["dcl_24v"].output(5.0, delay=1.0)
        for ld in ("dcl_12v", "dcl_24v", "dcl_5v"):
            self[ld].output(0.0, False)
        self["rla_pson"].set_off()


class Sensors(share.Sensors):
    """Sensors."""

    callback = None

    def open(self):
        """Create all Sensors."""
        dmm = self.devices["dmm"]
        sensor = tester.sensor
        self["gpo1"] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self["gpo2"] = sensor.Vac(dmm, high=8, low=4, rng=1000, res=0.01)
        self["airflow"] = sensor.Vdc(dmm, high=2, low=2, rng=100, res=0.1)
        self["airflow"].doc = "Airflow detector"
        # The 5V output pin. Subject to load current errors.
        #        self['o5v'] = sensor.Vdc(dmm, high=3, low=3, rng=10, res=0.0001)
        # The LED output pin. 5V - 100R - Diode.
        self["o5v"] = sensor.Vdc(dmm, high=7, low=3, rng=10, res=0.0001)
        self["o12v"] = sensor.Vdc(dmm, high=4, low=3, rng=100, res=0.001)
        self["o24v"] = sensor.Vdc(dmm, high=5, low=3, rng=100, res=0.001)
        self["pwrfail"] = sensor.Vdc(dmm, high=6, low=3, rng=100, res=0.01)
        dso = self.devices["dso"]
        tbase = sensor.Timebase(range=0.001, main_mode=True, delay=0, centre_ref=False)
        chan = sensor.Channel(
            ch=1, mux=1, range=0.4, offset=0.0, dc_coupling=False, att=1, bwlim=True
        )
        trg = sensor.Trigger(ch=1, level=-0.04, normal_mode=True, pos_slope=False)
        rdg = sensor.Vmax(ch=1)
        self["12V_Vmax"] = sensor.DSO(dso, [chan], tbase, trg, [rdg], single=True)
        dispatcher.connect(
            self._dso_trigger, sender=self["12V_Vmax"], signal=tester.SigDso
        )

    def _dso_trigger(self):
        """DSO Ready handler."""
        if self.callback:
            self.callback()


class Measurements(share.Measurements):
    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names(
            (
                ("dmm_fanoff", "FanOff", "airflow", "Fan not running"),
                ("dmm_fanon", "FanOn", "airflow", "Fan running"),
                ("dmm_gpo1", "GPO1out", "gpo1", "GPO1 output ON"),
                ("dmm_gpo2", "GPO2out", "gpo2", "GPO2 output ON"),
                ("dmm_5v", "5V", "o5v", "5V output ok"),
                ("dmm_12voff", "12Voff", "o12v", "12V output off"),
                ("dmm_12v", "12V", "o12v", "12V output ok"),
                ("dmm_24voff", "24Voff", "o24v", "24V output off"),
                ("dmm_24v", "24V", "o24v", "24V output ok"),
                ("dmm_pwrfail", "PwrFail", "pwrfail", "PFAIL asserted"),
                ("dmm_pwrfailoff", "PwrFailOff", "pwrfail", "PFAIL not asserted"),
                ("dso_12v", "12Vmax", "12V_Vmax", "12V transient ok"),
            )
        )
