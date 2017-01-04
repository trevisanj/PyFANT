#!/usr/bin/env python3

"""
Looks for files "*.norm" inside directories session-* and saves one figure per page in a PDF file

References:
http://stackoverflow.com/questions/17788685
"""

import matplotlib.backends.backend_pdf
import matplotlib.pyplot as plt
import pyscellanea as pa
import glob
import os
import argparse
import pyfant as pf
import logging


pa.logging_level = logging.INFO
pa.flag_log_file = True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
     description=__doc__,
     formatter_class=pa.SmartFormatter
     )

    parser.add_argument('--samey',
        help='Creates all plots with same y-limits of [0, 1.02]', action="store_true")
    parser.add_argument('fn_output', nargs='?', default='output.pdf', type=str,
                        help='PDF output file name')

    args = parser.parse_args()

    dd = glob.glob(pf.SESSION_PREFIX_SINGULAR+"*")
    dd.sort()

    pdf = matplotlib.backends.backend_pdf.PdfPages(args.fn_output)

    pa.format_BLB()

    for d in dd:
        name = d[8:]

        pa.get_python_logger().info("Looking into session '{}'...".format(name))

        norm_filenames = glob.glob(os.path.join(d, "*.norm"))
        if len(norm_filenames) == 0:
            continue

        for filename in norm_filenames:
            pa.get_python_logger().info("    File '{}'".format(filename))
            f = pa.FileSpectrumPfant()

            # Note: takes first .norm file that finds
            f.load(filename)

            pa.draw_spectra([f.spectrum])  #v.title = "%s" % name

            fig = plt.gcf()
            if args.samey:
                plt.ylim([0, 1.02])
            else:
                y = f.spectrum.y
                ymin, ymax = min(y), max(y)
                margin = .02*(ymax-ymin)
                plt.ylim([ymin-margin, ymax+margin])
            ax = plt.gca()
            p = ax.get_position()
            p.x0 = 0.11
            ax.set_position(p)  # Try to apply same position for all figures to improve flicking experience
            pdf.savefig(fig)
            plt.close()

    # for fig in xrange(1, figure().number): ## will open an empty extra figure :(
    #     pdf.savefig( fig )
    pdf.close()

