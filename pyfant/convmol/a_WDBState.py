from PyQt4.QtCore import *
from PyQt4.QtGui import *
from . import moldb as db
from astroapi import WDBRegistry
import astroapi as aa


__all__ = ["WDBState"]


# Field names to leave out of table widget
_FIELDNAMES_OUT = ("formula", "id_molecule")


class WDBState(WDBRegistry):
    """Registry for table 'state'"""


    def __init__(self, *args):
        WDBRegistry.__init__(self, *args)

        self._id_molecule = None
        # List of field names to appear as columns in the table widget, as well as the ones that will be edited
        # (does not know this list beforehand, decided to make this generic)
        self._fieldnames = []


    def set_id_molecule(self, id_):
        """Sets molecule id and re-populates table"""
        self._id_molecule = id_
        self._populate()


    def find_formula(self, formula):
        """Moves to row where formula is (if found, otherwise does nothing)"""
        for i, row in enumerate(self._data):
            if row["formula"] == formula:
                self.tableWidget.setCurrentCell(i, 0)
                break


    def _populate(self, restore_mode=None):
        """
        Populates table widget & self._fieldnames

        Args:
            restore_mode: how to reposition cursor:
                "index": tries to restore same row index
                anything else: does not re-position
        """
        self._flag_populating = True
        try:
            curr_idx = self.tableWidget.currentRow()

            t = self.tableWidget
            rows = aa.cursor_to_rows(db.query_states(id_molecule=self._id_molecule))
            ti = aa.get_table_info("state")
            fieldnames = [name for name in ti if name not in _FIELDNAMES_OUT]
            # unfortunately QTableWidget is not prepared to show HTML col_names = [row["caption"] or row["name"] for row in ti if not row["name"] in FIELDNAMES_OUT]
            col_names = fieldnames
            nr, nc = len(rows), len(fieldnames)

            aa.ResetTableWidget(t, nr, nc)
            t.setHorizontalHeaderLabels(col_names)

            if nr > 0:
                for i, row in enumerate(rows):
                    for j, fieldname in enumerate(fieldnames):
                        cell = row[fieldname]
                        item = QTableWidgetItem("" if cell is None else str(cell))
                        t.setItem(i, j, item)
            t.resizeColumnsToContents()
            self._data = rows

            if restore_mode == "index":
                if -1 < curr_idx < t.rowCount():
                    t.setCurrentCell(curr_idx, 0)
        finally:
            self._flag_populating = False
            self._wanna_emit_id_changed()

    def _get_edit_params(self):
        """Returns a Parameters object containing information about the fields that may be edited"""
        ti = aa.get_table_info("state")
        params = aa.table_info_to_parameters(ti)
        params = [p for p in params if not p.name.startswith("id")]
        return params

    def _get_edit_field_names(self):
        """Returns a list with the names of the fields that may be edited"""
        params = self._get_edit_params()
        ret = [p.name for p in params]
        return ret

    def _do_on_insert(self):
        params = self._get_edit_params()
        form = aa.XParametersEditor(specs=params, title="Insert Molecular State")
        r = form.exec_()
        if r == QDialog.Accepted:
            kwargs = form.get_kwargs()
            conn = db.get_conn()
            s = "insert into state (id_molecule, {}) values ({}, {})".\
                format(", ".join([p.name for p in params]),
                       self._id_molecule,
                       ", ".join(["?"*len(params)]))
            _ = conn.execute(s, list(kwargs.values()))
            conn.commit()
            self._populate(False)
            self.find_formula(kwargs["formula"])


    def _do_on_edit(self):
        r, form = aa.show_edit_form(self.row, self._get_edit_field_names(), "Edit Molecular State")
        if r == QDialog.Accepted:
            kwargs = form.get_kwargs()
            id_ = self.row["id"]
            s = "update state set {} where id = {}".format(
                ", ".join(["{} = '{}'".format(a, b) for a, b in kwargs.items()]), id_)
            conn = db.get_conn()
            conn.execute(s)
            conn.commit()
            self._populate()
            self._find_id(id_)


    def _do_on_delete(self):
        r = QMessageBox.question(None, "Delete Molecular State",
                                 "Are you sure?",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if r == QMessageBox.Yes:
            conn = db.get_conn()
            id_ = self.row["id"]
            conn.execute("delete from state where id = ?", [id_])
            conn.commit()

            self._populate("index")