__all__ = ["FileAbsoru2"]

from f311 import DataFile


class FileAbsoru2(DataFile):
    """PFANT "Absoru2" file

    Reader/writes not implemented (will be implemented when there is the need for so)"""

    default_filename = "absoru2.dat"

    def __init__(self):
        DataFile.__init__(self)

    def _do_load(self, filename):
        raise NotImplementedError("This class is a stub ATM")

    def _do_save_as(self, filename):
        raise NotImplementedError("This class is a stub ATM")
