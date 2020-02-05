#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BCE282-12/24 Initial Test Program."""

import sys
import os
import inspect
import time
import serial
import tester
from tester import TestStep, LimitLow, LimitBetween, LimitDelta, LimitPercent
import share
from . import console
from . import tosbsl


class Initial(share.TestSequence):

    """BCE282-12/24 Initial Test Program."""

    # Calibration data save file (TI Text format)
    msp_savefile = {    # Needs to be writable by the tester login
        'posix': '/home/setec/testdata/bslsavedata.txt',
        'nt': r'C:\TestGear\TestData\bslsavedata.txt',
        }[os.name]
    # Password data save file
    msp_password = {    # Needs to be writable by the tester login
        'posix': '/home/setec/testdata/bslpassword.txt',
        'nt': r'C:\TestGear\TestData\bslpassword.txt',
        }[os.name]
    # Factor to tighten the calibration check
    _cal_factor = 0.5
    # Limits common to both versions
    _common = (
        LimitLow('FixtureLock', 200),
        LimitDelta('VccBiasExt', 15.0, 1.0),
        LimitDelta('Vac', 240.0, 5.0),
        LimitBetween('Vbus', 330.0, 350.0),
        LimitPercent('VccPri', 15.6, 5.0),
        LimitPercent('VccBias', 15.0, 13.0),
        LimitLow('VbatOff', 0.5),
        LimitBetween('AlarmClosed', 1000, 3000),
        LimitBetween('AlarmOpen', 11000, 13000),
        LimitBetween('Status 0', -0.1, 0.1),
        )
    # ScaleFactor: 24V model responds with 12V output to measurement "msp_vout"
    # and is designed to be calibrated with half its measured output voltage.
    limitdata = {      # Test limit selection keyed by program parameter
        '12': {
            'Limits': _common + (
                LimitBetween('OutOCP', 20.05, 24.00),
                LimitBetween('BattOCP', 14.175, 15.825),
                LimitLow('InOCP', 13.0),
                LimitPercent('VoutPreCal', 13.8, 2.6),
                LimitDelta('VoutPostCal', 13.8, _cal_factor * 0.15),
                LimitBetween('MspVout', 13.0, 14.6),
                ),
            'LoadRatio': (20, 14),      # Iout:Ibat
            'ScaleFactor': 1000,
            'HexFile': 'bce282_12_3a.txt' # TI Text format

            },
        '24': {
            'Limits': _common + (
                LimitBetween('OutOCP', 10.0, 12.0),
                LimitBetween('BattOCP', 6.0, 9.0),
                LimitLow('InOCP', 26.0),
                LimitPercent('VoutPreCal', 27.6, 2.6),
                LimitDelta('VoutPostCal', 27.6, _cal_factor * 0.25),
                LimitBetween('MspVout', 26.0, 29.2),
                ),
            'LoadRatio': (10, 6),       # Iout:Ibat
            'ScaleFactor': 500,
            'HexFile': 'bce282_3a.txt' # TI Text format
            },
        }

    def open(self, uut):
        """Prepare for testing."""
        super().open(
            self.limitdata[self.parameter]['Limits'],
            Devices, Sensors, Measurements)
        self.steps = (
            TestStep('Prepare', self._step_prepare),
            TestStep('Program', self._step_program),
            TestStep('PowerUp', self._step_power_up),
            TestStep('Calibration', self._step_cal),
            TestStep('OCP', self._step_ocp),
            )
        self.devices['msp'].scaling(
            self.limitdata[self.parameter]['ScaleFactor'])

    @share.teststep
    def _step_prepare(self, dev, mes):
        """Prepare: Dc input, measure."""
        dev['dcs_vccbias'].output(15.0, True)
        self.measure(('dmm_lock', 'dmm_vccbiasext',), timeout=5)

    @share.teststep
    def _step_program(self, dev, mes):
        """Program the board.

        Notes from the BCE282 Testing Notes:
        The bootloader software is programmed into the MSP430 processor at
        the factory and cannot be erased. This software requires a password
        to be sent with any command that can read or write the internal
        Flash as a security measure. This password consists of a dump of
        the top 32 bytes of Flash memory, so it is a run of 32 0xFF values
        for an unprogrammed part, which allows a fresh part to be programmed
        initially. If a previous version of the software is installed on the
        BCE282, the required password can be read using a command from
        the serial port.

        Performing a mass erase will erase some further special locations
        in Flash that are factory programmed with values for calibrating
        the on chip oscillator. If the contents of these locations are lost
        then the processor becomes useless as the on-chip oscillator
        frequency can no longer be set to a sufficient accuracy for
        reliable timing or serial comms. So when re-programming a part it
        is essential that these values be saved and restored.

        """
        # Serial port for programming MSP430.
        msp_port1 = share.config.Fixture.port('020827', 'MSP1')
        # Get any existing password & write to MSP_PASSWORD file
        msp = dev['msp']
        password = None
        try:    # Fails if device has never been programmed
            msp.open()
            msp.measurement_fail_on_error = False
            password = '@ffe0\n{0}\nq\n'.format(msp['PASSWD'])
            with open(self.msp_password, 'w') as fout:
                fout.write(password)
        except share.console.Error:
            pass
        finally:
            msp.measurement_fail_on_error = True
            msp.close()
        dev['rla_prog'].set_on()
        try:
            # STEP 1 - SAVE INTERNAL CALIBRATION
            sys.argv = (['',
                '--comport={0}'.format(msp_port1), ] +
                (['-P', self.msp_password, ] if password else []) +
                ['--upload=0x10C0', '--size=64', '--ti', ]
                )
            tosbsl.main()
            # Write TI Text format calibration data to a file for use later
            with open(self.msp_savefile, 'w') as fout:
                for aline in tosbsl.SAVEDATA:
                    fout.write(aline)
                    fout.write('\n')
            # STEP 2 - ERASE & RESTORE INTERNAL CALIBRATION
            sys.argv = ['',
                '--comport={0}'.format(msp_port1),
                '--masserase',
                '--program', self.msp_savefile,
                ]
            tosbsl.main()
            # STEP 3 - PROGRAM
            folder = os.path.dirname(
                os.path.abspath(inspect.getfile(inspect.currentframe())))
            sys.argv = ['',
                '--comport={0}'.format(msp_port1),
                '--program', os.path.join(folder,
                    self.limitdata[self.parameter]['HexFile']),
                ]
            tosbsl.main()
        finally:
            dev['rla_prog'].set_off()
            dev['dcs_vccbias'].output(0.0, delay=1)

    @share.teststep
    def _step_power_up(self, dev, mes):
        """Power up the unit at 240Vac and measure voltages at min load."""
        dev['acsource'].output(voltage=240.0, output=True, delay=1.0)
        dev['dcl_vbat'].output(0.1, True)
        self.measure(
            ('dmm_vac', 'dmm_vbus', 'dmm_vccpri', 'dmm_vccbias',
             'dmm_vbatoff', 'dmm_alarmclose',
             ), timeout=5)
        dev['dcl_vbat'].output(0.0)

    @share.teststep
    def _step_cal(self, dev, mes):
        """Calibration."""
        msp = dev['msp']
        msp.open()
        msp.initialise()
        mes['msp_status']()
        msp.filter_reload()
        mes['msp_vout']()
        dmm_V = mes['dmm_voutpre'].stable(delta=0.005).reading1
        msp['CAL-V'] = dmm_V
        mes['dmm_voutpost'].stable(delta=0.005)
        msp['NV-WRITE'] = True
        mes['msp_status']()
        msp.close()

    @share.teststep
    def _step_ocp(self, dev, mes):
        """Test OCP."""
        self.measure(('dmm_alarmopen', 'ramp_battocp'), timeout=5)
        dev['dcl_vbat'].output(0.0)
        mes['ramp_outocp'](timeout=5)
        dev['dcl_vout'].output(0.0)


class Devices(share.Devices):

    """Devices."""

    def open(self):
        """Create all Instruments."""
        # Physical Instrument based devices
        for name, devtype, phydevname in (
                ('dmm', tester.DMM, 'DMM'),
                ('acsource', tester.ACSource, 'ACS'),
                ('discharge', tester.Discharge, 'DIS'),
                ('dcs_vccbias', tester.DCSource, 'DCS1'),
                ('dcs_vcom', tester.DCSource, 'DCS2'),
                ('dcl_vout', tester.DCLoad, 'DCL1'),
                ('dcl_vbat', tester.DCLoad, 'DCL2'),
                ('rla_prog', tester.Relay, 'RLA1'),
            ):
            self[name] = devtype(self.physical_devices[phydevname])
        # Serial connection to the console to communicate with the MSP430
        self['msp_ser'] = serial.Serial(baudrate=57600, timeout=5.0)
        # Set port separately, as we don't want it opened yet
        self['msp_ser'].port = share.config.Fixture.port('020827', 'MSP2')
        # MSP430 Console driver
        self['msp'] = console.Console(self['msp_ser'])
        # Apply power to fixture circuits.
        self['dcs_vcom'].output(9.0, True, delay=5)
        self.add_closer(lambda: self['dcs_vcom'].output(0.0, False))

    def reset(self):
        """Reset instruments."""
        self['msp'].close()
        self['acsource'].reset()
        self['dcl_vout'].output(2.0)
        self['dcl_vbat'].output(2.0)
        time.sleep(1)
        self['discharge'].pulse()
        for ld in ('dcl_vout', 'dcl_vbat'):
            self[ld].output(0.0, False)
        for dcs in ('dcs_vccbias', ):
            self[dcs].output(0.0, False)
        self['rla_prog'].set_off()


class Sensors(share.Sensors):

    """Sensors."""

    def open(self):
        """Create all Sensors."""
        dmm = self.devices['dmm']
        msp = self.devices['msp']
        sensor = tester.sensor
        self['lock'] = sensor.Res(dmm, high=10, low=6, rng=10000, res=1)
        self['vac'] = sensor.Vac(dmm, high=1, low=1, rng=1000, res=0.01)
        self['vbus'] = sensor.Vdc(dmm, high=2, low=2, rng=1000, res=0.01)
        self['vcc_pri'] = sensor.Vdc(dmm, high=3, low=2, rng=100, res=0.001)
        self['vcc_bias'] = sensor.Vdc(dmm, high=8, low=3, rng=100, res=0.001)
        self['vout'] = sensor.Vdc(dmm, high=6, low=4, rng=100, res=0.001)
        self['vbat'] = sensor.Vdc(dmm, high=7, low=4, rng=100, res=0.001)
        self['alarm'] = sensor.Res(dmm, high=9, low=5, rng=100000, res=1)
        self['msp_stat'] = sensor.KeyedReading(msp, 'MSP-STATUS')
        self['msp_stat'].doc = 'MSP430 console'
        self['msp_vo'] = sensor.KeyedReading(msp, 'MSP-VOUT')
        self['msp_vo'].doc = 'MSP430 console'
        low, high = self.limits['OutOCP'].limit
        self['ocp_out'] = sensor.Ramp(
            stimulus=self.devices['dcl_vout'],
            sensor=self['vout'],
            detect_limit=(self.limits['InOCP'], ),
            start=low - 0.5, stop=high + 0.5,
            step=0.05, delay=0.05)
        low, high = self.limits['BattOCP'].limit
        self['ocp_batt'] = sensor.Ramp(
            stimulus=self.devices['dcl_vbat'],
            sensor=self['vbat'],
            detect_limit=(self.limits['InOCP'], ),
            start=low - 0.5, stop=high + 0.5,
            step=0.05, delay=0.05)


class Measurements(share.Measurements):

    """Measurements."""

    def open(self):
        """Create all Measurements."""
        self.create_from_names((
            ('dmm_lock', 'FixtureLock', 'lock', ''),
            ('dmm_vac', 'Vac', 'vac', ''),
            ('dmm_vbus', 'Vbus', 'vbus', ''),
            ('dmm_vccpri', 'VccPri', 'vcc_pri', ''),
            ('dmm_vccbiasext', 'VccBiasExt', 'vcc_bias', ''),
            ('dmm_vccbias', 'VccBias', 'vcc_bias', ''),
            ('dmm_vbatoff', 'VbatOff', 'vbat', ''),
            ('dmm_alarmclose', 'AlarmClosed', 'alarm', ''),
            ('dmm_alarmopen', 'AlarmOpen', 'alarm', ''),
            ('dmm_voutpre', 'VoutPreCal', 'vout',
                'Output before Calibration'),
            ('dmm_voutpost', 'VoutPostCal', 'vout',
                'Output after Calibration'),
            ('ramp_outocp', 'OutOCP', 'ocp_out', ''),
            ('ramp_battocp', 'BattOCP', 'ocp_batt', ''),
            ('msp_status', 'Status 0', 'msp_stat',
                'Ask the MSP430 to report Status'),
            ('msp_vout', 'MspVout', 'msp_vo',
                'Ask the MSP430 to report output voltage'),
            ))
