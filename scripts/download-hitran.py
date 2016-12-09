#!/usr/bin/env python3

"""
Downloads molecular lines from HITRAN database
"""

import pyfant as pf
import argparse
import logging
import astroapi as aa
import tabulate
import sys


pf.logging_level = logging.INFO

_DEF_T = '(molecular formula)'
_DEF_M = '(lists molecules)'
_DEF_I = '(lists isotopologues)'
_DEF_LL = None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=aa.SmartFormatter
    )
    parser.add_argument('-t', type=str, help='Table Name',
                        default=_DEF_T, nargs=1)
    parser.add_argument('M', type=str, help='HITRAN molecule number',
                        default=_DEF_M, nargs='?')
    parser.add_argument('I', type=str,
                        help='HITRAN isotopologue number (not unique, starts over at each molecule)',
                        default=_DEF_I, nargs='?')
    parser.add_argument('llzero', type=float,
                        help='Initial wavelength (Angstrom)',
                        default=_DEF_LL, nargs='?')
    parser.add_argument('llfin', type=float,
                        help='Final wavelength (Angstrom)',
                        default=_DEF_LL, nargs='?')
    # parser.add_argument('llzero', type=str,
    # help='initial wavelength (',
    # default='()', nargs='?')
    # parser.add_argument('I', type=str,
    # help='HITRAN isotopologue number (not unique, starts over at each molecule',
    # default='()', nargs='?')
    args = parser.parse_args()

    db = pf.hitrandb
    if args.M == _DEF_M:
        print()
        print("\n".join(aa.format_h1("Listing all HITRAN molecules")))
        print()
        # Lists all molecules from local cache of HITRAN molecules
        print(tabulate.tabulate(*aa.cursor_to_data_header(db.query_molecule())))
    elif args.I == _DEF_I:
        row0 = db.query_molecule(ID=args.M).fetchone()
        if row0 is None:
            aa.print_error("Molecule ID {} not found".format(args.M))
            sys.exit()

        print()
        print("\n".join(aa.format_h1("Listing all isotopologues for molecule '{Formula}' ({Name})".
                                     format(**row0))))
        print()
        # Lists all molecules from local cache of HITRAN molecules
        print(tabulate.tabulate(*aa.cursor_to_data_header(
            db.query_isotopologue(**{"molecule.ID": args.M}))))
    else:
        row0 = db.query_molecule(ID=args.M).fetchone()
        if row0 is None:
            aa.print_error("Molecule ID {} not found".format(args.M))
        else:
            kwargs = {"molecule.id": args.M, "isotopologue.ID": args.I}
            row1 = db.query_isotopologue(**kwargs).fetchone()
            if row1 is None:
                aa.print_error("Isotopologue ({}, {}) not found".format(args.M, args.I))
                sys.exit()

            print(tabulate.tabulate(list(row1.items()), ["Field name", "Value"]))
            print()

            if args.llzero == _DEF_LL or args.llfin == _DEF_LL:
                aa.print_error("Please specify wavelength interval")
                sys.exit()

            print("Wavelength interval (air): [{llzero}, {llfin}] Angstrom".format(**args.__dict__))
            if args.llzero >= args.llfin:
                aa.print_error("Initial wavelength must be lower than Final wavelength")
                sys.exit()
            wn0 = aa.air_to_vacuum(1e8/args.llzero)
            wn1 = aa.air_to_vacuum(1e8/args.llfin)
            print("Wavenumber interval (vacuum): [{}, {}] cm**-1".format(wn1, wn0))

            table_name = args.t if args.t != _DEF_T else row0["Formula"]
            print("Table name: '{}'".format(table_name))
            print()
            print("Fetching data...")
            pf.hapi.fetch(table_name, int(args.M), int(args.I), wn1, wn0)

            print("...done")
            print("Please check files '{0}.header', '{0}.data'".format(table_name))





    # kwargs = {}
    # if not args.ID == "(all)":
    #     kwargs["molecule.ID"] = args.ID
    #
    # pf.hitrandb.print_isotopologues(**kwargs)