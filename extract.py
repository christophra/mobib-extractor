#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
 (c) 2009 MOBIB Extractor project. This software is provided 'as-is',
  without any express or implied warranty. In no event will the authors be held
  liable for any damages arising from the use of this software.

  Permission is granted to anyone to use this software for any purpose,
  including commercial applications, and to alter it and redistribute it
  freely, subject to no restriction.

  Technical remarks and questions can be addressed to
  <tania.martin@uclouvain.be>  <jean-pierre.Szikora@uclouvain.be>
"""

import sys
from pathlib import Path
import datetime
import string
import csv
from smartcard.System import readers
from smartcard.util import toHexString, toBytes
from smartcard.Exceptions import NoCardException
import folium
import webbrowser
import argparse
import json

class Connection:
    """Connection to a Mobib or other smartcard.

    Attributes:
        connection : connection to the card
    Methods:
        transmit : transmit a select command
    """
    def __init__(self, card_index=-1):
        """Create connection to a connected card.

        Args:
            card_index (int, optional): If set, use card at this index. Else, use the first that works.
        """
        connected_readers = readers()
        if len(connected_readers) == 0:
            print("[!] No reader detected")
            sys.exit(-1)
        print("\033[92mSmartcard reader detected.\033[0m")
        
        connection = None
        for i, reader in enumerate(connected_readers):
            if card_index >= 0 and i != card_index: # select one, default (-1) is loop over all
                continue
            try:
                print("Connecting to \033[4m{}\033[0m...".format(reader))
                connection = reader.createConnection()
                connection.connect()
                break # if successful, use first one
            except NoCardException as e:
                print("[!] No card inserted ({})".format(e))
                connection = None
        
        # Designated card or none of them
        if connection is None:
            sys.exit(-1)
        self.connection = connection

    def transmit(self, select_command_hex_string):
        """Transmit a select command to the card and obtain response.

        Args:
            select_command_hex_string (str): hex string of bytes to send.

        Returns:
            (str, bytes, bytes): data return as hex string, status word 1, status word 2
        """
        select_command = toBytes(select_command_hex_string)
        data, sw1, sw2 = self.connection.transmit(select_command)
        return toHexString(data), sw1, sw2


def hex_to_bin(h):
    """Hexadecimal to binary
    """
    return bin(int(h, 16))[2:].zfill(len(h)*4)

def bin_to_alphabet(b, t):
    """Binary to alphabet with offset t (on 5 bits)
    """
    res = ''
    r = 5 if len(b) % 5 == 0 else len(b) % 5
    for i in range(t, len(b)-(r+t), 5):
        a = int(b[i:i+5], 2)
        res += ' ' if (a > 26 or a < 1) else chr(64 + a)
    return res

def bin_to_number(b):
    """Binary to number (on the total length)
    """
    return str(int(b, 2))

def bin_to_number_dec(b, t):
    """Binary to number with offset t (on 4 bits)
    """
    res = ''
    r = 4 if len(b) % 4 == 0 else len(b) % 4
    for i in range(t, len(b) - (r+t), 4):
        a = int(b[i:i+4], 2)
        res += "x" if a > 9 else str(a)
    return res

def find_date(x):
    """Find a date from the 1st January 1997
    """
    init = datetime.date(1997, 1, 1)
    diff = datetime.timedelta(days=x)
    d = init + diff
    if d == init:
        fmt_date = "-"
    else:
        fmt_date = d.strftime("%d/%m/%Y")
    return fmt_date

def find_hour(x):
    """Find an hour
    """
    _min = str(int(x) % 60)
    if _min in [x for x in string.digits]:
        _min = '0' + _min
    return (int(x) / 60, _min)

def analyze_holder(raw_holder1, raw_holder2):
    """
    Find Name + Birthdate + Post code + Card number + Remaining travels ##

    raw_holder1 has :
        - bytes 0-1 : unknown data
        - bytes 2-11 : the card number
        - bytes 12-20 : unknown data
        - bytes 21-24 : the birthday
        - bytes 24-28 : the begining of the name
        - raw_holder2 has the end of the name
    """

    ## Name

    ## Card number
    hexa_card = ''.join(raw_holder1[2:13])[:-1]

    num_card = bin_to_number_dec(hex_to_bin(hexa_card), 2) # offset = 2
    print("\033[1mCard number:\033[0m {}".format(num_card))

    hexa_type = raw_holder1[25][0]
    bin_type = hex_to_bin(hexa_type)[0:2]
    if bin_type == '01':
        gender = 'Mr'
    elif bin_type == '10':
        gender = 'Mrs'
    else:
        gender = None

    if gender is not None:
        hexa_name = ''.join(raw_holder1[25:29])[1:] + ''.join(raw_holder2)
        bin_name = hex_to_bin(hexa_name)
        name = bin_to_alphabet(bin_name, 1) # offset = 1

        print("\033[1mName:\033[0m {} {}".format(gender, name))

        ## Birthday
        birthday = "{}/{}/{}{}".format(raw_holder1[24], raw_holder1[23],\
            raw_holder1[21], raw_holder1[22])
        print("\033[1mBirthday:\033[0m {}".format(birthday))
    else:
        print("\033[1mName:\033[0m MOBIB BASIC")


def analyze_envholder(raw_envholder):
    """
    Get zip code out of holder data.
    """
    # Zip code
    # TODO: zip code location seems to have changed. Seems to work for 2 cards so far.
    hexa_zipcode = raw_envholder[22] + raw_envholder[23] + raw_envholder[24][0]
    zipcode = bin_to_number(hex_to_bin(hexa_zipcode)[4:17])
    print("\033[1mZip code:\033[0m {}".format(zipcode))


def analyze_counter(raw_counter):
    """
    Get remaining travels out of holder data.
    """
    ## Remaining travels
    hexa_counter = []
    for i in range(0, 26, 3):
        hexa_counter.append(raw_counter[i] + raw_counter[i+1] + raw_counter[i+2])
    c = int(0)
    for i in range(len(hexa_counter)):
        c = c + int(bin_to_number(hex_to_bin(hexa_counter[i])))

    ## Contract type
    if c == 12034:
        c = "-"
        contract_type = "Day subscription"
    else:
        contract_type = "UNKNOWN"
    print("\033[1mContract type:\033[0m {}".format(contract_type))
    print("\033[1mRemaining travels:\033[0m {}".format(c))


def analyze_log(raw_log):
    """
    Analyze travel logs and returns readable data (line, station, date, time)
    plus coordinates looked up from open data.
    """
    ## Card total validations counter
    hexa_cp_total_log = raw_log[17] + raw_log[18] + raw_log[19] + raw_log[20][0]
    r = hex_to_bin(hexa_cp_total_log)
    cp_total_log = bin_to_number(r[3:-2])

    ## Travel connection counter
    hexa_cp_corresp_log = raw_log[20] + raw_log[21] + raw_log[22] + raw_log[23][0]
    r = hex_to_bin(hexa_cp_corresp_log)
    cp_corresp_log = bin_to_number(r[3:-2])

    ## Card validation date
    hexa_date_valid = raw_log[0][1] + raw_log[1] + raw_log[2][0]

    tmp_datev_bin = hex_to_bin(hexa_date_valid)
    date_valid = find_date(
        int(
            bin_to_number(
                tmp_datev_bin[2:]
            )
        )
    )

    ## Card validation date of the first transit travel
    hexa_date_transit = raw_log[23] + raw_log[24]
    tmp_datet_bin = hex_to_bin(hexa_date_transit)
    date_transit = find_date(int(bin_to_number(tmp_datet_bin[2:])))

    ## Card validation hour
    hexa_heure_valid = raw_log[2][1] + raw_log[3]

    tmp_heurev_bin = hex_to_bin(hexa_heure_valid)
    heure_valid = find_hour(int(bin_to_number(tmp_heurev_bin[:-1])))

    ## Card validation hour of the first transit travel
    hexa_heure_transit = raw_log[25] + raw_log[26][0]
    tmp_heuret_bin = hex_to_bin(hexa_heure_transit)
    heure_transit = find_hour(int(bin_to_number(tmp_heuret_bin[-1])))

    ## Transit or not ?
    if raw_log[6][0] == '6':
        transit = "YES"
    else:
        transit = "NO"

    ## Number of persons travelling
    bin_nb_persons = hex_to_bin(raw_log[6][1] + raw_log[7][0])[0:5]
    nb_persons = bin_to_number(bin_nb_persons)

    ## Bit string logs
    string_log = hex_to_bin(''.join(raw_log[:29]))

    ## Transport type
    type_transport = 'Unknown'
    match string_log[99:104]:
        case '00000':
            if date_valid == '-':
                type_transport = '-'
            else:
                type_transport = 'Metro'
        case '00111':
            type_transport = 'Premetro'
        case '10110':
            type_transport = 'Tramway'
        case '01111':
            type_transport = 'Bus'
    
    ## Station
    # defaults
    ligne, station, direction = '-', 'No info', 'No info'
    coordx, coordy = '-', '-'
    # For metro/premetro
    zone_id, subzone_id, station_id = string_log[104:110], string_log[110:114], string_log[114:121]
    # For bus and tram
    # matches some. was 71:83, 70:83. Also line number, but might go to [(80,99), (114,119), (137,160), (144,160), (180,188)]
    line_number, stop_number = bin_to_number(string_log[92:99]), bin_to_number(string_log[67:83])
    # TODO stops with appended letters?

    # if the transport is a metro or premetro
    if type_transport in ['Metro', 'Premetro']:
        reader = csv.reader(open("Database/metro_new.csv", "r"))
        for r in reader:
            if zone_id == r[1] and subzone_id == r[2] and station_id == r[3]:
                ligne = r[4]
                station = r[5]
                direction = "No info"
                coordx = r[6]
                coordy = r[7]
    # if the transport is a tram or bus, or was not found with the dedicated CSV
    if type_transport in ['Tramway', 'Bus'] or ligne == '-':
        # defaults if we don't find it in the CSV
        ligne = "Unknown" if line_number == '0' else line_number
        station = stop_number
        reader = csv.reader(open("Database/stops.txt", "r")) # TODO if 0 can skip the CSV...
        for r in reader:
            s = ''.join(filter(str.isdigit, r[0])) # FIXME some stop IDs in GTFS have appended letters - how do these appear on Mobib, if at all?
            if (stop_number == s):
                station = r[2] # station name
                #direction = r[1] # most stops come in pairs => determines direction - but haven't yet compiled this for updated list
                coordx = r[4]
                coordy = r[5]
                break
    
    # Print output
    print("{}\t\t{}\t{:15s}\t\t{} {:02d}:{}\t\t{};{}".format(
        type_transport,
        ligne,
        station,
        date_valid,
        int(heure_valid[0]),
        heure_valid[1],
        coordx,
        coordy
        ))
    return (coordx, coordy)

def analyze_logs(raw_logs):
    # Print table from entries
    print("\n\033[1mLast known locations:\033[0m\n")
    print("\033[4mTransport\tLine\tStation\t\t\tTime\t\t\t\tCoords\033[0m")
    coords_str = [analyze_log(log) for log in raw_logs]

    # Extract coords where available
    coords = []
    for cx, cy in coords_str:
        if cx != '-':
            coords.append((float(cx), float(cy)))

    return coords
    
def map_logs(coords):
    # Put them onto a Leaflet.js map
    m = folium.Map(tiles='OpenStreetMap')
    for coord in coords:
        folium.Marker(location=coord).add_to(m)
    # Center
    m.fit_bounds([[fun(c[i] for c in coords) for i in [0,1]] for fun in [min, max]])
    # Show
    m.save("_map.html")
    webbrowser.open_new_tab("_map.html")

def read_card():
    """Read salient raw data from the Mobib card in any connected card reader.
    """
    raw_data = {}

    # 0x00 class byte
    # 0xA4 select command
    # 0x04 P1
    # 0x00 P2
    # 0x0E Lc
    # 0x3154494341D056000191
    # 0x01 Le:q
    
    connection = Connection()

    connection.transmit("00 A4 04 00 0E 31 54 49 43 2E 49 43 41 D0 56 00 01 91 01")

    raw_data["envholder"] = connection.transmit("00 B2 01 3C 1D")[0]
    raw_data["counter"] = connection.transmit("00 B2 01 CC 1D")[0]

    # EvLog1, EvLog2, EvLog3, EvLog4 (new)
    raw_data["logs"] = [connection.transmit(f"00 B2 0{i} BC 1D")[0] for i in [1,2,3,4]]
    
    connection.transmit("00 A4 04 00 0B A0 00 00 02 91 D0 56 00 01 90 01")
    
    raw_data["holder1"] = connection.transmit("00 B2 01 E4 1D")[0]
    raw_data["holder2"] = connection.transmit("00 B2 02 E4 1D")[0]

    return raw_data

def split(raw_data):
    """Turn the format of toHexString into a list of bytes in hexadecimal for the analyse_... functions.
    """
    out = {}
    for k,v in raw_data.items():
        if type(v) is list:
            out[k] = [_v.split(' ') for _v in v]
        else:
            out[k] = v.split(' ')
    return out

def main(args):
    """
    I'm the main function :o
    """
    # Handle input/output: from card, from dump, to dump.
    if args.load is None:
        raw_data = read_card()
        if args.dump is not None:
            with open(args.dump, "w") as f:
                json.dump(raw_data, f, indent=4)
    else:
        with open(args.load) as f:
            raw_data = json.load(f)

    # To analyse, split hexadecimal representation
    raw_data = split(raw_data)

    # Extract info and prepare a pretty summary
    analyze_holder(raw_data["holder1"], raw_data["holder2"])
    # if not basic card
    if len(raw_data["envholder"]) > 1:
        analyze_envholder(raw_data["envholder"])
    analyze_counter(raw_data["counter"])
    coords = analyze_logs(raw_data["logs"])
    if args.map:
        map_logs(coords)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("mobib-extract")
    parser.add_argument("--dump", type=str, default=None, help="Dump the read raw data to this JSON file")
    parser.add_argument("--load", type=str, default=None, help="Read the raw data from a JSON file instead of the card")
    parser.add_argument("--map", action='store_true', help="Show a map where you've been")
    args = parser.parse_args()
    if args.dump is not None:
        dump = Path(args.dump)
        dump.parent.mkdir(exist_ok=True)
    main(args)
