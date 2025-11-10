#!/usr/bin/env python

from smartcard.System import readers
from smartcard.util import toHexString, toBytes
from smartcard.Exceptions import NoCardException
from extract import Connection
import sys

connection = Connection(card_index=0)


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

for s, label in [
    ("00 B2 01 3C 1D", "UNKNOWN1"),
    ("00 B2 02 3C 1D", "UNKNOWN2"),
    ("00 B2 01 CC 1D", "Counter"),
    ("00 B2 01 4C 1D", "Contra1"),
    ("00 B2 02 4C 1D", "Contra2"),
    ("00 B2 03 4C 1D", "Contra3"),
    ("00 B2 04 4C 1D", "Contra4"),
    ("00 B2 05 4C 1D", "Contra5"),
    ("00 B2 06 4C 1D", "Contra6"),
    ("00 B2 07 4C 1D", "Contra7"),
    ("00 B2 08 4C 1D", "Contra8"),
    ("00 B2 01 BC 1D", "EvLog1"),
    ("00 B2 02 BC 1D", "EvLog2"),
    ("00 B2 03 BC 1D", "EvLog3"),
    ("00 B2 04 BC 1D", "EvLog4?"),
    ("00 B2 01 EC 1D", "UNKNOWN1"),
    ("00 B2 02 EC 1D", "UNKNOWN2"),
    ("00 B2 03 EC 1D", "UNKNOWN3"),
    ("00 B2 04 EC 1D", "UNKNOWN4"),
    ("00 B2 01 B4 1D", "UNKNOWN1"),
    ("00 B2 01 F4 1D", "ConList"),
    ]:
    print("CAPDU:", s)
    data, sw1, sw2 = connection.transmit(s)
    print(f"{label:10s}: {data}")

s = "00 A4 04 00 0B A0 00 00 02 91 D0 56 00 01 90 01"
print("CAPDU:", s)
data,sw1,sw2 = connection.transmit(s)
print("RAPDU: %s %02x %02x" % (data, sw1,sw2))

if sw1 == 0x90 and sw2 == 0x00:
    read_1record = "00 C0 00 00 00" #intermediate if 0X9000
    print("CAPDU:", read_1record)
    data,sw1,sw2 = connection.transmit(read_1record)
    print("RAPDU:     %s %02x %02x" % (data, sw1, sw2))
    if sw1 == 0x6c and sw2 == 0x27:
        read_2record = "00 C0 00 00 27" #intermediate if 0X6C27 RAPDU
        print("CAPDU:", read_2record)
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
