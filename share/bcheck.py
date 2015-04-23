#!/usr/bin/env python3
"""Panasonic BT Radio interface."""

import logging
import serial
import time
import sys
import re
try:
    import json
    assert json
except ImportError:
    import simplejson as json

_LANG = 'latin1'


class BtCheck(object):

    """BT Radio interface functions."""

    def __init__(self, port=None):
        """Create."""
        self._logger = logging.getLogger(
            '.'.join((__name__, self.__class__.__name__)))
        self._port = port
        self._ser = None
        self._mac = None
        self._pin = None
        self._serial = None

    def _log(self, data):
        """Print logging statements after removing <CR><LF>."""
        if len(data) >= 2 and data[-2:] == '\r\n':
            self._logger.debug(data[:len(data)-2])
        else:
            self._logger.debug(data)

    def serflush(self):
        """Flush the serial buffer."""
        if self._ser is None:
            return
        while True:
            x = self._ser.read(1000).decode(_LANG)
            if not x:
                break
            self._log('flushing serial rx:{}'.format(x))
        self._ser.flushInput()
        self._ser.flushOutput()

    def btcmdresp(self, cmd):
        """Send command to modem.

        @return response

        """
        self.serflush()
        if cmd == '^^^':
            self._log('Leaving streaming mode, sending escape sequence')
            time.sleep(1)  # need long guard time before first letter
            for x in range(0, 3):
                sys.stdout.write('^')
                sys.stdout.flush()
                time.sleep(0.2)  # need short guard time between letters
                self._ser.write(b'^')
        else:
            self._log('Sending command:{}'.format(cmd))
            self._ser.write(cmd.encode(_LANG) + b'\r\n')
        line = self._ser.readline().decode(_LANG)
        self._log('Readline:{}'.format(line))
        # request for firmware version returns only simple integer
        if cmd == 'AT+JRRI':
            if re.search('^[0-9]+\r\n$', line):
                return True
            return False
        # all other requests return OK,
        # or ROK if AT+JRES and after hardware reset
        if re.search('^R?OK\r\n$', line):
            return True
        return False

    def btopen(self):
        """Open communications with BT Radio.

           Open the serial port if not open.
           Software reset.
           Enable security.

        """
        self._logger.debug('Open')
        try:
            if self._ser is None:
                self._ser = serial.Serial(
                    port=self._port, baudrate=115200,
                    timeout=2, writeTimeout=10, rtscts=True)
            time.sleep(1)
            self.serflush()
            for retry in range(0, 5):
                if not self.btcmdresp('AT+JRES'):  # reset
                    time.sleep(2)
                    continue
                if not self.btcmdresp(
                        'AT+JSEC=4,1,04,1111,2,1'):  # security mode
                    time.sleep(2)
                    continue
                break
        except:
            self._ser = None
            raise

    def btpin(self, name):
        """Generate pin from serial.

        @return PIN number

        """
        if len(name) != 11:
            return None
        HASH_START, HASH_MULT = 56210, 29
        pin = HASH_START
        for c in name:
            pin = ((pin * HASH_MULT) & 0xFFFF) ^ ord(c)
        pin = "%04d" % (pin % 10000)
        return pin

    def btscan(self, serial):
        """Scan for bluetooth devices.

           Returns true if a match with "serial" is found, else returns false

        """
        self._log('Scanning for serial {}'.format(serial))
        self._serial = serial
        if self._ser is None:
            return False
        for retry in range(0, 5):
            if self.btcmdresp("AT+JDDS=0"):  # start device scan
                break
            if retry == 4:
                return False
        # Read responses until completed.
        for retry in range(0, 20):
            line = self._ser.readline().decode(_LANG)
            self._log('Readline:{}'.format(line))
            if len(line) <= 2:
                continue
            if line == "+RDDSCNF=0\r\n":   # no more responses
                break
            match = re.search('^\+RDDSRES=([0-9A-F]{12}),BCheck ([^,]*),.*',
                              line)
            if match:
                data = match.groups()
                if len(data) >= 2:
                    pin = self.btpin(data[1])
                if self._serial == data[1]:
                    self._log('Serial number match found:{}'.format(data[1]))
                    self._mac = data[0]
                    self._pin = pin
        if self._mac:
            return True
        else:
            return False

    def btpair(self):
        """Pair with bluetooth device.

        @return True upon success

        """
        self._log('Pairing with mac {}'.format(self._mac))
        if not self.btcmdresp('AT+JCCR=' + self._mac + ',01'):
            return False
        for retry in range(0, 10):
            line = self._ser.readline().decode(_LANG)
            self._log('Readline:{}'.format(line))
            if len(line) <= 2:
                continue
            # device we are pairing to has asked for a pin code
            if line[:6] == '+RPCI=':
                self._log('Sending pin code:{}'.format(self._pin))
                if not self.btcmdresp('AT+JPCR=04,' + self._pin):
                    self._log('Sending pin code failed')
                    return False
                continue
            # device we are pairing to has asked to verify 6 digit id
            if line[:6] == '+RUCE=':
                self._log('Sending confirmation')
                if not self.btcmdresp('AT+JUCR=1'):
                    self._log('Sending confirmation failed')
                    return False
                continue
            # Example of good pairing response: '+RCCRCNF=500,0000,0\r\n'
            # The first 500 is MTU and is 000 on error.
            # The ',0' on the end means good status and ',1' would be an error.
            if line[:9] == '+RCCRCNF=':
                match = re.search('^\+RCCRCNF=([1-9][0-9]{2}),' +
                                  '([0-9]{4}),([0-9])\r\n$', line)
                if not match:
                    continue
                data = match.groups()
                if len(data) < 3:
                    continue
                mtu = int(data[0])
                if mtu == 500:
                    self._log('Now Paired, MTU {} bytes.'.format(mtu))
                    return True
                self._log('Pairing failed.')
                continue
        self._log('No more retries')
        return False

    def btunpair(self):
        """Unpair with bluetooth device.

        @return False

        """
        self._log('Unpairing')
        if not self.btcmdresp('AT+JSDR'):
            return False
        for retry in range(0, 10):  # about 20s due to 2s serial rx timeout
            time.sleep(2)
            line = self._ser.readline().decode(_LANG)
            if len(line) <= 2:
                continue
            self._log('Readline:{}'.format(line))
            if line == "+RDII\r\n":    # good unpairing response
                self._log('Now Un-Paired.')
                return True
        self._log('Unpairing timed out, try btopen() to reset' +
                  ' bluetooth tranciever.')
        return False

    def btcon(self):
        """Enter streaming data mode.

        @return True upon success

        """
        self._log('Entering streaming mode')
        if not self.btcmdresp('AT+JSCR'):
            return False
        return True

    def btesc(self):
        """Escape from streaming data mode back to command mode.

        @return True upon success

        """
        if not self.btcmdresp('^^^'):
            return False
        return True

    def btinfo(self):
        """Get information from the bluetooth device.

        @return Data, or False upon failure

        """
        if self._ser is None:
            return False
        # {"jsonrpc":"2.0","id":8256,"result":{"HardwareVersion":"2.0",
        #             "SoftwareVersion":"1.3.3190","SerialID":"A1415030099"}}
        for retry in range(0, 5):
            cmd = ('{"jsonrpc": "2.0", "method": "GetSystemInfo",' +
                   ' "params": {}, "id": 8256}')
            self._log('sending command to get system info...')
            self._log(cmd)
            self.serflush()
            self._ser.write((cmd + '\r').encode(_LANG))
            line = self._ser.readline().decode(_LANG)
            if len(line) > 0:
                self._log('Readline:{}'.format(line))
                data = json.loads(line)     # Convert string to dictionary
                return data['result']
            self._log("bad response getting device info")
            time.sleep(1)
        return False

    def btclose(self):
        """Close serial communications with BT Radio."""
        self._logger.debug('Close')
        if self._ser is None:
            return
        try:
            self._ser.setRtsCts(False)   # so close() does not hang
            self._ser.flushInput()
            self._ser.flushOutput()
            self._ser.close()
            self._ser = None
        except Exception:
            pass

#def _ForceBags(obj):
#    """Converts to Bags recursively."""
#    if type(obj) is dict:
#        b = Bag()
#        for k, v in obj.items():
#            b[str(k)] = _ForceBags(v)
#        return b
#    elif type(obj) in (list, tuple):
#        return [_ForceBags(x) for x in obj]
#    else:
#        return obj
#
#
#class Bag(dict):
#
#    """Convert a json string to a dictionary."""
#
#    def __getattr__(self, k):
#        try:
#            return self[k]
#
#        except KeyError:
#            raise AttributeError('No such attribute %r' % k)
#
#
#    # convert JSON to dict
#    @staticmethod
#    def FromJSON(s):
#        if sys.version_info < (2, 6):
#            return _ForceBags(json.read(s))
#        else:
#            return _ForceBags(json.loads(s))
#
#    # convert dict to JSON
#    @staticmethod
#    def ToJSON(d):
#        if sys.version_info < (2, 6):
#            return str(d)
#        else:
#            return json.dumps(d, sort_keys=False, indent=4)
#
#
## change serial port path
#def btserial(*newserial):
#    global ser, mac, serialport, maclist
#    if len(newserial) >= 1:
#        if len(newserial[0]) == 0:
#            return ''
#        serialport=newserial[0]
#    return serialport
#
#
#
## change mac
#def btmac(*newmac):
#    global mac
#    if len(newmac) >= 1:
#        if len(newmac[0]) != 12 and len(newmac[0]) != 0:
#            print('mac must be 12 chars long')
#            return ''
#        mac=newmac[0]
#    return mac
#
#def btname(*newname):
#    global name
#    if len(newname) >= 1:
#        if 11 != len(newname[0]) and 0 != len(newname[0]):
#            print('name must be 11 chars long, got '+newname[0])
#            return ''
#        if 0 != len(newname[0]):
#            if not re.search('^A[0-9]{10}$', newname[0]):
#                print('name must be in format of AXXXXXXXXXX where X is a decimal digit, got '+newname[0])
#                return ''
#        name=newname[0]
#    return name
#
#
## this one verify that mac is discovered and retry until it is
#def btscanv():
#    if len(mac) > 0:
#        for retry in range(0,5):
#            if not btscan():
#                return False
#            try:
#                name = maclist[mac][0]
#                pin = maclist[mac][1]
#            except KeyError:
#                print('mac ' + mac + ' not discovered, scanning again')
#                continue
#            print('discovered mac=' + mac + ' name=' + name + ' pin=' + pin)
#            return True
#    return False
#
#
#def bttestjson():
#    print('[]')
#    ser.write(b'[]\r')
#    while True:
#        try:
#            x=ser.readline().decode(LANG)
#        except:
#            print('ERROR ser.readline():', sys.exc_info())
#            return False
#        if len(x) != 0:
#            btprint(x)
#            break
#    return True
#
#
#def btlog():
#    global ser
#    # {"Timestamp":271,"Message":"{"jsonrpc": "2.0", "method": "GetLogBaseAddress", "params": {}, "id": 11}"},
#    if None == ser:
#        return False
#    serflush()
#    try:
#        ser.write(b'{"jsonrpc": "2.0", "method": "GetLogBaseAddress", "params": {}, "id": 11}\r')
#        res=ser.readline().decode(LANG)
#    except:
#        print('ERROR Unable to complete:', sys.exc_info())
#        res=''
#    if len(res)==0:
#        print("bad response getting base address")
#        return False
#    response_baseaddress = Bag.FromJSON(res)
#    baseaddress=response_baseaddress.result.BaseAddress
#    output=[]
#    recordindex=0
#    count=0
#    index=0
#    while True:
#        try:
#            ser.write(('{"jsonrpc": "2.0", "method": "GetLogRecord", "params": {"BaseAddress":%u, "RecordIndex": %d}, "id": 222}\r' % ( baseaddress, recordindex )).encode(LANG))
#            res=ser.readline().decode(LANG)
#        except:
#            print('ERROR Unable to complete:', sys.exc_info())
#            res=''
#        if len(res)==0:
#            print("bad response getting record")
#            return False
#        try:
#            record=Bag.FromJSON(res)
#            itemcount=record.result.ItemCount
#            if (itemcount==0):
#                break
#            j=0
#            for item in record.result.Items:
#                output.append("%06d " % (count+itemcount-j-1) + str(item.Timestamp) + ' ' + item.Message)
#                j=j+1
#            count=count+j
#        except:
#            print('ERROR Unable to complete:', sys.exc_info())
#            output.append("%06d " % count + res)
#            count=count+1
#
#        recordindex=recordindex+1
#    output.sort(reverse=True)
#    for msg in output:
#        print(msg[7:])
#    return True
#
#
#def btupload():
#    global ser
#    if None == ser:
#        return False
#    # {"jsonrpc":"2.0","id":3,"result":{"Comment":"Upload new code."}}
#    retry = 0
#    while True:
#        retry = retry + 1
#        if retry > 5:
#            return False
#        cmd='{"jsonrpc": "2.0","method":"CommencifyCommand","params":{"Command":"Upload"},"id": 3}'
#        print('sending command to upload firmware...')
#        print(cmd)
#        try:
#            serflush()
#            ser.write((cmd + '\r').encode(LANG))
#            res=ser.readline().decode(LANG)
#        except:
#            print('ERROR Unable to complete:', sys.exc_info())
#            res=''
#        if len(res) > 0:
#            print('response...')
#            print(res)
#            # {"jsonrpc":"2.0","id":3,"result":{"Comment":"Upload new code."}}
#            response = Bag.FromJSON(res)
#            try:
#                if response.result.Comment == 'Upload new code.':
#                    break
#            except:
#                True
#        print("bad response setting upload")
#        time.sleep(1)
#    return True
#
#
#
#def btlpc(*binfilearg):
#    binfilepath='.'
#    binfile=''
#    if len(binfilearg) == 0:
#        binfiles=[]
#        for f in listdir(binfilepath):
#            fn=join(binfilepath,f)
#            if not isfile(fn):
#                continue
#            if not fn.endswith('.bin'):
#                continue
#            binfiles.append(fn)
#        if len(binfiles) == 0:
#            print('no binfile found')
#            return False
#        binfiles.sort(reverse=True)
#        binfile=binfiles[0]
#    else:
#        binfile=binfilearg[0]
#    cmd='isplpc.py "%s" "%s"' % (serialport, binfile)
#    print('Running: ' + cmd)
#    res=os.system(cmd)
#    if res == 0:
#        print('lpc21isp returned success')
#        return True
#    print('lpc21isp returned failure: ', res)
#    return False
#
#
#
#def btid(newid):
#    global ser
#    if None == ser:
#        return False
#    retry = 0
#    while True:
#        retry = retry + 1
#        if retry > 5:
#            return False
#        cmd='{"jsonrpc": "2.0","method":"CommencifyCommand","params":{"Command":"DebugConsole"},"id": 3}'
#        print("sending command to enter debugconsole...")
#        print(cmd)
#        try:
#            serflush()
#            ser.write(('\r' + cmd + '\r').encode(LANG))
#            res=ser.readline().decode(LANG)
#        except:
#            print('ERROR Unable to complete:', sys.exc_info())
#            res=''
#        if len(res) > 0:
#            print('response...')
#            print(res)
#            break
#        print("bad response setting debugconsole try " + str(retry))
#        time.sleep(2)
#    time.sleep(2)
#    serflush()
#    ser.write(b'\r')
#    res=ser.read(1000).decode(LANG)
#    debugcommand=newid
#    if len(newid) == 11 and newid[0:1] == 'A':
#        j=0
#        for x in newid[1:]:
#            if x in '0123456789':
#                j=j+1
#            else:
#                j=0
#                break
#        if j==10:
#            debugcommand='%d unlock set-serial-id %s nv-write' % (0xdeadbea7, newid)
#    for cmd in ( debugcommand, 'RESTART' ):
#        if len(cmd) == 0:
#            continue
#        print("sending debugconsole command one char at a time...")
#        print(cmd)
#        for c in cmd:
#            retry = 0
#            while True:
#                retry = retry + 1
#                if retry > 10:
#                    print('')
#                    print('failed getting echo from debugconsole')
#                    return False
#                ser.write(c.encode(LANG))
#                res=ser.read(1).decode(LANG) # read 1 char with 2 second timeout
#                if len(res) > 0:
#                    sys.stdout.write(c)
#                    sys.stdout.flush()
#                    if c==res:
#                        break
#                else:
#                    sys.stdout.write('.')
#                    sys.stdout.flush()
#        serflush()
#        ser.write(b'\r')
#        res=ser.read(1000).decode(LANG) # read all with 2 second timeout
#        if len(res) == 0:
#            serflush()
#            ser.write(b'\r')
#            res=ser.read(1000).decode(LANG) # read all with 2 second timeout
#        print('')
#        print('response...')
#        print(res)
#        print('')
#        if len(res) == 0:
#            print('failed getting debugconsole prompt')
#            return False
#    return True
#
#
#def btuploadwrap():
#    global name,ser, mac, serialport, maclist
#    for retry in range(0,5):
#        if not btscanv():
#            return False
#
#        try:
#            name = maclist[mac][0]
#            pin = maclist[mac][1]
#        except KeyError:
#            print('mac not discovered, scanning again')
#            continue
#
#        if not re.search('^A[0-9]{10}$', name):
#            print('invalid name: ' + name)
#            return False
#
#        if not re.search('^[0-9]{4}$', pin):
#            print('invalid pin: ' + pin)
#            return False
#
#        if btpair(): # pair with global mac
#            break    # success, serial port is still open
#
#        if retry == 4:
#            return False
#
#        print('sleep(1)')
#        time.sleep(1)
#
#    if not btcon():
#        return False
#
#    #this command resets the remote bluetooth radio when completes successfully
#    if not btupload():
#        return False
#
#    btesc()
#    if not btopen():
#        return False
#
#    #this sleep waits for the radio to notice the device has reset and unpaired itself
#    print('sleep(3)')
#    time.sleep(3)
#    return True
#
#
#def btburn():
#    if not btscanv():
#        return False
#
#    if not btpair():
#        return False
#
#    if not btcon():
#        return False
#
#    print('sleep(3)')
#    time.sleep(3)
#
#    btclose()
#
#    #the external lpc program resets the remote bluetooth radio when completes successfully
#    #call btlpc() while in the connected streaming state
#    ntries = 4
#    for retry in range(0,ntries):
#        if btlpc():
#            break
#        if retry == ntries-1:
#            return False
#
#    if not btopen_no_reset():
#        return False
#
#    btesc()
#
#    if not btopen():
#        return False
#
#    #this sleep waits for the radio to notice the device has reset and unpaired itself
#    print('sleep(3)')
#    time.sleep(3)
#    return True
#
#
#def btburnid():
#    global name, ser
#    if re.search('^A[0-9]{10}$', name):
#        #
#        # program BCheck serial id
#        #
#        if None==ser:
#            if not btopen():
#                print('btburnid failed opening serial port')
#                return False
#
#        if not btscanv():
#            print('btburnid failed btscanv')
#            return False
#
#        if not btpair('8850'):  # try 8850 pin first, then will try calculated pin from btscan()
#            print('btburnid failed pairing')
#            return False
#
#        if not btcon():
#            print('btburnid failed switching to stream mode')
#            return False
#
#        # sleep a little because embedded is querying the mac of who just connected at this point
#        print('sleep(4)')
#        time.sleep(4)
#
#        if not btid(name):
#            return False
#
#        btesc()
#
#        if not btopen():
#            return False
#
#        if not btscanv():
#            return False
#
#        if not btpair():
#            return False
#
#        if not btcon():
#            return False
#
#        # sleep a little because embedded is querying the mac of who just connected at this point
#        print('sleep(4)')
#        time.sleep(4)
#
#        if not btinfo():
#            return False
#
#        if btesc():
#            btunpair()
#
#    else:
#        print('Not setting BCheck serial id because its invalid: ' + name)
#        return False
#    return True
#
#
#def btprogram():
#    global mac
#    print('programming mac: ' + mac)
#
#    if not btopen():
#        return False
#
#    if True:
#        #
#        # Put Bcheck into program flash mode, must be flashing green LED
#        #
#        if not btuploadwrap():
#            #Shlomi - instead of bailing, see if maybe we are already in blinking white mode
#            print('Failed putting into upload mode, trying to program anyway')
#            btesc()
#            btunpair()
#            btopen()
#            return False
#
#    if True:
#        #
#        # program flash, must already be flashing white LED
#        #
#        if not btburn():
#            return False
#
#    if True:
#        if not btburnid():
#            return False
#    return True
#
#
#
#def btprogramid():
#    mname=''
#    for retry in range(0,5):
#        while True:
#            if re.search('^A[0-9]{10}$',mname):
#                break
#            mname = input('Enter AXXXXXXXXXX identifier:')
#        if None == ser:
#            if not btopen():
#                break
#        if not btscan():
#            break
#        for mac in maclist:
#            if mname == maclist[mac][0]:
#                btmac(mac)
#                return btprogram()
#    print('Did not discover serial ID: ' + mname)
#    return False
#
#
#
#def btprogramwl():
#    whitelist=[]
#    f=open('whitelist.txt','rt')
#    while True:
#        x=f.readline()
#        if not x:
#            break
#        whitelist.append(x[:11])
#    f.close()
#    btopen()
#    btscan()
#    for x in maclist:
#        if maclist[x][0] in whitelist:
#            btmac(x)
#            print(btmac())
#            return btprogram()
#    return False
