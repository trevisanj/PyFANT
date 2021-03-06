#!/usr/bin/env python
"""
Creates symbolic links to PFANT data files as an alternative to copying these (sometimes large) files into local directory

A star is specified by three data files whose typical names are:
main.dat, abonds.dat, and dissoc.dat .

The other data files (atomic/molecular lines, partition function, etc.)
are star-independent, and this script is a proposed solution to keep you from
copying these files for every new case.

How it works: link.py will look inside a given directory and create
symbolic links to files *.dat and *.mod.

The following files will be skipped:
  - main files, e.g. "main.dat"
  - dissoc files, e.g., "dissoc.dat"
  - abonds files, e.g., "abonds.dat"
  - .mod files with a single model inside, e.g., "modeles.mod"
  - hydrogen lines files, e.g., "thalpha", "thbeta"

This script works in two different modes:

a) default mode: looks for files in a subdirectory of PFANT/data
   > link.py common
   (will create links to filess inside PFANT/data/common)

b) "-l" option: lists subdirectories of PFANT/data

c) "-p" option: looks for files in a directory specified.
   Examples:
   > link.py -p /home/user/pfant-common-data
   > link.py -p ../../pfant-common-data

Note: in Windows, this script must be run as administrator.
"""
import argparse
import logging
import sys
import pyfant
import a99


a99.logging_level = logging.INFO
a99.flag_log_file = True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=a99.SmartFormatter
    )
    parser.add_argument('-l', '--list', action='store_true',
      help='lists subdirectories of '+pyfant.get_pfant_data_path())
    parser.add_argument('-p', '--path', action='store_true',
      help='system path mode')
    parser.add_argument('-y', '--yes', action="store_true",
                        help="Automatically answers 'yes' to eventual question")
    parser.add_argument('directory', type=str, nargs="?", default="common",
     help='name of directory (either a subdirectory of PFANT/data or the path '
          'to a valid system directory (see modes of operation)')

    args = parser.parse_args()

    # if len(sys.argv) == 1:
    #     args.list = True  # makes "-l" the default behaviour

    if (not args.directory or len(args.directory) ==  0) and not args.list:
        print("Directory name is required, except if '-l' option specified.")
        parser.print_usage()
        sys.exit()

    # "-l" mode
    if args.list:
        print("\n".join(a99.format_h1("Subdirectories of '%s'" % pyfant.get_pfant_data_path())))
        for dirname in pyfant.get_pfant_data_subdirs():
            print(dirname)
        sys.exit()

    if args.path:
        dir_ = args.directory
    else:
        dir_ = pyfant.get_pfant_path('data', args.directory)

    flag_ask = not args.path and not args.yes

    if flag_ask:
        while True:
            ans = input("Create links to PFANT data files in '%s' (Y/n)? " %
                            dir_).upper()
            if ans in ("N", "NO"):
                sys.exit()
            if ans in ("Y", "YES", ""):
                break

    pyfant.link_to_data(dir_)

