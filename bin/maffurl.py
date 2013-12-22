#! /usr/bin/python
import zipfile as zf;
import sys;
import re;

def maffurl (maffpath):
    got = 0;
    with zf.ZipFile(maffpath) as maffzip:
        for filename in maffzip.namelist():
            if re.match('^\w+/index.rdf$', filename) is None:
                continue;
            with maffzip.open(filename) as rdf:
                for line in rdf:
                    match = re.search('<MAF:originalurl RDF:resource="(.*)"/>', line);
                    if not match is None:
                        print match.group(1);
                        got += 1;
    sys.stderr.write("Got %d urls.\n" % got);
    return;

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s ${maff_path}\n" % sys.argv[0]);
    else:
        maffurl(sys.argv[1]);
