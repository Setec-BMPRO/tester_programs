#!/usr/bin/env python3
"""Utility Server - Texas Instruments EV220x Controller.

Uses the TI EV2200 RS232 to SMBus unit to communicate with the
TI BQ2060A Battery Management chip on the CMR-SBP.
The EV2200 is a command-response system. The EV2200 will not send anything
other than responses to commands we send it.
Refer to EV2200 Evaluation Board data.

"""

import logging
import struct
import string
import time
import datetime
import re


# BQ2060A ADC reading cycle time
# "2.0-2.5s, with an occasional extra 0.5s delay"
_ADC_DELAY = 3.0
# Time for EEPROM power-up by BQ2060A "900ms"
_EE_POWERUP = 0.9
# Manufacturer code to connect SMBus through to I2C
_EE_CODE = 0x606
# Time to wait after write to EEPROM "10ms"
_EE_DELAY = 0.01
# Max time to wait for  'Monitor' change, units of about 10ms
_CALI_MAXREADS = 500
# Number of VFC 'Monitor' changes to use
_CALI_VFC_TICKS = 30
# Deliberately corrupt the EEPROM Check Words
# after dumping
# 0 = No Action
# 1 = Write check bytes
# 2 = Write all bytes
# This will make the PIC re-write all EEPROM values
_ZAP_EEPROM = 0

# !=0 will dump EEPROM at 1st 'READVIT' command
_DUMP_AT_VIT = 0
# !=0 will wipe EEPROM at 1st 'READVIT' command
_WIPE_AT_VIT = 0

# !=0 will do the EEPROM write at calibration
_WRITE_EE_AT_CAL = 1

# Sanity check limits for Voltage Calibration
#   FSV nominal = 20000
#   VOFF nominal = 0
_FSV_MIN = 19000        # +5%
_FSV_MAX = 21000        # -5%
_VOFF_MIN = -20
_VOFF_MAX = 20

# Sanity check limits for Current Calibration
#   ADCSRG nominal = 31250
_ADC_MIN = 29687        # -5%
_ADC_MAX = 32813        # +5%

# Sanity check limits for VFC Calibration
#   VFCSRG nominal = 20480
_VFC_MIN = 18432        # -10%
_VFC_MAX = 22528        # +10%

# EV2200 Commands
_CMD = {'EchoBlock':         b'\x08',
        'RdSMBusWord':       b'\x20',
        'RdSMBusWordPEC':    b'\x22',
        'SetSMBusSlave':     b'\x42',
        'WrSMBusWord':       b'\x60',
        'WrSMBusWordPEC':    b'\x61',
        'BoardStatus':       b'\x80',
        }

# EV2200 Sub-Commands
_SUBCMD = {'ManufAccess':       b'\x00',
           'Temperature':       b'\x08',
           'Voltage':           b'\x09',
           'Current':           b'\x0A',
           'RelCharge':         b'\x0D',
           'AbsCharge':         b'\x0E',
           'RemCapacity1':      b'\x0F',  # TODO: Name??
           'FullCapacity':      b'\x10',
           'CycleCount':        b'\x17',
           'DesCapacity':       b'\x18',
           'ManufDate':         b'\x1B',
           'SerialNo':          b'\x1C',
           'LightLoadEst[MSB]': b'\x25',
           'RemCapacity':       b'\x26',
           'TempOffset[MSB]':   b'\x40',
           'AdcOffset[LSB]':    b'\x41',
           'AdcVoltGain':       b'\x43',
           'AdcResGain':        b'\x44',
           'VfcResGain':        b'\x45',
           'Reset1':            b'\x4F',
           'Monitor':           b'\x5D',
           'InvOffset[MSB]':    b'\x5F',
           'Reset2':            b'\x7D',
           'EE-Check1':         b'\x00',
           'EE-Check2':         b'\x7E',
           'EE-ManufDate':      b'\x16',
           'EE-SerialNo':       b'\x18',
           'EE-VfcOffset[LSB]': b'\x60',
           'EE-AdcOffset[LSB]': b'\x62',
           'EE-AdcVoltGain':    b'\x66',
           'EE-AdcResGain':     b'\x68',
           'EE-VfcResGain':     b'\x6A',
           # Dummy for EchoBlock
           'Echo':              b'\xFF',
           # Dummy values for SlaveSet
           'SetBQ':             b'\x16',
           'SetEE':             b'\xA0',
           }


class Ev2200Error(Exception):

    """EV2200 Exception class."""

    def __init__(self, message):
        """Save the message."""
        super().__init__()
        self.message = message

    def __str__(self):
        """Return error message."""
        return repr(self.message)


def _signed8bit(number):
    """Convert unsigned 'number' to a signed 8-bit number.

    @param  number Unsigned 8-bit value

    @return Signed integer value

    """
    return (number + 128) % 256 - 128


def _signed16bit(number):
    """Convert unsigned 'number' to a signed 16-bit number.

    @param number Unsigned 16-bit value

    @return Signed integer value

    """
    return (number + 32768) % 65536 - 32768


def _ev_cmd_err(lsb, msb):
    """Check a returned error status word.

    Raise an error if an error is indicated
    Status Word (only 1 bit ever set):
        lsb:    b0 = RS232 sync byte error
                b1 = I2C error
                b2 = SMBus error
                b3 = HDQ error
        msb: if I2C error:
                1 = bus locked low
                2 = EEPROM no acknowledge
            if SMBus error:
                1 = SMBC locked low
                2 = SMBD locked low
                3 = No acknowledge from device
                4 = SMBD not released
                5 = Bus locked before trying to Tx

    """
    if lsb > 0:
        err1 = {1: 'RS232 sync byte error',
                2: 'I2C error',
                4: 'SMBus error',
                8: 'HDQ error',
                }[lsb]
        err2 = ''
        if lsb == 2:    # I2C Error
            err2 = {1: 'bus locked low',
                    2: 'EEPROM no acknowledge',
                    }[msb]
        elif lsb == 4:  # SMBus Error
            err2 = {1: 'SMBC locked low',
                    2: 'SMBD locked low',
                    3: 'No acknowledge from device',
                    4: 'SMBD not released',
                    5: 'Bus locked before trying to Tx',
                    }[msb]
        else:
            err2 = ''
        if len(err2) > 0:
            err1 += ' - ' + err2
        raise Ev2200Error(err1)


# FIXME: _dumper() doesn't work in python3 yet
def _dumper(raw_data):
    """Data Validity Checker."""
    field_list = """\
        H Check Word 1 [0x3c7f]
        H Remaining Time Alarm (minutes) [10]
        H Remaining Capacity Alarm (mAh) [1300]
        B EDV A0 Impedance Age Factor [0]
        B EDV TC Cold Impedance Factor [0]
        B Misc Options [0]
        B Safety Overtemperature [0]
        H Charging Voltage (mV)  [16000]
        H Reserved [0x0080]
        H Cycle Count [-]
        H Reserved [0]
        H Design Voltage (mV) [12000]
        H Specification Information [0x31]
        H Manufacture Date [-]
        H Serial Number [-]
        H Fast-Charging Current (mAh) [4000]
        H Maintenance Charging Current (mA) [650]
        H Pre-Charge Current (mA) [650]
        11p Manufacturer Name [" SETEC P/L"]
        B Light Discharge Current [0]
        H Reserved [0]
        h Maximum Overcharge (note SIGNED!) (mAh) [-320]
        8p Device Name ["CMR-SBP"]
        H Last Measured Discharge [-]
        H Pack Capacity [13000]
        h Cycle Count Threshold (note SIGNED!) [-10400]
        B Reserved [0]
        B Pack Configuration [160]
        5p Device Chemistry ["NiMh"]
        B MaxT DeltaT [192]
        H Overload Current (mA)  [8000]
        B Overvoltage Margin [10]
        B Overcurrent Margin [32]
        B LioN Cell Under/Over Voltage [0]
        b Fast Charge Termination %  (note SIGNED!) [-100]
        b Fully Charged Clear %   (note SIGNED!) [-95]
        B Charge Efficiency % [0xff]
        B Current Taper Threshold [7]
        B Holdoff Time Nickel / Current Taper Qual Voltage Li-Ion [7]
        B Manufacturers Data Length [7]
        B Control Mode [53]
        B Digital Filter [45]
        B Self-Discharge Rate [190]
        B Battery Low % [18]
        B Near Full [255]
        H Reserved [0]
        H Reserved [0]
        H Reserved [0]
        H Reserved [0]
        H VFC Offset1 [-]
        B VFC Offset2 [-]
        B Temperature Offset [-]
        B ADC Offset [-]
        B Cell 2 Cal Factor (Li-Ion) / Eff Temp Compensation (Nickel) [0x20]
        B Cell 3 Cal Factor (Li-Ion) / Eff Drop Off Percentage (Nickel) [0xa0]
        B Cell 4 Cal Factor (Li-Ion) / Eff Reduction Rate (Nickel) [0x50]
        H ADC Voltage Gain*(2) [-]
        H ADC Sense Resistor Gain [-]
        H VFC Sense Resistor Gain [-]
        H VOC 25% [0xd314]
        H VOC 50% [0xcf2c]
        H VOC 75% [0xcb44]
        H EDVF/EDV0 [0x2904]
        H EMF/ EDV1 [0x2a30]
        H EDV T0 Factor [0]
        H EDV C1/C0 Factor/EDV2 [0x2af8]
        H EDV R0 Factor [0]
        H EDV R1 Factor [0]
        H Check Word 2 [0xa55a]
"""
    offset = 0
    fields = []
    for fstr in field_list.splitlines():
        fieldspec, desc = fstr.strip().split(None, 1)
        dlen = struct.calcsize(fieldspec)
        checkval = None
        if desc.endswith(']'):
            desc, checkval = desc.rsplit('[', 1)
            checkval = checkval[:-1]
        # print '%02x' % offset, fieldspec, desc, `checkval`
        fields.append([fieldspec, offset, desc, checkval])
        offset += dlen

    structdef = '<' + ''.join([x[0] for x in fields])
    assert struct.calcsize(structdef) == 0x80

    msg = ''.join([chr(x) for x in raw_data])

    dump_ok = 0
    vals = struct.unpack(structdef, msg)
    for i in zip(fields, vals):
        checkval = i[0][3]
        explain = 'OK'
        if checkval == '-':
            explain = "OK: calibration value"
        elif checkval is not None:
            checkval = eval(checkval)
            if checkval != i[1]:
                explain = " Error, expected %s" % checkval
        else:
            explain = "!!! NOT CHECKED !!!"
        if not explain.startswith('OK') or dump_ok:
            print("0x%02x = %s (%s) %s" % (i[0][1], i[1], i[0][2], explain))


class EV2200():

    """EV2200 Controller."""

    def __init__(self, serport):
        """Connect to the EV2200.

        @param serport Serial port

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._logger.info('Started')
        self._ser = serport
        self._ser.flushInput()
        self._logger.info('Connected')

    def read_vit(self):
        """Read Voltage-Current-Temperature from the BQ2060.

        @return Dictionary of readings:
                'Voltage', 'Current', 'Temperature'

        """
        self._board_status()

        if _DUMP_AT_VIT:
            self._ee_dump()
        if _WIPE_AT_VIT:
            self._ee_wipe()
        if _DUMP_AT_VIT or _WIPE_AT_VIT:
            raise Ev2200Error('FORCED FAIL')

        # values to read and scale factors
        job = (('Voltage', 1000), ('Current', 1000), ('Temperature', 10))
        # Dictionary for the return values
        data = {}
        for j in job:
            val = self._ram_read(j[0])
            val = _signed16bit(val)
            data[j[0]] = float(val) / j[1]
        self._logger.debug('ReadVIT() %s', data)
        return data

    def cal_v(self, voltage):
        """Calibrate voltage measurement - Takes about 8sec to run.

        @param voltage Actual voltage measured externally (Volt)

        @return Dictionary of readings:
                    'PreVoltage',  'PreFSV',  'PreOff'
                    'PostVoltage', 'PostFSV', 'PostOff'

        """
        self._logger.debug('Voltage = %s', voltage)
        voltage *= 1000     # convert to mVolt

        self._board_status()
        self._ee_dump()

        # Dictionary of readings to return
        readings = {}

        # Read LLE and save the MSB
        lle = self._ram_read('LightLoadEst[MSB]')
        lle_msb = lle & 0xFF00
        self._logger.debug('lle_msb = %s', lle_msb)
        # Write back LLE with MSB zeroed
        self._ram_write('LightLoadEst[MSB]', lle & 0xFF)

        # Read ADC Offset
        adc_off = self._ram_read('AdcOffset[LSB]')
        adc_off_msb = adc_off & 0xFF00
        self._logger.debug('adc_off_msb = %s', adc_off_msb)
        adc_off_lsb = adc_off & 0xFF
        adc_off_lsb = _signed8bit(adc_off_lsb)
        self._logger.debug('adc_off_lsb = %s', adc_off_lsb)

        # Read ADC Voltage Gain Factor
        fsv = self._ram_read('AdcVoltGain')
        readings['PreFSV'] = fsv
        self._logger.debug('fsv = %s', fsv)

        # Sanity check the calibration values
        if ((fsv < _FSV_MIN) or
                (fsv > _FSV_MAX) or
                (adc_off_lsb < _VOFF_MIN) or
                (adc_off_lsb > _VOFF_MAX)):
            raise Ev2200Error('Voltage calibration out of range')

        # Read and average some samples, _ADC_DELAYs apart (Voltage, Offset)
        volt = inv_off = 0
        samples = 3
        for num in range(samples):
            volt += self._ram_read('Voltage')
            i = (self._ram_read('InvOffset[MSB]') & 0xFF00) >> 8
            inv_off += _signed8bit(i)
            if num < (samples - 1):
                time.sleep(_ADC_DELAY)
        volt /= samples                                 # mVolt
        readings['PreVoltage'] = float(volt) / 1000     # Volt
        self._logger.debug('Voltage = %s', float(volt) / 1000)
        inv_off = int(inv_off / samples)
        readings['PreOff'] = inv_off
        self._logger.debug('inv_off = %s', inv_off)

        # Calculate new Scale and Offset
        new_off = ((adc_off_lsb - inv_off) & 0xFF)
        readings['PostOff'] = new_off
        self._logger.debug('new_off = %s', _signed8bit(new_off))
        new_off = new_off | adc_off_msb
        new_fsv = int(voltage / ((float(volt) / fsv) + (-inv_off / 32768.0)))
        readings['PostFSV'] = new_fsv
        self._logger.debug('new_fsv = %s', new_fsv)

        # Read & Restore LLE MSB
        lle = self._ram_read('LightLoadEst[MSB]')
        lle = (lle & 0xFF) | lle_msb
        # Write back LLE with MSB restored
        self._ram_write('LightLoadEst[MSB]', lle)

        # Write Calibration to RAM
        self._ram_write('AdcOffset[LSB]', new_off)
        self._ram_write('AdcVoltGain', new_fsv)
        if _WRITE_EE_AT_CAL:
            # Write Calibration to EEPROM
            self._ee_write((('EE-AdcOffset[LSB]', new_off),
                            ('EE-AdcVoltGain', new_fsv)))

        # Allow time for the new values to take effect
        time.sleep(_ADC_DELAY)
        # The BQ2060 seems to need about 1sec after the 1st read
        # for the read voltage to change
        # Here we do a dummy read...
        self._ram_read('Voltage')
        time.sleep(_ADC_DELAY)

        # Read Post-Calibration voltage reading
        readings['PostVoltage'] = (float(self._ram_read('Voltage')) /
                                   1000)  # Volt
        self._logger.debug('Voltage = %s', readings['PostVoltage'])
        return readings

    def cal_i(self, current):
        """Calibrate current measurement - Takes about 30sec to run.

        @param current Actual current measured externally (Amp)

        @return Dictionary of readings:
                    'PreCurrent',  'PostCurrent', 'Elapsed'

        """
        self._logger.debug('Actual Current = %s', current)
        current *= 1000     # convert to mAmp

        self._board_status()

        # Dictionary of readings to return
        readings = {}

        # Prepare
        self._ram_write('RemCapacity', 1000)
        adc_srg = self._ram_read('AdcResGain')
        self._logger.debug('adc_srg = %s', adc_srg)

        vfc_srg = _signed16bit(self._ram_read('VfcResGain'))
        self._logger.debug('vfc_srg = %s', vfc_srg)

        # Read and average some samples, _ADC_DELAYs apart (Current)
        curr = 0
        samples = 3
        for _ in range(samples):
            time.sleep(_ADC_DELAY)
            curr += self._ram_read('Current')
        curr /= samples                                 # mAmp
        curr = _signed16bit(int(curr))
        readings['PreCurrent'] = float(curr) / 1000     # Amp
        self._logger.debug('BQ Current = %s', readings['PreCurrent'])

        # SRG Init
        self._ram_write('VfcResGain', 1)
        time.sleep(_ADC_DELAY)

        # Read monitor value and wait for it to change
        mon = self._ram_read('Monitor')
        nextmon = mon
        while mon == nextmon:
            mon = self._ram_read('Monitor')
        nextmon = mon - 1
        if nextmon < 0:         # Handle unsigned int underflow
            nextmon = 0xFFFF

        # Start timing changes now
        start_time = datetime.datetime.now()

        # Wait for required number of changes
        changes = _CALI_VFC_TICKS
        self._logger.debug('Waiting for %s changes', changes)
        for _ in range(changes):
            reads = 0
            while mon != nextmon:
                mon = self._ram_read('Monitor')
                reads += 1
                if reads > _CALI_MAXREADS:
                    raise Ev2200Error('Monitor read timeout')
            nextmon = mon - 1
            if nextmon < 0:         # Handle unsigned int underflow
                nextmon = 0xFFFF

        # Calculate the elapsed time
        elapsed = datetime.datetime.now() - start_time
        elapsed = (float(elapsed.seconds) +
                   float(elapsed.microseconds) / 1000000)
        readings['Elapsed'] = elapsed
        self._logger.debug('Elapsed = %s', elapsed)

        # Calculate new calibration factors
        new_adc_srg = int((adc_srg * current) / curr)
        # abs(current) is used because the current polarity determines the
        # count direction. VFCSRG ends up as (409.6 / Rs), so it cannot be
        # a negative number.
        new_vfc_srg = int((abs(current) * elapsed * 18.204444) / changes)
        self._logger.debug('new_adc_srg = %s', new_adc_srg)
        self._logger.debug('new_vfc_srg = %s', new_vfc_srg)

        # Sanity check the calibration values
        if ((new_adc_srg < _ADC_MIN) or
                (new_adc_srg > _ADC_MAX) or
                (new_vfc_srg < _VFC_MIN) or
                (new_vfc_srg > _VFC_MAX)):
            raise Ev2200Error('Current/VFC calibration out of range')

        # Write Calibration to RAM
        self._ram_write('AdcResGain', new_adc_srg)
        self._ram_write('VfcResGain', new_vfc_srg)
        if _WRITE_EE_AT_CAL:
            # Write Calibration to EEPROM
            self._ee_write((('EE-AdcResGain', new_adc_srg),
                            ('EE-VfcResGain', new_vfc_srg)))

        # Allow time for the new values to take effect
        time.sleep(_ADC_DELAY)
        # The BQ2060 seems to need about 1sec after the 1st read for the
        # read voltage to change. Here we do a dummy read...
        self._ram_read('Current')
        time.sleep(_ADC_DELAY)

        # Read Post-Calibration current reading
        curr = self._ram_read('Current')
        curr = _signed16bit(curr)
        readings['PostCurrent'] = float(curr) / 1000  # Amp
        self._logger.debug('Current = %s', readings['PostCurrent'])
        return readings

    def sn_date(self, datecode, serialno):
        """Program SerialNo & Manufacturing Datecode into EEPROM.

        @param datecode ISO format date YYYY-MM-DD
        @param serialno Serial number (a 16-bit integer)

        @return EEPROM write retry count

        """
        self._board_status()
        pattern = ('^(20[0-9]{2})-([0][1-9]|[1][0-2])' +
                   '-(0[1-9]|[1-2][0-9]|3[0-1]$)')
        match = re.search(pattern, datecode)
        if not match:
            raise Ev2200Error('Invalid Date Code: ' + datecode)
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        dcword = ((year - 1980) << 9) | (month << 5) | day
        # BIT: 15 14 13 12 11 10 09 08 07 06 05 04 03 02 01 00
        #       Y  Y  Y  Y  Y  Y  Y  M  M  M  M  D  D  D  D  D

        pattern = '^[0-9]{1,5}$'
        match = re.search(pattern, serialno)
        if not match:
            raise Ev2200Error('Invalid Serial No: ' + serialno)
        sncode = int(serialno)
        if sncode > 65535:
            raise Ev2200Error('Serial No > 16-bit: ' + serialno)

        # Write Calibration to RAM
        self._logger.debug('ManufDate: %s, SerialNo: %s', dcword, sncode)
        self._ram_write('ManufDate', dcword)
        self._ram_write('SerialNo', sncode)
        # Write Calibration to EEPROM
        self._ee_write((('EE-ManufDate', dcword), ('EE-SerialNo', sncode)))

        return {'Retries': 0}

    def _ee_dump(self):
        """Dump all values from EEPROM.

        Prints a Hex and ASCII dump of the EEPROM contents to the console.

        @return Tuple of byte values

        """
        self._board_status()
        # Select the EEPROM
        self._logger.debug('Dumping EEPROM')
        self._ev_cmd('WrSMBusWordPEC', 'ManufAccess', _EE_CODE)
        time.sleep(_EE_POWERUP)
        self._ev_cmd('SetSMBusSlave', 'SetEE')
        # Read EEPROM value(s)
        vals = ()
        for ptr in range(0, 128, 2):
            val = self._ev_cmd('RdSMBusWord', bytes((ptr, )))
            vals += val[1],
            vals += val[2],
        # Select BQ2060
        self._ev_cmd('SetSMBusSlave', 'SetBQ')

        self._board_status()

        # Show a pretty display on the console
        for i in range(8):
            print('{0:04X}:'.format(16 * i), end=' ')
            msg = '  '
            for j in range(8):
                adr = 16 * i + j * 2
                loval = vals[adr]
                hival = vals[adr + 1]
                print('{0:02X} {1:02X}'.format(loval, hival), end=' ')
                char = chr(loval)
                dontprint = '\r\n\t\b'
                if (char not in string.printable) or (char in dontprint):
                    char = '.'
                msg += char
                char = chr(hival)
                if (char not in string.printable) or (char in dontprint):
                    char = '.'
                msg += char
                if j == 3:
                    print('', end=' ')
                    msg += ' '
            print(msg)

#        _dumper(vals)

        if _ZAP_EEPROM == 1:     # Erase Check bytes only
            self._ee_write((('EE-Check1', 0xFFFF), ('EE-Check2', 0xFFFF)))
        elif _ZAP_EEPROM == 2:   # Erase ALL bytes
            self._ee_wipe()
            raise Ev2200Error('Forced EE Wipe')

        return vals

    def _ee_wipe(self):
        """Wipe the entire EEPROM by writing to 0xFF."""
        self._logger.debug('Erasing EEPROM')
        self._ev_cmd('WrSMBusWordPEC', 'ManufAccess', _EE_CODE)
        time.sleep(_EE_POWERUP)
        self._ev_cmd('SetSMBusSlave', 'SetEE')
        for ptr in range(0, 128, 2):
            adr = bytes((ptr, ))
            self._ev_cmd('WrSMBusWord', adr, 0xFFFF)
            # Only delay at the end of each 8-byte page
            if (ptr > 0) and ((ptr + 2) % 8) == 0:
                time.sleep(_EE_DELAY)
            check = self._ev_cmd('RdSMBusWord', adr)
            check = (check[2] << 8) | check[1]
            if check != 0xFFFF:
                print('Verify error at', str(adr), str(check))
        # Select BQ2060
        self._ev_cmd('SetSMBusSlave', 'SetBQ')

    def _board_status(self):
        """Use EV2200 Echo command to detect EV2200.

        We send 3 x 0xFF, which should be echoed back as 3 x 0x00
        Query EV2200 Board Status.
        An automatic response status check will happen in _ev_cmd()

        """
        echo = self._ev_cmd('EchoBlock', 'Echo', 0xFFFF)
        if echo != b'\x00\x00\x00':
            raise Ev2200Error('Invalid echo reply')
        self._ev_cmd('BoardStatus', b'\x00')

    def _ram_read(self, subcmd):
        """Read value from BQ2060 RAM.

        @param subcmd Address

        @return 16-bit integer value

        """
        val = self._ev_cmd('RdSMBusWordPEC', subcmd)
        data = (val[2] << 8) | val[1]
        return data

    def _ee_read(self, rdparam):
        """Read value from EEPROM.

        @param rdparam Tuple of addresses

        @return Tuple of 16-bit integer values

        """
        # Select the EEPROM
        self._ev_cmd('WrSMBusWordPEC', 'ManufAccess', _EE_CODE)
        time.sleep(_EE_POWERUP)
        self._ev_cmd('SetSMBusSlave', 'SetEE')
        # Read EEPROM value(s)
        vals = ()
        for ptr in rdparam:
            subcmd = ptr
            val = self._ev_cmd('RdSMBusWord', subcmd)
            vals += (val[2] << 8) | val[1],
        # Select BQ2060
        self._ev_cmd('SetSMBusSlave', 'SetBQ')
        return vals

    def _ram_write(self, subcmd, val):
        """Write value to BQ2060 RAM.

        @param subcmd EV2200 Sub Command
        @param val Data value to write

        """
        self._ev_cmd('WrSMBusWordPEC', subcmd, val)

    def _ee_write(self, wrparam):
        """Write value to EEPROM.

        @param wrparam Tuple of tuples of (address, value)

        """
        # Select the EEPROM
        self._ev_cmd('WrSMBusWordPEC', 'ManufAccess', _EE_CODE)
        time.sleep(_EE_POWERUP)
        self._ev_cmd('SetSMBusSlave', 'SetEE')
        # Write value(s) to EEPROM
        for ptr in wrparam:
            subcmd = ptr[0]
            val = ptr[1]
            self._ev_cmd('WrSMBusWord', subcmd, val)
            time.sleep(_EE_DELAY)
        # Select BQ2060
        self._ev_cmd('SetSMBusSlave', 'SetBQ')

    def _ev_cmd(self, cmd, subcmd, val=0):
        """Send a command block.

        @param cmd Command name
        @param subcmd Sub-Command name (or address number)
        @param val 16-bit integer value to send

        @return 3-byte return string

        """
        # Check the subcmd. If its not in the SubCmd dictionary,
        # treat it as an address number
        scmd = _SUBCMD[subcmd] if subcmd in _SUBCMD else subcmd
        # Build the 5-byte command packet
        cmd_blk = (b'\xAA' +
                   _CMD[cmd] +
                   scmd +
                   bytes((val & 255, (val >> 8) & 255))
                   )
        self._ser.flushInput()
        self._ser.write(cmd_blk)
        res_blk = self._ser.read(5)   # this has a timeout

        # We should have got 5 bytes back
        if len(res_blk) != 5:
            raise Ev2200Error('Response timeout')

        # The 1st 2 bytes should always be what we sent
        if cmd_blk[:1] != res_blk[:1]:
            raise Ev2200Error('Reply != Command')

        lsb = res_blk[2]
        msb = res_blk[3]
        if (subcmd == 'WrSMBusWord' or
                subcmd == 'WrSMBusWordPEC' or
                subcmd == 'BoardStatus'):
            _ev_cmd_err(lsb, msb)
        elif (subcmd == 'RdSMBusWord' or
                subcmd == 'RdSMBusWordPEC'):
            if lsb != scmd:
                _ev_cmd_err(lsb, msb)

        return res_blk[2:]
