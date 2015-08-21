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
            ('InputAdj', self._step_in_adj, None, True),
            ('OutputAdj', self._step_out_adj, None, True),
            ('Email', self._step_email, None, True),
            ('ErrorCheck', self._step_error_check, None, True),
            )
        # Set the Test Sequence in my base instance
        super().__init__(selection, sequence, fifo)
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._devices = physical_devices
        self._limits = test_limits
        self._ctr_data = []

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

    def _step_in_adj(self):
        """Input adjust and measure.

            Adjust input dc source to get Iin = 1mA.
            Measure Iin.

         """
        self.fifo_push(((s.oIsen, (0.5, ) * 30 + (1.0, 1.002), ), ))
        d.dcs_vin.output(22.0, True)
        m.ramp_VinAdj.measure(timeout=5)
        m.dmm_Iin.measure(timeout=5)

    def _step_out_adj(self):
        """Output adjust and measure.

            Adjust output DC source to get 5V across collector-emitter,
            Measure Vce.
            Measure Iout.
            Measure Iin.
            Calculate CTR.

        """
        self._ctr_data = []
        for i in range(20):
            self.fifo_push(((s.Vce[i], (-4.5, ) * 20 + (-5.0, -5.04), ),
                          (s.Iout[i], 0.60), (s.oIsen, 1.005), ))
            d.dcs_vout.output(5.0, True)
            tester.testsequence.path_push('Opto{}'.format(i + 1))
            m.ramp_VoutAdj[i].measure(timeout=5)
            m.dmm_Vce[i].measure(timeout=5)
            i_out = m.dmm_Iout[i].measure(timeout=5)[1][0]
            i_in = m.dmm_Iin.measure(timeout=5)[1][0]
            ctr = (i_out / i_in) * 100
            self._ctr_data.append(int(ctr))
            s.oMirCtr.store(ctr)
            m.dmm_ctr.measure()
            tester.testsequence.path_pop()

    def _step_email(self):
        """Email test result data."""
        self._logger.info('Building CSV data')
        uut = self.uuts[0]
        now = datetime.datetime.now().isoformat()[:19]
        header = '"UUT","TestDateTime"'
        for i in range(20):
            header += ',"CTR{}"'.format(i + 1)
        data = '"{}","{}"'.format(uut, now)
        for ctr in self._ctr_data:
            data += ',{}'.format(ctr)
        csv = header + '\r\n' + data + '\r\n'

        self._logger.info('Building email')
        outer = MIMEMultipart()
        outer['To'] = _RECIPIENT
        outer['From'] = _FROM
        outer['Subject'] = _SUBJECT + ' for unit {}'.format(uut)
        outer.preamble = 'You will not see this in a MIME-aware mail reader.'
        summsg = MIMEText('GEN8 Opto test data is attached.')
        outer.attach(summsg)

        m = MIMEApplication(csv)
        m.add_header(
            'Content-Disposition',
            'attachment',
            filename='gen8_optodata_{}_{}.csv'.format(uut, now))
        outer.attach(m)

        self._logger.info('Sending email to %s', _RECIPIENT)
        s = smtplib.SMTP(_EMAIL_SERVER)
        s.send_message(outer)
        s.quit()
