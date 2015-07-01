#!/usr/bin/python3
"""This program flashes the LPC parts via ISP through a serial port."""

import binascii
import re
import time
import logging

from . import device


# Serial encoding
_LANG = 'latin1'

# Dictionary of known LPC devices, indexed by the device's ID
_PART_TABLE = {
    0x1549: device.Lpc('LPC1549',
                      ramaddr=0x02000300,
                      sectorsize=(4096,) * 64,
                      uuencode=False),
    0x50080: device.Lpc('LPC1115',
                       ramaddr=0x10000300,
                       sectorsize=(4096,) * 16),
    # LPC1113 has 2 possible Device IDs...
    0x0434102B: device.Lpc('LPC1113',
                          ramaddr=0x10000300,
                          sectorsize=(4096,) * 6),
    0x2532102B: device.Lpc('LPC1113',
                          ramaddr=0x10000300,
                          sectorsize=(4096,) * 6),
    }


class CmdRespError(Exception):

    """Command response exception."""


class UuencodeError(Exception):

    """UUencode receive exception."""


class UnknownDeviceError(Exception):

    """Unknown device exception."""


class Programmer():

    """LPC Processor In-System-Programmer (ISP)."""

    def __init__(self, ser, bindata, erase_only, verify, crpmode):
        """Create the programmer.

        @param ser An opened serial port.
        @param bindata Bytearray of device data to program.
        @param erase_only True: Device should be erased only.
        @param verify True: Verify the programmed device.
        @param crpmode Code Protection:
                        True: ON, False: OFF, None: per 'bindata'.

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._ser = ser
        self._serecho = True
        self._bindata = bindata
        self._erase_only = erase_only
        self._do_verify = verify
        self._crpmode = crpmode
        self._device = None
        self.serialid = None
        if not erase_only:
            if not isinstance(bindata, bytearray):
                self._logger.error('bindata data must be a bytearray')
                raise TypeError
            # Test if bindata is a intel hex file
            # eg: :1000000000400002B50100002D020000D173000085
            if len(bindata) < 48:
                self._logger.error('No data read from file')
                raise TypeError
            if re.search('^:[0-9A-Fa-f]{10}', bindata[:48].decode(_LANG)):
                self._logger.error('File appears to be intel hex.' +
                    ' This program requires a binary file')
                raise TypeError

    def program(self):
        """Program a device."""
        # Synchronise with the device
        self._device = self._synchronize()
        # Erase all flash memory
        self._erase()
        if self._erase_only:
            return
        # Setup flash image data in device instance
        self._device.set_bindata(self._bindata)
        # Set the CRP value
        self._device.crp_update(self._crpmode)
        # Write data to device
        self._write()
        # Verify device
        if self._do_verify:
            self._verify()
        # Read device serial ID
        # After '0' response we should receive four integer strings
        self.serialid = self._cmdresp('N', '0', 4)
        # Convert 4 strings into 4 integers
        for i in range(0, 4):
            self.serialid[i] = int(self.serialid[i])

    def _synchronize(self):
        """Synchronize with the device to be programmed.

        When starting here we don't really know the state of the micro, it
        could be synchronized or not, if it is then echo could be enabled or
        disabled - we don't know for sure.

        @return LPC Device class instance.

        """
        self._serecho = True    # tells cmdresp() to read echo chars
        self._logger.info('Synchronizing...')
        try:
            self._cmdresp('?', 'Synchronized')
            # OK it wasn't synchronized but now it is so we know the serial
            # state at this point.
            self._cmdresp('Synchronized', 'OK')
            # this number is required but its value ignored
            self._cmdresp('12000', 'OK')
        except CmdRespError:
            # '?' Sync has failed.
            # OK we think its synchronized but don't know for sure if echo is
            # enabled or not. Try 4 times to get a response from enabling echo
            # so we start from a known state.
            sync = False
            for j in range(0, 4):
                try:
                    self._cmdresp('A 1', '0')
                    sync = True
                    break
                except CmdRespError:
                    pass
            if not sync:
                self._logger.error('Failed to synchronize')
                raise CmdRespError
        # Assume synchronized and echo is currently enabled. Turn off echo
        self._cmdresp('A 0', '0')
        # From here on the commands and binary data we send should not be
        # echoed any more.
        self._serecho = False # tells cmdresp() to not read echo any more
        self._logger.info('Synchronized')
        # Read the part id
        # After the '0' response we should receive one integer
        partid = self._cmdresp('J', '0', 1)
        try:
            device = _PART_TABLE[int(partid[0])]
        except KeyError:
            self._logger.error('Unhandled part identifier: %s', partid[0])
            raise UnknownDeviceError
        self._logger.info('Identified part as %s', device.name)
        return device

    def _erase(self):
        """Erase device.

        IMPORTANT Note: If CRP (Code Read Protect) is enabled on the chip then
        only a full erase is possible. Erasing anything less than all sectors
        will fail with code 19 being returned.
        For this reason we are erasing all flash sectors here to ensure this
        is not a problem.

        """
        self._logger.info('Erasing device')
        # unlock flash write commands
        self._cmdresp('U 23130', '0')
        last_sector = len(self._device.sectorsize) - 1
        # prepare all of flash for erase
        self._cmdresp('P 0 {}'.format(last_sector), '0')
        # erase all of flash
        self._cmdresp('E 0 {}'.format(last_sector), '0')

    def _write(self):
        """Write data to device."""
        self._logger.info('Programming device')
        ramaddr = self._device.ramaddr
        for sectornum, offset in self._device.sector_list():
            secsize = self._device.sectorsize[sectornum]
            secdata = self._device.bindata[offset:offset + secsize]
            # Blank check flash sector
            self._cmdresp('I {0} {0}'.format(sectornum), '0')
            # Write binary data for one sector into ram buffer
            self._cmdresp('W {} {}'.format(ramaddr, secsize), '0')
            if self._device.uuencode:
                self._send_uuencode_data(secdata)
            else:
                self._logger.debug(
                    'Sending {} bytes at binary file offset 0x{:08X}'.format(
                        secsize, offset))
                self._ser.write(secdata)
            # Prepare flash sector for writing
            self._cmdresp('P {0} {0}'.format(sectornum), '0')
            # Copy ram buffer to flash
            self._cmdresp('C {} {} {}'.format(offset, ramaddr, secsize), '0')
            if not self._device.uuencode:
                # Verify flash sector crc32
                # (Not all LPC parts have the 'S' command)
                try:
                    # after '0' response we should receive one integer
                    dev_crc32 = self._cmdresp('S {} {}'.format(
                        offset, secsize), '0', 1)
                    dev_crc32 = int(dev_crc32[0])
                except CmdRespError:
                    return # Assume there is no 'S' command
                ref_crc32 = binascii.crc32(secdata)
                if dev_crc32 != ref_crc32:
                    self._logger.error(
                        'Aborting because flash sector crc32 is {}'
                        ', should be {}'.format(dev_crc32, ref_crc32))
                    raise MemoryError

    def _verify(self):
        """Verify device programming.

        Read back the flash sectors we wrote and verify against bindata.

        """
        self._logger.info('Verifying device')
        bindata = self._device.bindata
        self._cmdresp('R 0 {}'.format(len(bindata), '0'))
        # Select the data read function to use
        if self._device.uuencode:
            func = self._receive_uuencode_data
        else:
            func = self._ser.read
        if func(len(bindata)) != bindata:
            self._logger.error('Flash verify failed')
            raise MemoryError
        self._logger.info('Flash verify OK')
        if self._device.uuencode:
            self._logger.info('Launching new application code')
            self._cmdresp('G 0 T', '0')

    def _cmdresp(self, cmd, *expect):
        """Command Response processor.

        @param cmd If cmd is None then no command is sent and only response
                    are read.
        @param expect expect[0] if supplied will be string compared against the
                      first response line.
                      expect[1] if supplied will be integer count of data
                      strings following expect[0].
        @raises CmdRespError on failure.
        @return A tuple of the data strings received, () if none.

        If self._serecho is True then we will expect each char of cmd sent out
        to be read back.

        """
        result = []
        count = -1
        necho = 0
        if cmd is not None:
            self._logger.debug('Command: %s', cmd)
            if cmd != '?':
                cmd += '\r\n'
                if self._serecho:
                    necho = len(cmd)
            self._ser.write(cmd.encode(_LANG))
            if necho > 0:
                # read in all the cmd chars sent out as echo
                x = self._ser.read(necho).decode(_LANG)
        # first time through its -1
        while count != 0:
            x = self._ser.readline(1000).decode(_LANG)
            while len(x) > 0:
                # Normally CRLF is received for line end, however in some cases
                # the last byte is corrupted 0x8A instead of 0x0A so here
                # accept both.
                if x[-1] not in '\r\n\x8A':
                    break
                x = x[:-1]
            if count == -1:
                # reading the response line
                count = 0
                if len(expect) > 0:
                    if len(expect[0]) > 0:
                        if expect[0] == x:
                            self._logger.debug('Success: %s', x)
                            if len(expect) > 1:
                                count = expect[1]
                        else:
                            self._logger.error('Failed: %s', x)
                            raise CmdRespError
                    else:
                        self._logger.debug('Response: %s', x)
                else:
                    self._logger.debug('Response: %s', x)
            else:
                # reading 1 or more data lines
                self._logger.debug('Data: %s', x)
                result.append(x)
                count -= 1
        return result

    def _send_uuencode_data(self, data):
        """Send UUencoded data to the device.

        @param data Data to be encoded and sent.

        <length><data><CR><LF>
        [... repeat for 1 to 20 of the above lines]
        <checksum><CR><LF>

        length:     One char with ascii value 32 plus the number of data bytes
                    encoded on line.
        data:       UUencode data bytes, 61 characters or 45 data bytes maximum
                    per line.
        checksum:   The sum of all the data bytes in decimal mod 256.

        After receiving this data block the controller will respond with one of
        the following:
            OK<CR><LF>
            RESEND<CR><LF>

        1. The data is subdivided into 3 byte groups forming a 24 bit stream.
        2. The 24 bit stream is then subdivided into 6 bit groups.
        3. A value of 0x20 is added to the 6 bit group.
        4. If a 6 bit group has a value of 0x00, a value of 0x60 is added.
        5. The number of data bytes is calculated and converted into its ASCII
           equivalent.
        If the number of bytes is not a multiple of three, 0x00 pad bytes are
        added to create a multiple of three.
        For instance, for a payload consisting of 4 bytes, two padded bytes are
        added to create a 6 byte payload.

        """
        data2 = data
        bytecount = len(data2)
        self._logger.info('Send %s bytes UUencoded', bytecount)
        while 0 != len(data2) % 3:
            data2 = data2 + b'\x00'
        checksum = 0
        linesout = 0
        while bytecount > 0 and len(data2) > 0:
            if bytecount > 45:  # length char
                line = '' + chr(45 + 32)
            else:
                line = '' + chr(bytecount + 32)
            # Max 61 characters per line
            while len(line) < (45 * 4) / 3 + 1 and len(data2) > 0:
                # Take 3 bytes of data to make 4 output chars
                checksum = checksum + data2[0] + data2[1] + data2[2]
                x = data2[0] << 16 | data2[1] << 8 | data2[2]
                for z in range(4):
                    y = (x >> (18 - z * 6)) & 0x3F
                    if 0 == y:
                        y += 0x60
                    else:
                        y += 0x20
                    line = line + chr(y)
                data2 = data2[3:]
                bytecount = bytecount - 3
            line = line + '\r\n'
            self._logger.debug('>>> ' + str(linesout) + ': ' + line)
            self._ser.write(line.encode(_LANG))
            time.sleep(0.05)
            linesout += 1
            if (0 == linesout % 20) or bytecount <= 0 or len(data2) <= 0:
                line = str(checksum) + '\r\n'
                self._logger.debug('>>> ' + line)
                self._ser.write(line.encode(_LANG))
                self._cmdresp(None, 'OK')
                checksum = 0

    def _receive_uuencode_data(self, count):
        """Receive UUencoded data from the device.

        @param count Expected number of data bytes.
        @return Data bytes.

        """
        self._logger.info('Receiving %s bytes UUencoded', count)
        data = []
        linesread = 0
        pat = re.compile(r'^[0-9]+$')
        while len(data) < count:
            x = self._ser.readline(1000).decode(_LANG)
            while len(x) > 0:
                if x[-1] != '\r' and x[-1] != '\n':
                    break
                x = x[:len(x) - 1]
            self._logger.debug("<<< %s: %s", linesread, x)
            m = len(x)
            if m < 5 or m > 61 or 0 != ((m - 1) % 4):
                self._logger.error(
                    'rx uuencode line length error len=%s: %s', m, x)
                raise UuencodeError
            n = ord(x[0]) - 32  # number of bytes encoded in this row
            if n < 1 or n > int((m - 1) / 4) * 3:
                self._logger.error(
                    'rx uuencode line syntax error len=%s bytes=%s: %s',
                    m, n, x)
                raise UuencodeError
            x = x[1:]
            m = int(n / 3)   # number of 4 char fields to decode
            if 0 != (n % 3):
                m += 1
            for j in range(m):
                # decode 4 chars into 3 bytes store in y
                y = 0
                for k in range(4):
                    y = y << 6
                    ch = ord(x[k])
                    # 0x20 not used and 0x60 means 0
                    if ch <= 0x20 or ch > 0x60:
                        self._logger.error('rx uuencode line range error')
                        raise UuencodeError
                    if 0x60 != ch:      # 0x60 means 0
                        y += (ch - 0x20)
                x = x[4:]
                # Append the 3 bytes just decoded from the 4 chars
                for k in range(3):
                    if 0 == n:
                        break
                    data.append((y >> (16 - k * 8)) & 255)
                    n -= 1
                if 0 == n:
                    break
            linesread += 1
            # read crc decimal number and ignore it
            if 0 == (linesread % 20) or len(data) >= count:
                x = self._ser.readline(1000).decode(_LANG)
                while len(x) > 0:
                    if x[-1] != '\r' and x[-1] != '\n':
                        break
                    x = x[:len(x) - 1]
                print('<<< ' + x)
                if None == re.search(pat,x):
                    self._logger.error(
                        'rx uuencode error reading checksum line')
                    raise UuencodeError
                self._logger.debug('>>> OK')
                self._ser.write(b'OK\r\n')
        return bytes(data)
