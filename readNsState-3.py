#!/usr/bin/env python3

import sys
from struct import pack, unpack, calcsize
import base64
import time
from datetime import timedelta

def flipend(end):
    return '>' if end == '<' else '<'

def printGenState(dn, nsstate, flip):
    if pack('<h', 1) == pack('=h', 1):
        print("Little Endian")
        end = '<'
        if flip:
            end = flipend(end)
    elif pack('>h', 1) == pack('=h', 1):
        print("Big Endian")
        end = '>'
        if flip:
            end = flipend(end)
    else:
        print("Unknown Endian")
        sys.exit(-1)

    print("For replica", dn)
    thelen = len(nsstate)

    if thelen <= 20:
        pad = 2
        timefmt = 'I'
    else:
        pad = 6
        timefmt = 'Q'

    base_fmtstr = f"H{pad}x3{timefmt}H{pad}x"
    print(f"  fmtstr=[{base_fmtstr}]")
    print(f"  size={calcsize(base_fmtstr)}")
    print("  len of nsstate is", thelen)

    fmtstr = end + base_fmtstr
    rid, sampled_time, local_offset, remote_offset, seq_num = unpack(fmtstr, nsstate)

    now = int(time.time())
    tdiff = now - sampled_time

    wrongendian = False
    try:
        tdelta = timedelta(seconds=tdiff)
        wrongendian = tdelta.days > 3650
    except OverflowError:
        wrongendian = True

    if wrongendian:
        print("The difference in days is", tdiff // 86400)
        print("This is probably the wrong bit-endianness - flipping")
        end = flipend(end)
        fmtstr = end + base_fmtstr
        rid, sampled_time, local_offset, remote_offset, seq_num = unpack(fmtstr, nsstate)
        tdiff = now - sampled_time
        tdelta = timedelta(seconds=tdiff)

    print(f"""  CSN generator state:
    Replica ID    : {rid}
    Sampled Time  : {sampled_time}
    Gen as csn    : {sampled_time:08x}{seq_num:04d}{rid:04d}0000
    Time as str   : {time.ctime(sampled_time)}
    Local Offset  : {local_offset}
    Remote Offset : {remote_offset}
    Seq. num      : {seq_num}
    System time   : {time.ctime(now)}
    Diff in sec.  : {tdiff}
    Day:sec diff  : {tdelta.days}:{tdelta.seconds}
""")

def main():
    if len(sys.argv) < 2:
        print("Usage: readNsState.py <file.ldif> [flip]")
        sys.exit(1)

    filename = sys.argv[1]
    flip = len(sys.argv) > 2
    dn = ''
    nsstate = None

    with open(filename) as f:
        for line in f:
            if line.startswith("dn: "):
                dn = line[4:].strip()
            if line.startswith("nsState:: ") and dn.startswith("cn=replica"):
                b64val = line[10:].strip()
                print("nsState is", b64val)
                nsstate = base64.b64decode(b64val)
                printGenState(dn, nsstate, flip)

    if nsstate is None:
        print("Error: nsstate not found in file", filename)
        sys.exit(1)

if __name__ == '__main__':
    main()
