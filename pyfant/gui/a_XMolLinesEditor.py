
__all__ = ["XMolLinesEditor"]

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from ._shared import *
import a99
import pyfant


class XMolLinesEditor(QMainWindow):

    def __init__(self, parent):
        QMainWindow.__init__(self)

        # objects in matplotlib window

        self.parent = parent
        self.flag_populating = False  # activated when populating table

        a = self.tableWidget = QTableWidget()
        a.setSelectionMode(QAbstractItemView.SingleSelection)
        a.currentCellChanged.connect(self.on_tableWidget_currentCellChanged)
        a.cellChanged.connect(self.on_tableWidget_cellChanged)
        a.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        a.setFont(a99.MONO_FONT)
        a.installEventFilter(self)


        self.setCentralWidget(a)
        a99.snap_right(self, 200)

    def on_tableWidget_currentCellChanged(self, currentRow, currentColumn, previousRow,
                                          previousColumn):
        self.parent.MolLinesEditor_current_row_changed(currentRow)

    def on_tableWidget_cellChanged(self, row, column):
        if not self.flag_populating:
            item = self.tableWidget.item(row, column)
            try:
                value = float(item.text())
            except ValueError:
                # restores original value
                a99.show_error("Invalid floating point value: %s" % item.text())
                item.setText(str(self.parent.sol.__getattribute__(SOL_ATTR_NAMES[column])[row]))
            else:
                self.parent.MolLinesEditor_cell_changed(row, column, value)

    def closeEvent(self, _):
        self.parent.MolLinesEditor_closing()

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return:
                if source == self.tableWidget:
                    self.tableWidget.editItem(self.tableWidget.currentItem())
                    return True
        return False

    # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # *

    def set_sol(self, sol, title):
        """Sets set of lines."""

        assert isinstance(sol, pyfant.SetOfLines)

        self.flag_populating = True
        try:
            self.setWindowTitle(title)

            t = self.tableWidget
            n = len(sol)
            a99.reset_table_widget(t, n, len(SOL_HEADERS))
            t.setHorizontalHeaderLabels(SOL_HEADERS)

            # list with the vectors themselves
            attrs = [sol.__getattribute__(x) for x in SOL_ATTR_NAMES]

            for i in range(len(sol)):
                for j, attr in enumerate(attrs):
                    item = QTableWidgetItem(str(attr[i]))
                    t.setItem(i, j, item)

            t.resizeColumnsToContents()
        finally:
            self.flag_populating = False

    def set_row(self, i):
        t = self.tableWidget
        c = t.currentColumn()
        self.tableWidget.setCurrentCell(i, c)
