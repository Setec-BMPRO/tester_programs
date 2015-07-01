#!/usr/bin/python3
"""LPC device definition."""

import logging
import struct


class Lpc():

    """Definition of a LPC device.

    Manages the device memory location and sizes and to store the data image
    for programming.
    Updates the CRP (Code Read Protect) mode bytes, and the Interrupt vector
    table in the data image.
    Generates the sector list for device programming.

    """

    def __init__(self, name, ramaddr, sectorsize,
                 uuencode=True,
                 crp_adr=0x000002FC,
                 crp_disable=struct.pack('<I', 0xFFFFFFFF),
                 crp_enable=struct.pack('<I', 0x87654321)):
        """Create a device type instance.

        @param name Name for display purposes only.
        @param ramaddr RAM address to buffer one flash sector.
        @param sectorsize Flash sector sizes and count.
        @param uuencode True the flash data transfer is uuencode.
        @param crp_adr Code Read Protect address.
        @param crp_disable CRP disable value.
        @param crp_enable CRP enable value.

        """
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self.name = name
        self.ramaddr = ramaddr
        self.sectorsize = sectorsize
        # Calculate flash memory size in bytes
        self.flash_size = 0
        for sector in sectorsize:
            self.flash_size += sector
        self.uuencode = uuencode
        self.crp_adr = crp_adr
        self.crp_disable = crp_disable
        self.crp_enable = crp_enable
        self.bindata = None
        self._programsectors = None

    def set_bindata(self, bindata):
        """Set binary data image for the device.

        @param bindata Bytearray of device data.
        The data is padded with 0xFF to fill the last flash sector.

        """
        self._logger.info('Set binary data image')
        # Will the data fit into the device?
        if len(bindata) > self.flash_size:
            msg = 'File is larger than flash memory'
            self._logger.error(msg)
            raise TypeError(msg)

        # Calculate number of flash sectors required
        j = len(bindata)
        programsectors = 0
        while j > 0 and programsectors < len(self.sectorsize):
            programsectors += 1
            j = j - self.sectorsize[programsectors]
        self._programsectors = programsectors
        if j < 0:
            # Padding is required to fill last flash sector
            j = -j
            self._logger.debug('Padding with %s 0xFF bytes in last sector', j)
            bindata.extend(b'\xFF' * j)
        else:
            self._logger.debug('Padding is not required')

        self._logger.info(
            'Updating interrupt vector checksum at flash offset 0x1C-1F')
        # Add up first 7 32-bit vectors
        vectors = struct.unpack('<7I', bindata[:0x1C])
        xsumvector = 0
        for vec in vectors:
            xsumvector = (xsumvector + vec) & 0xFFFFFFFF
        # Compute 32-bit 2s complement of the sum so first 8 vectors sum to 0
        if xsumvector > 0:
            xsumvector = 0x100000000 - xsumvector
        # Convert xsumvector to 4 bytes little endian and overwrite 0x1C-1F
        bindata[0x1C:0x20] = struct.pack('<I', xsumvector)
        self.bindata = bindata

    def crp_update(self, crpmode):
        """Update CRP values in data image.

        @param crpmode Code Protection:
                True: ON, False: OFF, None: leave per 'bindata'.

        """
        # Get 4 byte value for the CRP mode, modify if required
        crpvalue = self.bindata[self.crp_adr:self.crp_adr + 4]
        if crpmode is None:
            self._logger.debug(
                'Leaving current CRP mode 0x{:08X}: 0x{:08X}'.format(
                    self.crp_adr,
                    struct.unpack('<I', crpvalue)[0]))
        else:
            if crpmode:
                crp_new = self.crp_enable
                self._logger.debug(
                    'Enabling CRP mode 0x{:08X}: 0x{:08X} -> 0x{:08X}'.format(
                        self.crp_adr,
                        struct.unpack('<I', crpvalue)[0],
                        struct.unpack('<I', crp_new)[0]))
            else:
                crp_new = self.crp_disable
                self._logger.debug(
                    'Disabling CRP mode 0x{:08X}: 0x{:08X} -> 0x{:08X}'.format(
                        self.crp_adr,
                        struct.unpack('<I', crpvalue)[0],
                        struct.unpack('<I', crp_new)[0]))
            # Update bindata with new 4 byte CRP value
            self.bindata[self.crp_adr:self.crp_adr + 4] = crp_new

    def sector_list(self):
        """Calculate sector write list.

        Build a (sector,offset) array so that the first flash sector
        is programmed last
        @return List of Tuple of (sector, offset).

        """
        self._logger.info('Generating programming sector list')
        sectorlist = []
        offset = self.sectorsize[0] # offset of the 2nd flash sector
        for sectornum in range(1, self._programsectors):
            sectorlist.append((sectornum, offset))
            offset = offset + self.sectorsize[sectornum]
        sectorlist.append((0, 0)) # first sector #0 at offset 0 done last
        return sectorlist
