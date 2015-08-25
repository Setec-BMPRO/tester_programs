#!/usr/bin/env python3
"""Opto Test Program."""

import logging
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

import tester
from . import support
from . import limit

LIMIT_DATA = limit.DATA

# These are module level variable to avoid having to use 'self.' everywhere.
d = None        # Shortcut to Logical Devices
s = None        # Shortcut to Sensors
m = None        # Shortcut to Measurements


_FROM = '"GEN8 Opto Tester" <noreply@setec.com.au>'
_RECIPIENT = '"Stephen Bell" <stephen.bell@setec.com.au>'
_SUBJECT = 'GEN8 Opto Test Data'
_EMAIL_SERVER = 'smtp.core.setec.com.au'


class Main(tester.TestSequence):

    """Opto Test Program."""

    def __init__(self, selection, physical_devices, test_limits, fifo):
        """Create the test program as a linear sequence.

           @param selection Product test program
           @param physical_devices Physical instruments of the Tester
           @param test_limits Product test limits

        """
        # Define the (linear) Test Sequence
        #    (Name, Target, Args, Enabled)
        sequence = (
            ('BoardNum', self._step_boardnum, None, True),
            ('InputAdj', self._step_in_adj1, None, True),
            ('OutputAdj', self._step_out_adj1, None, True),
            ('InputAdj', self._step_in_adj10, None, True),
            ('OutputAdj', self._step_out_adj10, None, True),
            ('Email', self._step_email, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        self._brdnum = None
        self._ctr_data1 = []
        self._ctr_data10 = []

    def open(self):
        """Prepare for testing."""
        self._logger.info('Open')
        global d, s, m
        d = support.LogicalDevices(self._devices)
        s = support.Sensors(d, self._limits)
        m = support.Measurements(s, self._limits)

    def close(self):
        """Finished testing."""
        self._logger.info('Close')
        global m, d, s
        m = d = s = None

    def safety(self, run=True):
        """Make the unit safe after a test."""
        self._logger.info('Safety(%s)', run)
        if run:
            # Reset Logical Devices
            d.reset()

    def _step_error_check(self):
        """Check physical instruments for errors."""
        d.error_check()

    def _step_boardnum(self):
        """Get the PCB number."""
        result, brdnum = m.ui_SnEntry.measure()
        self._brdnum = brdnum[0]

    def _step_in_adj1(self):
        """Input adjust and measure.

            Adjust input dc source to get the required value of Iin.

         """
        self.fifo_push(((s.oIsen, (0.5, ) * 30 + (1.0,), ), ))
        d.dcs_vin.output(0.0, True)
        m.ramp_VinAdj1.measure(timeout=5)

    def _step_in_adj10(self):
        """Input adjust and measure.

            Adjust input dc source to get the required value of Iin.

         """
        self.fifo_push(((s.oIsen, (5.0, ) * 30 + (10.0,), ), ))
        d.dcs_vin.output(0.0, True)
        m.ramp_VinAdj10.measure(timeout=5)

    def _step_out_adj1(self):
        """Output adjust and measure.

            Adjust output DC source to get 5V across collector-emitter,
            Measure Vce.
            Measure Iout.
            Measure Iin.
            Calculate CTR.

        """
        for i in range(20):
            self.fifo_push(((s.Vce[i], (-4.5, ) * 20 + (-5.0, -5.02), ),
                          (s.Iout[i], 0.6), (s.oIsen, 1.003), ))
            d.dcs_vout.output(5.0, True)
            tester.testsequence.path_push('Opto{}'.format(i + 1))
            m.ramp_VoutAdj[i].measure(timeout=5)
            m.dmm_Vce[i].measure(timeout=5)
            i_out = m.dmm_Iout[i].measure(timeout=5)[1][0]
            i_in = m.dmm_Iin1.measure(timeout=5)[1][0]
            ctr = (i_out / i_in) * 100
            self._ctr_data1.append(int(ctr))
            s.oMirCtr.store(ctr)
            m.dmm_ctr.measure()
            tester.testsequence.path_pop()

    def _step_out_adj10(self):
        """Output adjust and measure.

            Adjust output DC source to get 5V across collector-emitter,
            Measure Vce.
            Measure Iout.
            Measure Iin.
            Calculate CTR.

        """
        for i in range(20):
            self.fifo_push(((s.Vce[i], (-4.5, ) * 20 + (-5.0, -5.02), ),
                          (s.Iout[i], 7.5), (s.oIsen, 10.03), ))
            d.dcs_vout.output(5.0, True)
            tester.testsequence.path_push('Opto{}'.format(i + 1))
            m.ramp_VoutAdj[i].measure(timeout=5)
            m.dmm_Vce[i].measure(timeout=5)
            i_out = m.dmm_Iout[i].measure(timeout=5)[1][0]
            i_in = m.dmm_Iin10.measure(timeout=5)[1][0]
            ctr = (i_out / i_in) * 100
            self._ctr_data10.append(int(ctr))
            s.oMirCtr.store(ctr)
            m.dmm_ctr.measure()
            tester.testsequence.path_pop()

    def _step_email(self):
        """Email test result data."""
        self._logger.info('Building CSV data')
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
        self._logger.info('Csv Data: %s', csv)
        self._logger.info('Building email')
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

        self._logger.info('Sending email to %s', _RECIPIENT)
        s = smtplib.SMTP(_EMAIL_SERVER)
        s.send_message(outer)
        s.quit()
