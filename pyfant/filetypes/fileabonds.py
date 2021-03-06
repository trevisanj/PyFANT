__all__ = ["FileAbonds"]

import struct
import a99
from f311 import DataFile
from ..basic import adjust_atomic_symbol
import re
from .filedissoc import FileDissoc
import tabulate
import pyfant

class FileAbonds(DataFile):
    """PFANT Stellar Chemical Abundances"""

    default_filename = "abonds.dat"
    attrs = ["notes", "ele", "abol", "notes_per_ele"]
    editors = ["abed.py", "x.py"]

    def __init__(self):
        DataFile.__init__(self)
        # list of atomic symbols
        self.ele = []
        # corresponding abundances
        self.abol = []
        # notes per element, ignored by pfant
        self.notes_per_ele = []
        # overall
        self.notes = ""

    def __str__(self):
        data = zip(self.ele, self.abol, self.notes_per_ele)
        headers = ["El", "Abund", "Notes"]

        notes = ""
        if self.notes:
            notes = "\n\nNotes\n-----\n{}".format(self.notes)

        return tabulate.tabulate(data, headers)+notes

    def __add__(self, other):
        if not isinstance(other, FileAbonds):
            raise TypeError("I don't want a {}".format(other.__class__.__name__))
        return "I dont know"

    def __len__(self):
        """Returns length of "ele" attribute."""
        return len(self.ele)

    def __getitem__(self, ele):
        """Return abundance given element symbol.

        notes_per_ele may be None if index is beyond len.
        """
        import pyfant as pf
        i = self.ele.index(pf.adjust_atomic_symbol(ele))
        return self.abol[i]

    def __setitem__(self, ele, abol):
        import pyfant as pf
        i = self.ele.index(pf.adjust_atomic_symbol(ele))
        self.abol[i] = abol

    def _do_load(self, filename):
        self.abol, self.ele, self.notes_per_ele = [], [], []

        ostr = struct.Struct("1x 2s 6s")
        with open(filename, "r") as h:
            for s in h:
                if len(s) > 0:
                    if s[0] == "1":  # sign to stop reading file
                        if len(self) == 0:
                            # We need at least one element in order increase the amount of
                            # file validation
                            raise RuntimeError("'EOF' marker found at beginning of file, I need at least one element")

                        self.notes = s[10:].replace("<br>", "\n")
                        break
                [ele, abol, notes] = s[1:3], s[3:9], s[10:]

                if not re.search(r'[a-z]', ele, re.IGNORECASE):
                    raise RuntimeError("Invalid element symbol: '%s'" % ele.strip())

                self.ele.append(adjust_atomic_symbol(ele))
                self.abol.append(float(abol))
                self.notes_per_ele.append(notes.strip())

    def _do_save_as(self, filename):
        with open(filename, "w") as h:
            h.writelines([' %-2s%6.2f %s\n' % (self.ele[i], self.abol[i], self.notes_per_ele[i])
                          for i in range(len(self))])
            c = (" "*9)+self.notes.replace("\n", "<br>") if len(self.notes) > 0 else ""
            h.writelines(['1'+c+'\n', '1\n'])

    def get_file_dissoc(self):
        """Creates a new FileDissoc object.

        To do so, it loads the default dissoc.dat file from ftpyfant/data/default
        directory and searches for the new abundances within self using the
        element symbol as key.

        The abundance values are "corrected" by subtracting 12.

        If element is not found in self, list.index() raises.
        """

        f = FileDissoc()
        f.init_default()
        for i, elem in enumerate(f.elems):
            if elem != " H":
                try:
                    j = self.ele.index(elem)
                    f.cclog[i] = self.abol[j]-12
                except ValueError:
                    # if dissoc element is not found in abonds, will use
                    # value in default dissoc.dat
                    pass
        return f

    def get_turbospectrum_str(self):
        """Returns ((atomic number, abundance), ...) string for TurboSpectrum.

        Returns a text string to be pasted in a script that runs TurboSpectrum.

        Elements whose symbol is not found in the periodic table are skipped
        without warning.
        """

        # determines the atomic numbers of the elements
        atomic_numbers, abunda = [], []
        for symbol, abundance in zip(self.ele, self.abol):
            s = symbol.strip()
            try:
                atomic_numbers.append("%3d" % (pyfant.SYMBOLS.index(s)+1))
                abunda.append(abundance)
            except ValueError:
                pass  # skips elements whose symbol is not in the periodic table
        # sorts by atomic number
        indexes = sorted(list(range(len(atomic_numbers))), key=lambda k: atomic_numbers[k])
        # mounts string
        l = ["'INDIVIDUAL ABUNDANCES:'   '%d'" % len(indexes), "  1 12.",]+\
            ["%s %g" % (atomic_numbers[i], abunda[i]) for i in indexes]
        return "\n".join(l)

    def sort_a(self):
        """Sorts alphabetically using self.ele.

        Symbols not found in the periodic table will appear first and  orderered
        alphabetically.
        """

        indexes = sorted(list(range(len(self))), key=lambda k: self.ele[k].strip())
        self.ele = [self.ele[i] for i in indexes]
        self.abol = [self.abol[i] for i in indexes]
        self.notes_per_ele = [self.notes_per_ele[i] for i in indexes]

    def sort_z(self):
        """
        Sorts by atomic number.

        Symbols not found in the periodic table will appear first.

        Returns: list with those symbols not found in the periodic table.
        """

        # first determines the atomic numbers of the elements
        atomic_numbers = []
        not_found = []
        for symbol in self.ele:
            s = symbol.strip()
            try:
                atomic_numbers.append("%3d" % (pyfant.SYMBOLS.index(s)+1))
            except ValueError:
                atomic_numbers.append("    "+s)
                not_found.append(symbol)

        indexes = sorted(list(range(len(atomic_numbers))), key=lambda k: atomic_numbers[k])
        self.ele = [self.ele[i] for i in indexes]
        self.abol = [self.abol[i] for i in indexes]
        self.notes_per_ele = [self.notes_per_ele[i] for i in indexes]

        return not_found


    # def make_dissoc(self):
    #     """Creates a new FileDissoc object.
    #
    #     Returns (file_dissoc, log), where
    #      - file_dissoc is a FileDissoc instance,
    #      - log is a list with this structure:
    #        [(element, dissoc abundance, message string), ...]
    #        if all atomic symbols are found in self, log will be an empty list.
    #        Otherwise it will contain the registry of the elements not found
    #        in self.
    #
    #     To do so, it loads the default dissoc.dat file from ftpyfant/data/default
    #     directory and searches for the new abundances within self using the
    #     element symbol as key.
    #
    #     The abundance values are "corrected" by subtracting 12.
    #     """
    #
    #     f, log = FileDissoc(), []
    #     f.init_default()
    #     for i, elem in enumerate(f.elems):
    #         try:
    #             j = self.ele.index(elem)
    #             f.cclog[i] = self.abol[j]-12
    #         except ValueError:
    #             log.append((elem, f.cclog[i],
    #              "Element \"%s\", kept original %g" % (elem, f.cclog[i])))
    #     return f, log


