#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnitTest for CMR-SBP Test program."""

import datetime
import copy
import unittest
from unittest.mock import MagicMock, patch
from ..data_feed import UnitTester, ProgramTestCase
from programs import cmrsbp

_CMR_TEMPLATE = {
    'BATTERY MODE': 0,
    'TEMPERATURE': 297.0,
    'VOLTAGE': 13.710,
    'CURRENT': 0.0,
    'REL STATE OF CHARGE': 100,
    'ABS STATE OF CHARGE': 0,
    'REMAINING CAPACITY': 0,
    'FULL CHARGE CAPACITY': 0,
    'CHARGING CURRENT': 0.0,
    'CHARGING VOLTAGE': 0.0,
    'BATTERY STATUS': 0,
    'CYCLE COUNT': 1,
    'PACK STATUS AND CONFIG': -24416,
    'FULL PACK READING': 0,
    'HALF CELL READING': 397,
    'SENSE RESISTOR READING': 0,
    'CHARGE INPUT READING': 350,
    'ROTARY SWITCH READING': 256,
    'SERIAL NUMBER': 1234,
    }


class CMRSBPInitial(ProgramTestCase):

    """CMRSBP Initial program test suite."""

    prog_class = cmrsbp.Initial
    debug = False

    def setUp(self):
        """Per-Test setup."""
        # Patch EV2200 driver
        self.myev = MagicMock(name='EV2200_Data')
        self.myev.read_vit.side_effect = (
            {'Voltage': 12.20, 'Current': -2.00, 'Temperature': 300}, # V uncal
            {'Voltage': 12.00, 'Current': -2.00, 'Temperature': 300}, # V cal
            {'Voltage': 12.00, 'Current': -2.04, 'Temperature': 300}, # I uncal
            {'Voltage': 12.00, 'Current': -2.00, 'Temperature': 300}, # I cal
            )
        patcher = patch(
            'programs.cmrsbp.ev2200.EV2200', return_value=self.myev)
        self.addCleanup(patcher.stop)
        patcher.start()
        # Patch CMR-SBP data monitor
        self.mycmr = MagicMock(name='CMR-SBP_Data')
        self.mycmrdata = copy.copy(_CMR_TEMPLATE)
        self.mycmr.read.return_value = self.mycmrdata
        patcher = patch(
            'programs.cmrsbp.cmrsbp.CmrSbp', return_value=self.mycmr)
        self.addCleanup(patcher.stop)
        patcher.start()
        for target in (
                'share.programmer.PIC',
                'serial.Serial',
                ):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            patcher.start()
        super().setUp()

    def test_pass(self):
        """PASS run of the program."""
        self.mycmrdata['FULL CHARGE CAPACITY'] = 13000
        self.mycmrdata['SENSE RESISTOR READING'] = 250
        self.mycmrdata['HALF CELL READING'] = 110,
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'PowerUp': (
                    (sen['ovbatIn'], 0.5), (sen['ovbat'], 12.0),
                    (sen['oVcc'], 3.3),
                    ),
                'Program': (
                    (sen['oVcc'], 5.0),
                    ),
                'CheckPicValues': (
                    ),
                'CheckVcharge': (
                    (sen['ovbat'], 12.0), (sen['oVcc'], 3.3),
                    ),
                'CalBQvolts': (
                    (sen['ovbat'], 12.0),
                    ),
                'CalBQcurrent': (
                    (sen['oibat'], -0.02),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(16, len(result.readings))
        self.assertEqual(
            ['PowerUp', 'Program', 'CheckPicValues', 'CheckVcharge',
             'CalBQvolts', 'CalBQcurrent'],
            self.tester.ut_steps)
        # Check EV2200 calls
        self.assertEqual(4, self.myev.read_vit.call_count)
        self.assertEqual(1, self.myev.cal_v.call_count)
        self.assertEqual(1, self.myev.cal_i.call_count)


class CMRSBPSerialDate(ProgramTestCase):

    """CMRSBP SerialDate program test suite."""

    prog_class = cmrsbp.SerialDate
    debug = False
    sernum = '9136861F1234'

    def setUp(self):
        """Per-Test setup."""
        # Patch EV2200 driver
        self.myev = MagicMock(name='EV2200')
        patcher = patch(
            'programs.cmrsbp.ev2200.EV2200', return_value=self.myev)
        self.addCleanup(patcher.stop)
        patcher.start()
        myser = MagicMock(name='SerialPort')
        myser.read.return_value = b''
        patcher = patch('serial.Serial', return_value=myser)
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def test_pass(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'SerialDate': (
                    (sen['ovbatIn'], 0.5),
                    (sen['sn_entry_ini'], (self.sernum, )),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(2, len(result.readings))
        self.assertEqual(['SerialDate'], self.tester.ut_steps)
        # Check S/N & Date were written
        self.myev.sn_date.assert_called_once_with(
            datecode=datetime.date.today().isoformat(),
            serialno=self.sernum[-4:]
            )


class _CMRSBPFin(ProgramTestCase):

    """CMRSBP Final program test suite."""

    prog_class = cmrsbp.Final

    def setUp(self):
        """Per-Test setup."""
        # Patch CMR-SBP data monitor
        self.mycmr = MagicMock(name='CMRSBP')
        self.mycmrdata = copy.copy(_CMR_TEMPLATE)
        self.mycmr.read.return_value = self.mycmrdata
        patcher = patch(
            'programs.cmrsbp.cmrsbp.CmrSbp', return_value=self.mycmr)
        self.addCleanup(patcher.stop)
        patcher.start()
        patcher = patch('serial.Serial')
        self.addCleanup(patcher.stop)
        patcher.start()
        super().setUp()

    def _pass_run(self):
        """PASS run of the program."""
        sen = self.test_program.sensors
        data = {
            UnitTester.key_sen: {       # Tuples of sensor data
                'Startup': (
                    (sen['sn_entry_fin'], (self.sernum, )),
                    ),
                'Verify': (
                    (sen['ovbatIn'], 13.72),
                    ),
                },
            }
        self.tester.ut_load(data, self.test_program.sensor_store)
        self.tester.test(('UUT1', ))
        result = self.tester.ut_result
        self.assertEqual('P', result.code)
        self.assertEqual(13, len(result.readings))
        self.assertEqual(['Startup', 'Verify'], self.tester.ut_steps)
        # Access to the CMR data driver
        self.mycmr.read.assert_called_once_with()


class CMR_8_Final(_CMRSBPFin):

    """CMR-SBP-8 Final program test suite."""

    parameter = '8'
    debug = False
    sernum = 'G240214F1234'

    def test_pass_run(self):
        """PASS run of the A program."""
        self.mycmrdata['FULL CHARGE CAPACITY'] = 8000
        self.mycmrdata['SENSE RESISTOR READING'] = 50
        super()._pass_run()


class CMR_13_Final(_CMRSBPFin):

    """CMR-SBP-13 Final program test suite."""

    parameter = '13'
    debug = False
    sernum = 'G240166F1234'

    def test_pass_run(self):
        """PASS run of the B program."""
        self.mycmrdata['FULL CHARGE CAPACITY'] = 13000
        self.mycmrdata['SENSE RESISTOR READING'] = 250
        super()._pass_run()


class CMR_17_Final(_CMRSBPFin):

    """CMR-SBP-17 Final program test suite."""

    parameter = '17'
    debug = False
    sernum = 'G240323F1234'

    def test_pass_run(self):
        """PASS run of the C program."""
        self.mycmrdata['REL STATE OF CHARGE'] = 25
        self.mycmrdata['FULL CHARGE CAPACITY'] = 17000
        self.mycmrdata['SENSE RESISTOR READING'] = 450
        super()._pass_run()


class CMRDataMonitor(unittest.TestCase):

    """CMR-SBP data monitor test suite."""

    _data_template = (
        ('BATTERY MODE', '24576'),
        ('TEMPERATURE', '297.0'),
        ('VOLTAGE', '13.710'),
        ('CURRENT', '0.013'),
        ('REL STATE OF CHARGE', '100'),
        ('ABS STATE OF CHARGE', '104'),
        ('REMAINING CAPACITY', '8283'),
        ('FULL CHARGE CAPACITY', '8283'),
        ('CHARGING CURRENT', '0.400'),
        ('CHARGING VOLTAGE', '16.000'),
        ('BATTERY STATUS', '224'),
        ('CYCLE COUNT', '1'),
        ('PACK STATUS AND CONFIG', '-24416'),
        ('FULL PACK READING', '790'),
        ('HALF CELL READING', '397'),
        ('SENSE RESISTOR READING', '66'),
        ('CHARGE INPUT READING', '1'),
        ('ROTARY SWITCH READING', '256'),
        ('SERIAL NUMBER', '949'),
        )

    def test_read(self):
        """Read CMR data."""
        myser = MagicMock(name='SerialPort')
        # Generate the binary serial data
        response = bytearray()
        for entry in self._data_template:
            response += '#{0[0]},{0[1]}\n'.format(entry).encode()
        myser.read.return_value = response
        # Generate expected result of a data read call
        myresult = {}
        for entry in self._data_template:
            val = float(entry[1]) if '.' in entry[1] else int(entry[1])
            myresult[entry[0]] = val
        # Read data
        cmr = cmrsbp.cmrsbp.CmrSbp(myser)
        result = cmr.read()
        cmr.close()
        self.assertEqual(myresult, result)
