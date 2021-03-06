#!/usr/bin/env python
"""
Copies stellar data files (such as main.dat, abonds.dat, dissoc.dat) to local directory

examples of usage:
  > copy-star.py
  (displays menu)

  > copy-star.py arcturus
  ("arcturus" is the name of a subdirectory of PFANT/data)

  > copy-star.py -p /home/user/pfant-common-data
  (use option "-p" to specify path)

  > copy-star.py -l
  (lists subdirectories of PFANT/data , doesn't copy anything)

"""
import argparse
import logging
import os.path
import sys
import glob
import shutil
import pyfant
import a99


a99.logging_level = logging.INFO
a99.flag_log_file = True


if __name__ == "__main__":
    flag_menu = len(sys.argv) == 1  # will display menu if no command-line arguments

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=a99.SmartFormatter
    )
    parser.add_argument('-l', '--list', action='store_true',
      help='lists subdirectories of '+pyfant.get_pfant_data_path())
    parser.add_argument('-p', '--path', action='store_true',
      help='system path mode')
    parser.add_argument('directory', type=str, nargs="?",
     help='name of directory (either a subdirectory of PFANT/data or the path '
          'to a valid system directory (see modes of operation)')

    args = parser.parse_args()


    # "-l" mode
    if args.list:
        print("\n".join(a99.format_h1("Subdirectories of '{}'".format(pyfant.get_pfant_data_path()))))
        for dirname in pyfant.get_pfant_data_subdirs():
            print(dirname)
        sys.exit()
        
    # figures out the path to directory (dir_)
    if flag_menu:
        print("\nLooking into directory '{}'...".format(pyfant.get_pfant_data_path()))
        dirnames = pyfant.get_pfant_star_subdirs()
        dirnames.sort()
        choice = a99.menu("Choose a star", ["{}{}".format(x[0].upper(), x[1:]) for x in dirnames],
                      cancel_label="quit", flag_allow_empty=True, flag_cancel=False)
        if choice is None or choice <= 0:
            sys.exit()
        dir_ = os.path.join(pyfant.get_pfant_data_path(), dirnames[choice-1])
    else:
        if args.path:
            dir_ = args.directory
        else:
            dir_ = os.path.join(pyfant.get_pfant_data_path(), args.directory)
            
    if not os.path.isdir(dir_):
        print("'%s' is not a directory" % dir_)
        sys.exit(-1)
    pyfant.copy_star(dir_)

    # print("\n")
    # print("\n".join(a99.format_box("Attention")))
    # print("File 'dissoc.dat' may require revision!\n\n"
    #       "You may delete this file to assume atomic abundances in 'abonds.dat' for the molecules.\n\n"
    #       "(this message should be deleted when all files 'dissoc.dat' provided with PFANT\n"
    #       "finish being reviewed)\n\n"
    #       "(2017-11-28)\n")
