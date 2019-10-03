#!/usr/bin/python2

import gzip
import os
import sys
import gmv.blowfish
import gmv.gmvault_utils as gmvault_utils
import gmv.imap_utils as imap_utils
from pathlib2 import Path

parser = argparse.ArgumentParser(description='Decrypt gmvault email.')
required_args = parser.add_argument_group('required arguments')

required_args.add_argument('-d', '--database', action='store_true',
                           help='full path to db directory', required=True)
required_args.add_argument('-o', '--output', action='store_true',
                           help='full path to output directory', required=True)
required_args.add_argument('-c', '--cipher', action='store_true',
                           help='blowfish cipher', required=True)
parser.add_argument('-v', '--verbose', action='store_true',
                    help='enable verbose output')
args = parser.parse_args()


def vprint(msg):
    if verbose:
        print(msg)


eml_list = list(Path(database).rglob("*.gz"))
cipher = gmv.blowfish.Blowfish(blowfish)

for filepath in eml_list:
    eml = str(filepath)
    basename = os.path.basename(eml)
    decrypted_filename = basename[:basename.index('.')] + '.eml'
    filename = os.path.join(output, decrypted_filename)

    vprint('Decrypting: ' + eml)

    gz_fd = gzip.open(eml)
    content = gz_fd.read()
    cipher.initCTR()
    message = cipher.decryptCTR(content)

    try:
        with open(filename, 'w') as f:
            f.write(message)
    except IOError:
        print('Unable to write to \"' + filename + '\"')
        sys.exit(1)

    vprint('Wrote: ' + decrypted_filename)
