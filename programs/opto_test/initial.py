#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2022 SETEC Pty Ltd
"""Opto Test Program."""

import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

import tester

import share


class Initial(share.TestSequence):

    """Opto Test Program."""

    _opto_count = 20
    limitdata = (
        tester.LimitHigh('Isen1', 0.995e-3),
        tester.LimitHigh('Isen10', 9.95e-3),
        tester.LimitDelta('VinAdj', 0, 99999),
        tester.LimitDelta('Iin1', 0.99e-3, 1.05e-3),
        tester.LimitDelta('Iin10', 9.9e-3, 10.5e-3),
        tester.LimitHigh('Vsen', 5.0),
        tester.LimitDelta('VceAdj', 4.99, 5.04),
        tester.LimitPercent('Vce', 5.00,  1.0),
        tester.LimitDelta('VoutAdj', 0, 99999),
        tester.LimitDelta('Iout', 0.0e-3, 22.0e-3),
        tester.LimitDelta('CTR', 0, 220),
        )
    _recipient = '"Stephen Bell" <stephen.bell@setec.com.au>'
#    _recipient = '"Wayne Tomkins" <wayne.tomkins@setec.com.au>'
    _email_server = 'smtp.mel.setec.com.au'

    def open(self, uut):
        """Prepare for testing."""
        Sensors._opto_count = self._opto_count
        super().open(self.limitdata, Devices, Sensors, Measurements)
        self.steps = (
            tester.TestStep('BoardNum', self._step_boardnum),
            tester.TestStep('InputAdj1', self._step_in_adj1),
            tester.TestStep('OutputAdj1', self._step_out_adj1),
            tester.TestStep('InputAdj10', self._step_in_adj10),
            tester.TestStep('OutputAdj10', self._step_out_adj10),
            tester.TestStep('Email', self._step_email),
            )
        self.sernum = None
        self._ctr_data1 = []
        self._ctr_data10 = []

    @share.teststep
    def _step_boardnum(self, dev, mes):
        """Get the PCB number."""
        self.sernum = self.get_serial(self.uuts, 'SerNum', 'ui_sernum')
        self._ctr_data1.clear()
        self._ctr_data10.clear()

    @share.teststep
    def _step_in_adj1(self, dev, mes):
        """Input adjust and measure.

        Adjust input DC source to get the required value of Iin.

         """
        dev['dcs_iset'].output(22.5, True)
        self.measure(('ramp_VinAdj1', 'dmm_Iin1', ), timeout=2)

    @share.teststep
    def _step_out_adj1(self, dev, mes):
        """Output adjust and measure.

        Adjust output DC source to get 5V across collector-emitter,
            Measure Vce.
            Measure Iout.
            Measure Iin.
            Calculate CTR.

        """
        for i in range(self._opto_count):
            dev['dcs_vset'].output(4.7, True)
            with tester.PathName('Opto{0}'.format(i + 1)):
                mes['search_VoutAdj1'][i].measure(timeout=2)
                mes['dmm_Vce'][i].measure(timeout=2)
                i_out = mes['dmm_Iout'][i].measure(timeout=2).reading1
                i_in = mes['dmm_Iin1'].measure(timeout=2).reading1
                ctr = (i_out / i_in) * 100
                self._ctr_data1.append(int(ctr))
                mes['dmm_ctr'].sensor.store(ctr)
                mes['dmm_ctr'].measure()

    @share.teststep
    def _step_in_adj10(self, dev, mes):
        """Input adjust and measure.

        Adjust input DC source to get the required value of Iin.

         """
        dev['dcs_iset'].output(35.5, True)
        self.measure(('ramp_VinAdj10', 'dmm_Iin10', ), timeout=2)

    @share.teststep
    def _step_out_adj10(self, dev, mes):
        """Output adjust and measure.

        Adjust output DC source to get 5V across collector-emitter,
            Measure Vce.
            Measure Iout.
            Measure Iin.
            Calculate CTR.

        """
        for i in range(self._opto_count):
            dev['dcs_vset'].output(16.0, True)
            with tester.PathName('Opto{0}'.format(i + 1)):
                mes['search_VoutAdj10'][i].measure(timeout=2)
                mes['dmm_Vce'][i].measure(timeout=2)
                i_out = mes['dmm_Iout'][i].measure(timeout=2).reading1
                i_in = mes['dmm_Iin10'].measure(timeout=2).reading1
                ctr = (i_out / i_in) * 100
                self._ctr_data10.append(int(ctr))
                mes['dmm_ctr'].sensor.store(ctr)
                mes['dmm_ctr'].measure()

    @share.teststep
    def _step_email(self, dev, mes):
        """Email test result data."""
        now = datetime.datetime.now().isoformat()[:19]
        # First make the CSV header row
        lines = []
        lines.append('"PCB-Opto","TestDateTime","CTR-1","CTR-10"')
        # Now the rows of CSV data
        for opto in range(self._opto_count):
            lines.append(
                '"{0}-{1:02}","{2}",{3},{4}'.format(
                    self.sernum, opto + 1, now,
                    self._ctr_data1[opto], self._ctr_data10[opto]))
        # Build into an email and send it
        outer = MIMEMultipart()
        outer['To'] = self._recipient
        outer['From'] = '"Opto Tester" <noreply@setec.com.au>'
        outer['Subject'] = 'Opto Test Data for PCB {0}'.format(self.sernum)
        outer.preamble = 'You will not see this in a MIME-aware mail reader.'
        summsg = MIMEText('Opto test data is attached.')
        outer.attach(summsg)
        msg = MIMEApplication('\r\n'.join(lines))
        msg.add_header(
            'Content-Disposition',
            'attachment',
            filename='optodata_{0}_{1}.csv'.format(self.sernum, now))
        outer.attach(msg)
        svr = smtplib.SMTP(self._email_server)
        svr.send_message(outer)
        svr.quit()


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('dcs_iset', tester.DCSource, 'DCS1'),
                ('dcs_vset', tester.DCSource, 'DCS2'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])

    def reset(self):
        """Reset instruments."""
        for dcs in ('dcs_iset', 'dcs_vset'):
            self[dcs].output(0.0, False)


class Sensors(share.Sensors):

    """Sensors."""

    _opto_count = None

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        sensor = tester.sensor
        self['MirCTR'] = sensor.MirrorReading()
        self['Isense'] = sensor.Vdc(
            dmm,
            high=1, low=1, rng=100, res=0.001,
            scale=0.001)
        self['VinAdj1'] = sensor.Ramp(
            stimulus=self.devices['dcs_iset'],
            sensor=self['Isense'],
            detect_limit=(self.limits['Isen1'], ),
            ramp_range=sensor.RampRange(start=22.5, stop=24.0, step=0.01),
            delay=0.02)
        self['VinAdj1'].reset = False
        self['VinAdj10'] = sensor.Ramp(
            stimulus=self.devices['dcs_iset'],
            sensor=self['Isense'],
            detect_limit=(self.limits['Isen10'], ),
            ramp_range=sensor.RampRange(start=35.5, stop=38.0, step=0.01),
            delay=0.02)
        self['VinAdj10'].reset = False
        # Generate a list of collector-emitter voltage sensors
        self['Vce'] = []
        for i in range(self._opto_count):
            s = sensor.Vdc(
                dmm,
                high=(i + 5), low=2, rng=10, res=0.0001,
                scale=-1)
            self['Vce'].append(s)
        # Generate a list of VoutAdj ramp sensors for 1mA and 10mA inputs
        self['VoutAdj1'] = []
        for i in range(self._opto_count):
            s = sensor.Search(
                stimulus=self.devices['dcs_vset'],
                sensor=self['Vce'][i],
                detect_limit=self.limits['Vsen'],
                response_limit=self.limits['VceAdj'],
                start=4.7, stop=6.7, resolution=0.04, delay=0.1)
            self['VoutAdj1'].append(s)
        self['VoutAdj10'] = []
        for i in range(self._opto_count):
            s = sensor.Search(
                stimulus=self.devices['dcs_vset'],
                sensor=self['Vce'][i],
                detect_limit=self.limits['Vsen'],
                response_limit=self.limits['VceAdj'],
                start=14.0, stop=26.0, resolution=0.04, delay=0.1)
            self['VoutAdj10'].append(s)
        # Generate a list of Iout voltage sensors
        self['Iout'] = []
        for i in range(self._opto_count):
            s = sensor.Vdc(
                dmm,
                high=(i + 5), low=1, rng=100, res=0.001,
                scale=0.001)
            self['Iout'].append(s)
        self['sernum'] = sensor.DataEntry(
            message=tester.translate('opto_initial', 'msgSnEntry'),
            caption=tester.translate('opto_initial', 'capSnEntry'))


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            # measurement_name, limit_name, sensor_name, doc
            ('dmm_ctr', 'CTR', 'MirCTR', ''),
            ('dmm_Iin1', 'Iin1', 'Isense', ''),
            ('dmm_Iin10', 'Iin10', 'Isense', ''),
            ('ramp_VinAdj1', 'VinAdj', 'VinAdj1', ''),
            ('ramp_VinAdj10', 'VinAdj', 'VinAdj10', ''),
            ('ui_sernum', 'SerNum', 'sernum', 'PCB serial number'),
            ))
        # Generate collector-emitter voltage measurements
        self['dmm_Vce'] = []
        lim = self.limits['Vce']
        for sen in self.sensors['Vce']:
            self['dmm_Vce'].append(tester.Measurement(lim, sen))
        # Generate VoutAdj ramps for 1mA & 10mA inputs
        self['search_VoutAdj1'] = []
        lim = self.limits['VoutAdj']
        for sen in self.sensors['VoutAdj1']:
            self['search_VoutAdj1'].append(tester.Measurement(lim, sen))
        self['search_VoutAdj10'] = []
        lim = self.limits['VoutAdj']
        for sen in self.sensors['VoutAdj10']:
            self['search_VoutAdj10'].append(tester.Measurement(lim, sen))
        # Generate Iout voltage measurements
        self['dmm_Iout'] = []
        lim = self.limits['Iout']
        for sen in self.sensors['Iout']:
            self['dmm_Iout'].append(tester.Measurement(lim, sen))
