#!/usr/bin/env python3

"""Abundances file editor"""

import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import argparse
import pyfant as pf
import hypydrive as hpd
import logging


hpd.logging_level = logging.INFO
hpd.flag_log_file = True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=hpd.SmartFormatter
    )
    parser.add_argument('fn', type=str, help='abundances file name', default='abonds.dat', nargs='?')
    args = parser.parse_args()

    m = pf.FileAbonds()
    m.load(args.fn)
    app = hpd.get_QApplication([])
    form = pf.XFileAbonds()
    form.show()
    form.load(m)
    sys.exit(app.exec_())
