#!/usr/bin/env python3
"""Programmer module for P89LPC924 devices."""

import time
import serial
import logging


# Command data
_TYPE_READ_VERSION = 1

_TYPE_MISC_WRITE = 2
_DATA_STATUS_BIT_ZERO = '0300'
_DATA_STATUS_BIT_ONE = '0301'
# Retry counter for writing
_WRITE_MAX_RETRY = 5

_TYPE_MISC_READ = 3
_DATA_UCFG1 = '00'
_DATA_BOOT_VECTOR = '02'
_DATA_STATUS_BYTE = '03'
_DATA_MANUFACTURER = '10'
_DATA_DEVICE_ID = '11'
_DATA_DERIVATIVE_ID = '12'

_TYPE_ERASE = 4
_DATA_PAGE = '00'
_DATA_SECTOR = '01'

_TYPE_RESET_MCU = 8


def _checksum(buf):
    """Return a checksum for a given hex string."""
    cs = 0
    x = int(len(buf) / 2)
    for i in range(x):
        j = i + i
        cs = cs - int(buf[j:(j + 2)], 16)
    return cs % 256


ERR_PORT = 1
ERR_TIMEOUT = 2
ERR_CHECKSUM = 3


class ISPError(Exception):

    """ISP exception class."""

    def __init__(self, code, message):
        """Create error."""
        super().__init__()
        self.code = code
        self.message = message

    def __str__(self):
        """Display error summary.

        @return error message

        """
        return ('Error {0.code}, {0.message}').format(self)


class P89LPC924():

    """P89LPC924 In-System-Programming (ISP) interface."""

    def __init__(self, port=0, baud=9600, timeout=1.0):
        """Open serial port to device.

        Sends a 'U' twice to the ISP firmware to establish the baud rate.

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        ser = serial.Serial(port)
        self._logger.info('Opened "%s" at %sBd', ser.name, baud)
        self.ser = ser
        ser.baudrate = baud
        ser.parity = serial.PARITY_NONE
        ser.timeout = timeout
        self._logger.debug('ISP Baud rate detect')
        ser.flushInput()
        ser.flushOutput()
        for i in range(5):
            ser.write(b'U')
            reply = ser.read()
            self._logger.debug('Try %s: %s', i, reply)
            self.ser.flushInput()
            if reply == b'U':
                break
        msg = None
        if len(reply) == 0:
            msg = 'Timeout'
        elif reply != b'U':
            msg = 'Bad response'
        if msg:
            self._logger.debug('%s> %s', msg, reply)
            raise ISPError(ERR_TIMEOUT, msg)
        else:
            self._logger.debug('Connected')

    def _build_hex_record(self, addr, type, data):
        """Return an Intel Hex record from the given parameters.

        addr: Address of first data byte in the record
        type: Specifies function to be performed
        data: String of data bytes in the record

        """
        nbytes = len(data) / 2
        form = '%02X%04X%02X%%0%dX' % (nbytes, addr, type, (2 * nbytes))
        b = form % int(data, 16)
        record = ':' + b + ('%02X' % _checksum(b))
        return record

    def write_hex_record(self, record):
        """Write single Hex record to ISP firmware.

        Returns a value if available.
        If a checksum error occurs, the operation indicated by the record type
        is not performed.
        Retries in case of checksum error.

        """
        self._logger.debug('Hex record> %s', record)
        ser = self.ser
        ser.flushInput()
        record_data = record.encode()
        ser.write(record_data)
        reply = b'X'
        count = 0
        while reply[-1] != ord('.') and count < _WRITE_MAX_RETRY:
            reply = ser.readline()
            # Remove \r\n
            reply = reply[:-2]
#            self._logger.debug('Reply: %s', reply)
            if reply[-1] == ord('X'):
                self._logger.debug('Checksum error')
                ser.flushInput()
                ser.write(record_data)
                count += 1
        if count == _WRITE_MAX_RETRY:
            msg = 'Write failed'
            self._logger.debug(msg)
            raise ISPError(ERR_CHECKSUM, msg)
        else:
            n = len(record)
            m = len(reply)
            ser.flushInput()
            return reply[n:m - 1]

    def read_device_id(self):
        """Read Device ID.

        @return Device ID

        """
        record = self._build_hex_record(
            addr=0, type=_TYPE_MISC_READ, data=_DATA_DEVICE_ID)
        value = self.write_hex_record(record)
        self._logger.debug('Device ID> %s', value)
        return value

    def read_status_byte(self):
        """Read Status Byte.

        @return Status Byte

        """
        record = self._build_hex_record(
            addr=0, type=_TYPE_MISC_READ, data=_DATA_STATUS_BYTE)
        value = self.write_hex_record(record)
        self._logger.debug('Boot Status Byte> %s', value)
        return value

    def read_boot_vector(self):
        """Read Boot Vector.

        @return Boot Vector

        """
        record = self._build_hex_record(
            addr=0, type=_TYPE_MISC_READ, data=_DATA_BOOT_VECTOR)
        value = self.write_hex_record(record)
        self._logger.debug('Boot Vector> %s', value)
        return value

    def read_UCFG1_register(self):
        """Read UCFG1 Register.

        @return Register value

        """
        record = self._build_hex_record(
            addr=0, type=_TYPE_MISC_READ, data=_DATA_UCFG1)
        value = self.write_hex_record(record)
        self._logger.debug('UCFG1 Register> %s', value)
        return value

    def write_UCFG1_register(self, value):
        """Write UCFG1 Register.

        @return Written value

        """
        record = self._build_hex_record(
            addr=0, type=_TYPE_MISC_WRITE, data=_DATA_UCFG1 + value)
        self.write_hex_record(record)
        self._logger.debug('UCFG1 Register> %s', value)
        return value

    def write_status_bit_zero(self):
        """Write_Boot Status Bit Zero.

        Power-up execution starts at location 0000H after reset.

        """
        record = self._build_hex_record(
            addr=0, type=_TYPE_MISC_WRITE, data=_DATA_STATUS_BIT_ZERO)
        self.write_hex_record(record)
        self._logger.debug('Boot Status Bit programmed to zero.')

    def write_status_bit_one(self):
        """Write_Boot Status Bit One.

        Power-up execution starts at bootloader location 0F0H  after reset.

        """
        record = self._build_hex_record(
            addr=0, type=_TYPE_MISC_WRITE, data=_DATA_STATUS_BIT_ONE)
        self.write_hex_record(record)
        self._logger.debug('Boot Status Bit programmed to one.')

    def write_hex_file(self, fname):
        """Send all records from a given Hex file to the ISP firmware."""
        f = open(fname, 'r')
        for record in f.readlines():
            self.write_hex_record(record[:-1])
            time.sleep(0.01)                    # wait between lines

    def erase_page(self, start_addr):
        """Erase a page (64 bytes) from program memory."""
        record = self._build_hex_record(
            addr=0, type=_TYPE_ERASE, data=_DATA_PAGE + start_addr)
        self.write_hex_record(record)
        self._logger.debug('Page erased (Start address> %s)', start_addr)

    def erase_sector(self, start_addr):
        """Erase a sector (1024 bytes) from program memory."""
        record = self._build_hex_record(
            addr=0, type=_TYPE_ERASE, data=_DATA_SECTOR + start_addr)
        self.write_hex_record(record)
        self._logger.debug('Sector erased (Start address> %s)', start_addr)

    def reset_mcu(self):
        """Reset MCU."""
        self.write_hex_record(':00000008F8')
        self._logger.debug('MCU Reset')

    def close(self):
        """Close serial port."""
        self.ser.close()
        self._logger.info('Closed')
