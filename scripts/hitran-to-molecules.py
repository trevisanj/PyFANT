#!/usr/bin/env python3
"""
Converts VALD3 atomic/molecular lines file to PFANT atomic lines file.

Molecular lines are skipped.

"""

import argparse
import logging
import numpy as np
import sys
import pyfant as pf
import astroapi as aa


aa.logging_level = logging.INFO
aa.flag_log_file = True


DEFOUT = "molecules-<fn_input>"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
     description=__doc__,
     formatter_class=aa.SmartFormatter
     )
    parser.add_argument('tablename', type=str,
     help='HITRAN table name. A pair of files <tablename>.data and <tablename>.header '
          'must exist in local directory', nargs=1)
    parser.add_argument('fn_output', type=str, help='output file name', nargs="?",
     default=DEFOUT)

    # TODO filter molecular lines by threshold
    # parser.add_argument('--min_algf', type=float, nargs='?', default=-7,
    #  help='minimum algf (log gf)')
    # parser.add_argument('--max_kiex', type=float, nargs='?', default=15,
    #  help='maximum kiex')

    args = parser.parse_args()
    logger = aa.get_python_logger()

    fn_out = args.fn_output
    if fn_out == DEFOUT:
        fn_out = "atoms-untuned-"+args.fn_input[0]

    logger.info("Converting file...")
    with open(args.fn_input[0], 'r') as file_:
        file_atoms = pf.vald3_to_atoms(file_)

    # n0 = file_atoms.num_lines
    # logger.info("Number of lines before filtering: %d" % n0)
    #
    # logger.info("Removing all (algf < %g)..." % args.min_algf)
    # file_atoms.filter(lambda line: line.algf >= args.min_algf)
    # logger.info("Number of lines removed: %d" % (n0-file_atoms.num_lines))
    #
    # logger.info("Number of lines after filtering: %d" % file_atoms.num_lines)

    logger.info("Saving file...")
    file_atoms.save_as(fn_out)
    print("File %s was successfully created." % fn_out)
