#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Opto Test Program."""

import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from pydispatch import dispatcher
import tester

LIMITS = tester.testlimit.limitset((
    # Set 0.005 back from 1mA.
    ('Isen1', 1, None, 0.995, None, None),
    # Set 0.05 back from 10mA.
    ('Isen10', 1, None, 9.95, None, None),
    ('VinAdj', 1, 0, 99999, None, None),
    # 1mA +/- 1%.
    ('Iin1', 1, 0.99, 1.05, None, None),
    # 10mA +/- 1%.
    ('Iin10', 1, 9.9, 10.5, None, None),
    ('Vsen', 1, 5.0, None, None, None),
    ('VceAdj', 1, 4.99, 5.04, None, None),
    # 5.0V +/- 1%.
    ('Vce', 1, 4.95, 5.05, None, None),
    ('VoutAdj', 1, 0, 99999, None, None),
    ('Iout', 1, 0.0, 22.0, None, None),
    ('CTR', 1, 0, 220, None, None),
    ('SerNum', 0, None, None, r'^A[0-9]{3}$', None),
    ))

# These are module level variables to avoid having to use 'self.' everywhere.
d = s = m = None

_FROM = '"GEN8 Opto Tester" <noreply@setec.com.au>'
_RECIPIENT = '"Michael Burrell" <michael.burrell@setec.com.au>'
# _RECIPIENT = '"Stephen Bell" <stephen.bell@setec.com.au>'
# _RECIPIENT = '"Rajiv Fonn" <rajiv.fonn@setec.com.au>'
_SUBJECT = 'GEN8 Opto Test Data'
_EMAIL_SERVER = 'smtp.core.setec.com.au'


class Main(tester.TestSequence):

    """Opto Test Program."""

    def __init__(self, physical_devices):
        """Create the test program as a linear sequence.

           @param per_panel Number of units tested together
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        super().__init__()
        self._devices = physical_devices
        self._limits = LIMITS
        self._brdnum = None
        self._ctr_data1 = []
        self._ctr_data10 = []

    def open(self, parameter):
        """Prepare for testing."""
        sequence = (
            tester.TestStep('BoardNum', self._step_boardnum),
            tester.TestStep('InputAdj', self._step_in_adj1),
            tester.TestStep('OutputAdj', self._step_out_adj1),
            tester.TestStep('InputAdj', self._step_in_adj10),
            tester.TestStep('OutputAdj', self._step_out_adj10),
            tester.TestStep('Email', self._step_email, not self.fifo),
            )
        super().open(sequence)
        global d, s, m
        d = LogicalDevices(self._devices)
        s = Sensors(d, self._limits)
        m = Measurements(s, self._limits)

    def close(self):
        """Finished testing."""
        global m, d, s
        m = d = s = None
        super().close()

    def safety(self):
        """Make the unit safe after a test."""
        d.reset()

    def _step_boardnum(self):
        """Get the PCB number."""
        self.fifo_push(((s.oSnEntry, ('A999', )), ))

        self._brdnum = m.ui_SnEntry.measure().reading1

    def _step_in_adj1(self):
        """Input adjust and measure.

        Adjust input dc source to get the required value of Iin.

         """
        self.fifo_push(((s.oIsen, (0.5, ) * 30 + (1.0, 1.003), ), ))
        d.dcs_vin.output(22.5, True)
        m.ramp_VinAdj1.measure(timeout=2)
        m.dmm_Iin1.measure(timeout=2).reading1

    def _step_in_adj10(self):
        """Input adjust and measure.

        Adjust input dc source to get the required value of Iin.

         """
        self.fifo_push(((s.oIsen, (5.0, ) * 30 + (10.0, 10.03), ), ))
        d.dcs_vin.output(35.5, True)
        m.ramp_VinAdj10.measure(timeout=2)
        m.dmm_Iin10.measure(timeout=2).reading1

    def _step_out_adj1(self):
        """Output adjust and measure.

        Adjust output DC source to get 5V across collector-emitter,
        Measure Vce.
        Measure Iout.
        Measure Iin.
        Calculate CTR.

        """
        for i in range(20):
            self.fifo_push(
                ((s.Vce[i], (-5.3, -4.9, -5.02, -5.02)),
                 (s.Iout[i], 0.6), (s.oIsen, 1.003), ))
            d.dcs_vout.output(4.7, True)
            with tester.PathName('Opto{}'.format(i + 1)):
                m.ramp_VoutAdj1[i].measure(timeout=2)
                m.dmm_Vce[i].measure(timeout=2)
                i_out = m.dmm_Iout[i].measure(timeout=2).reading1
                i_in = m.dmm_Iin1.measure(timeout=2).reading1
                ctr = (i_out / i_in) * 100
                self._ctr_data1.append(int(ctr))
                s.oMirCtr.store(ctr)
                m.dmm_ctr.measure()

    def _step_out_adj10(self):
        """Output adjust and measure.

        Adjust output DC source to get 5V across collector-emitter,
        Measure Vce.
        Measure Iout.
        Measure Iin.
        Calculate CTR.

        """
        for i in range(20):
            self.fifo_push(
                ((s.Vce[i], (-5.5, -4.8, -5.2, -4.94, -5.02, -5.02)),
                 (s.Iout[i], 15.0), (s.oIsen, 10.03), ))
            d.dcs_vout.output(16.0, True)
            with tester.PathName('Opto{}'.format(i + 1)):
                m.ramp_VoutAdj10[i].measure(timeout=2)
                m.dmm_Vce[i].measure(timeout=2)
                i_out = m.dmm_Iout[i].measure(timeout=2).reading1
                i_in = m.dmm_Iin10.measure(timeout=2).reading1
                ctr = (i_out / i_in) * 100
                self._ctr_data10.append(int(ctr))
                s.oMirCtr.store(ctr)
                m.dmm_ctr.measure()

    def _step_email(self):
        """Email test result data."""
        now = datetime.datetime.now().isoformat()[:19]
        header = '"UUT","TestDateTime"'
        for i in range(20):
            header += ',"CTR{}_1"'.format(i + 1)
        for i in range(20):
            header += ',"CTR{}_10"'.format(i + 1)
        data = '"{}","{}"'.format(self._brdnum, now)
        for ctr in self._ctr_data1:
            data += ',{}'.format(ctr)
        for ctr in self._ctr_data10:
            data += ',{}'.format(ctr)
        csv = header + '\r\n' + data + '\r\n'
        outer = MIMEMultipart()
        outer['To'] = _RECIPIENT
        outer['From'] = _FROM
        outer['Subject'] = _SUBJECT + ' for unit {}'.format(self._brdnum)
        outer.preamble = 'You will not see this in a MIME-aware mail reader.'
        summsg = MIMEText('GEN8 Opto test data is attached.')
        outer.attach(summsg)
        m = MIMEApplication(csv)
        m.add_header(
            'Content-Disposition',
            'attachment',
            filename='gen8_optodata_{}_{}.csv'.format(self._brdnum, now))
        outer.attach(m)
        s = smtplib.SMTP(_EMAIL_SERVER)
        s.send_message(outer)
        s.quit()


class LogicalDevices():

    """Logical Devices."""

    def __init__(self, devices):
        """Create all Logical Instruments.

        @param devices Physical instruments of the Tester

        """
        self.dmm = tester.DMM(devices['DMM'])
        self.dcs_vin = tester.DCSource(devices['DCS1'])
        self.dcs_vout = tester.DCSource(devices['DCS2'])

    def reset(self):
        """Reset instruments."""
        for dcs in (self.dcs_vin, self.dcs_vout):
            dcs.output(0.0, False)


class Sensors():

    """Sensors."""

    def __init__(self, logical_devices, limits):
        """Create all Sensor instances.

        @param logical_devices Logical instruments used
        @param limits Product test limits

        """
        dmm = logical_devices.dmm
        sensor = tester.sensor
        self.oMirCtr = sensor.Mirror()
        dispatcher.connect(
            self._reset, sender=tester.signals.Thread.tester,
            signal=tester.signals.TestRun.stop)
        self.oIsen = sensor.Vdc(dmm, high=1, low=1, rng=100, res=0.001)
        self.oVinAdj1 = sensor.Ramp(
            stimulus=logical_devices.dcs_vin, sensor=self.oIsen,
            detect_limit=(limits['Isen1'], ),
            start=22.5, stop=24.0, step=0.01, delay=0.02, reset=False)
        self.oVinAdj10 = sensor.Ramp(
            stimulus=logical_devices.dcs_vin, sensor=self.oIsen,
            detect_limit=(limits['Isen10'], ),
            start=35.5, stop=38.0, step=0.01, delay=0.02, reset=False)
        # Generate a list of 20 collector-emitter voltage sensors.
        self.Vce = []
        for i in range(20):
            s = sensor.Vdc(
                dmm, high=(i + 5), low=2, rng=10, res=0.0001, scale=-1)
            self.Vce.append(s)
        # Generate a list of 20 VoutAdj ramp sensors for 1mA and 10mA inputs.
        self.VoutAdj1 = []
        for i in range(20):
            s = sensor.Search(
                stimulus=logical_devices.dcs_vout, sensor=self.Vce[i],
                detect_limit=(
                    limits['Vsen'],), response_limit=(limits['VceAdj'],),
                start=4.7, stop=6.7, resolution=0.04, delay=0.1)
            self.VoutAdj1.append(s)
        self.VoutAdj10 = []
        for i in range(20):
            s = sensor.Search(
                stimulus=logical_devices.dcs_vout, sensor=self.Vce[i],
                detect_limit=(
                    limits['Vsen'],), response_limit=(limits['VceAdj'],),
                start=14.0, stop=26.0, resolution=0.04, delay=0.1)
            self.VoutAdj10.append(s)
        # Generate a list of 20 Iout voltage sensors.
        self.Iout = []
        for i in range(20):
            s = sensor.Vdc(dmm, high=(i + 5), low=1, rng=100, res=0.001)
            self.Iout.append(s)
        self.oSnEntry = sensor.DataEntry(
            message=tester.translate('opto_test', 'msgSnEntry'),
            caption=tester.translate('opto_test', 'capSnEntry'))

    def _reset(self):
        """TestRun.stop: Empty the Mirror Sensors."""
        self.oMirCtr.flush()


class Measurements():

    """Measurements."""

    def __init__(self, sense, limits):
        """Create all Measurement instances.

        @param sense Sensors used
        @param limits Product test limits

        """
        Measurement = tester.Measurement
        self.dmm_ctr = Measurement(limits['CTR'], sense.oMirCtr)
        self.dmm_Iin1 = Measurement(limits['Iin1'], sense.oIsen)
        self.dmm_Iin10 = Measurement(limits['Iin10'], sense.oIsen)
        self.ramp_VinAdj1 = Measurement(limits['VinAdj'], sense.oVinAdj1)
        self.ramp_VinAdj10 = Measurement(limits['VinAdj'], sense.oVinAdj10)
        # Generate a tuple of 20 collector-emitter voltage measurements.
        self.dmm_Vce = []
        for sen in sense.Vce:
            m = Measurement(limits['Vce'], sen)
            self.dmm_Vce.append(m)
        # Generate tuple of 20 VoutAdj ramps for 1mA & 10mA inputs.
        self.ramp_VoutAdj1 = []
        for sen in sense.VoutAdj1:
            m = Measurement(limits['VoutAdj'], sen)
            self.ramp_VoutAdj1.append(m)
        self.ramp_VoutAdj10 = []
        for sen in sense.VoutAdj10:
            m = Measurement(limits['VoutAdj'], sen)
            self.ramp_VoutAdj10.append(m)
        # Generate a tuple of 20 Iout voltage measurements.
        self.dmm_Iout = []
        for sen in sense.Iout:
            m = Measurement(limits['Iout'], sen)
            self.dmm_Iout.append(m)
        self.ui_SnEntry = Measurement(limits['SerNum'], sense.oSnEntry)
