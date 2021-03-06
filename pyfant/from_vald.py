"""
VALD3-to-PFANT conversions
"""

__all__ = ["vald3_to_atoms"]

import csv
import a99
import sys
import pyfant


# Here is a sample of a VALD3 file:
#  1|                                                                   Lande factors      Damping parameters
#  2|Elm Ion      WL_air(A)   log gf* E_low(eV) J lo  E_up(eV) J up  lower  upper   mean   Rad.  Stark  Waals
#  3|'OH 1',       10000.092,  -7.089,  0.0750,  4.5,  1.3150,  3.5,99.000,99.000,99.000, 0.000, 0.000, 0.000,
#  4|'  Hb                                                      2s2.3s2.1p3          X,2,1,e,5,0'
#  5|'  Hb                                                  2s2.3s2.1p3              X,2,1,e,4,3'
#  6|'GSGCD             OH data from Kur   1 GSGCD     1 GSGCD     1 GSGCD     1 GSGCD     1 GSGCD     1 GSGCD     1 GSGCD     1 GSGCD     1 GSGCD   (16)OH        '
#  7|'OH 1',       10000.117, -10.110,  2.5930, 26.5,  3.8330, 26.5,99.000,99.000,99.000, 0.000, 0.000, 0.000,
#  8|'  Hb                                                     2s2.3s2.1p3          X,2,1,f,26,3'
#  9|'  Hb                                                 2s2.3s2.1p3              X,2,1,f,27,7'
# 10|'GSGCD             OH data from Kur   1 GSGCD     1 GSGCD     1 GSGCD     1 GSGCD     1 GSGCD     1 GSGCD     1 GSGCD     1 GSGCD     1 GSGCD   (16)OH        '
# 11|'Ar 2',       10000.184,  -3.150, 25.4140,  2.5, 26.6540,  3.5,99.000,99.000,99.000, 0.000, 0.000, 0.000,
# 12|'  JK                                                           3s2.3p4.(3P<2>).5f     2[3]'
# 13|'  JK                                                           3s2.3p4.(3P<1>).7g     2[3]'
# 14|'KP                Li 1 - K 5 Bell    2 KP        2 KP        2 KP        2 KP        2 KP        2 KP        2 KP        2 KP        2 KP      Ar+           '


# Symbols of elements with first letter uppercase and second letter (if present) lowercase
_Symbols = ['H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Na', 'Mg', 'Al', 'Si', 'P', 'S',
            'Cl', 'Ar', 'K', 'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga',
            'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd',
            'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm',
            'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os',
            'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th',
            'Pa', 'U']


def vald3_to_atoms(file_obj):
    """
    Converts data from a VALD3 file into a FileAtoms object.

    Args:
      file_obj: file-like object, e.g., returned by open()

    Returns: a FileAtoms object

    VALD3 website: http://vald.astro.uu.se/
    """

    _logger = a99.get_python_logger()

    def log_skipping(r, reason, row):
        _logger.info("Skipping row #%d (%s)" % (r, reason))
        _logger.info(str(row))

    reader = csv.reader(file_obj)
    ret = pyfant.FileAtoms()
    edict = {}  # links atomic symbols with Atom objects created (key is atomic symbol)
    r = 0
    num_skip_ioni, num_skip_mol = 0, 0
    try:
        for row in reader:
            r += 1
            if len(row) <=  12:  # Condition to detect row of interest
                continue

            elem = row[0][1:row[0].index(" ")]
            if not elem in _Symbols:
                # skips molecule
                num_skip_mol += 1
                continue

            # # Collects information and creates atomic line object.
            # Note: Variable names follow Fortran source variable names.

            s_ioni = row[0][-2]
            ioni = int(s_ioni)  # not used, stays as file validation

            if ioni > 2:
                # log_skipping(r, "ionization > 2", row)
                num_skip_ioni += 1
                continue

            _waals = float(row[12])
            if _waals > 0:
                # If the van der Waals damping parameter is > 0, it means
                # something else, see the documentation at
                # http://www.astro.uu.se/valdwiki/Vald3Format:
                #  "if >0 : two parameters as defined in Barklem et al.
                #   2000A&AS..142..467B : integer part is cross-section sigma,
                #   fractional part is velocity parameter alpha"
                # Therefore, we fall back.
                _waals = 0

            line = pyfant.AtomicLine()
            line.lambda_ = float(row[1])
            line.algf = float(row[2])
            line.kiex = float(row[3])
            if _waals == 0:
                line.ch = 0.3e-31
            else:
                try:
                    # Formula supplied by Elvis Cantelli:
                    # extracted from cross-entropy code by P. Barklem
                    line.ch = 10**(2.5*_waals-12.32)
                except:
                    # Catches error to log _waals value that gave rise to error
                    _logger.critical("Error calculating ch: waals=%g" % _waals)
                    raise

            # Setting gr to zero will cause PFANT to calculate it using a formula.
            # See pfantlib.f90::read_atoms() for the formula.
            line.gr = 0.0
            # ge is not present in VALD3 file.
            # it enters as a multiplicative term in popadelh(). The original
            # atom4070g.dat and atoms.dat all had ge=0 for all lines.
            line.ge = 0.0
            # Attention: zinf must be tuned later using tune-zinf.py
            line.zinf = 0.5
            # Never used in PFANT
            line.abondr = 1

            # # Stores line in object
            elem = pyfant.adjust_atomic_symbol(elem)
            key = elem+s_ioni  # will group elements by this key
            if key in edict:
                a = edict[key]
            else:
                a = edict[key] = pyfant.Atom()
                a.elem = elem
                a.ioni = int(s_ioni)
                ret.atoms.append(a)
            a.lines.append(line)
    except Exception as e:
        raise type(e)(("Error around %d%s row of VALD3 file" %
            (r, a99.ordinal_suffix(r)))+": "+str(e)).with_traceback(sys.exc_info()[2])
    _logger.debug("VALD3-to-atoms conversion successful!")
    _logger.info("Number of lines skipped (molecules): %d" % num_skip_mol)
    _logger.info("Number of lines skipped (ioni > 2): %d" % num_skip_ioni)
    _logger.debug("Number of (element+ioni): %s" % len(ret))
    _logger.debug("Total number of atomic lines: %d" % (sum(len(a) for a in ret.atoms),))
    return ret


