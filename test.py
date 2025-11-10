#!/usr/bin/env python

from smartcard.System import readers
from smartcard.util import toHexString, toBytes
from smartcard.Exceptions import NoCardException
import sys

class Connection:
    def __init__(self, reader_index=0):
        # select first smartcard reader by default
        r=readers()
        if not len(r):
            print("[!] No reader connected.")
            sys.exit(-1)
        else:
            print("[+] Connecting to %s" % r[reader_index])

        try:
            connection = r[reader_index].createConnection()
            connection.connect()
        except NoCardException as e:
            print("[!] Insert a card in the reader, dummy.")
            sys.exit(-1)
        self.connection = connection

    def transmit(self, hex_string):
        select_command = toBytes(hex_string)
        data, sw1, sw2 = self.connection.transmit(select_command)
        return toHexString(data), sw1, sw2

connection = Connection()


# select ICC
select_command = "80 A4 08 00 04 3F 00 00 02"
data,sw1,sw2 = connection.transmit(select_command)
if sw2 == 0x19:
    read_1record = "80 B2 01 04 1D" #intermediate if 0X612A
    data,sw1,sw2 = connection.transmit(read_1record)
    print("ICC:", data)
else:
    print ("Error in ICC select")


# select holder
s = "80 A4 08 00 04 3F 00 3F 1C"
data,sw1,sw2 = connection.transmit(s)
print("RAPDU: %s %02x %02x" % (data, sw1,sw2))
if sw2 == 0x19:
    read_1record = "80 B2 01 04 1D"
    data,sw1,sw2 = connection.transmit(read_1record)
    print("Holder 1:", data)
    read_2record = "80 B2 02 04 1D"
    data,sw1,sw2 = connection.transmit(read_2record)
    print("Holder 2:", data)
else:
    print ("Error in ICC select")

s = "00 A4 04 00 0E 31 54 49 43 2E 49 43 41 D0 56 00 01 91 01"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("RAPDU: %s %02x %02x" % (data, sw1,sw2))
if sw2 == 0x2a:
    read_1record = "00 C0 00 00 2A" #intermediate if 0X612A
    print("CAPDU: %s" % read_1record)
    data,sw1,sw2 = connection.transmit(read_1record)
    print("UNKNOWN:", data)
else:
    print ("Error in ICC select")

s = "00 B2 01 3C 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("UNKNOWN1:", data)

s = "00 B2 02 3C 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("UNKNOWN2:", data)

s = "00 B2 01 CC 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("Counter:", data)


s = "00 B2 01 4C 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("Contra1:", data)
s = "00 B2 02 4C 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("Contra2:", data)
s = "00 B2 03 4C 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("Contra3:", data)
s = "00 B2 04 4C 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("Contra4:", data)
s = "00 B2 05 4C 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("Contra5:", data)
s = "00 B2 06 4C 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("Contra6:", data)
s = "00 B2 07 4C 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("Contra7:", data)
s = "00 B2 08 4C 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("Contra8:", data)

# EvLog1
s = "00 B2 01 BC 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("EvLog1: ", data)

# EvLog2
s = "00 B2 02 BC 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("EvLog2: ", data)

# EvLog3
s = "00 B2 03 BC 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("EvLog3: ", data)

s = "00 B2 04 BC 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("EvLog4?:", data)

s = "00 B2 01 EC 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("UNKNOWN1:", data)
s = "00 B2 02 EC 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("UNKNOWN2:", data)
s = "00 B2 03 EC 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("UNKNOWN3:", data)
s = "00 B2 04 EC 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("UNKNOWN4:", data)

s = "00 B2 01 B4 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("UNKNOWN1:", data)

s = "00 B2 01 F4 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("ConList: ", data)
s = "00 A4 04 00 0B A0 00 00 02 91 D0 56 00 01 90 01"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("RAPDU: %s %02x %02x" % (data, sw1,sw2))

if sw1 == 0x90 and sw2 == 0x00:
    s = "00 C0 00 00 00"
    read_1record = toBytes(s) #intermediate if 0X9000
    print("CAPDU:", s)
    data,sw1,sw2 = connection.transmit(read_1record)
    print("RAPDU:     %s %02x %02x" % (data, sw1, sw2))
    if sw1 == 0x6c and sw2 == 0x27:
        s = "00 C0 00 00 27" #intermediate if 0X6C27 RAPDU
        read_2record = toBytes(s)
        print("CAPDU:", s)
        data,sw1,sw2=connection.transmit(read_2record)
        print("UNKNOWN:    ", data)
    else:
        print("Error in 0X6C27 read")
else:
    print ("Error in 0X900 read")


s = "00 B2 01 E4 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("Holder1:", data)
s = "00 B2 02 E4 1D"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("Holder2:", data)
