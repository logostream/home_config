#! /usr/bin/python
import sys;
import re;

def mhturl (mhtpath):
    got = 0;
    with open(mhtpath) as mht:
        for line in mht:
            match = re.search('^Content-Location: (.*)$', line);
            if not match is None:
                print match.group(1);
                got += 1;
    sys.stderr.write("Got %d urls.\n" % got);
    return;

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s ${mht_path}\n" % sys.argv[0]);
    else:
        mhturl(sys.argv[1]);

