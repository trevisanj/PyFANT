from PyQt4.QtCore import *
from PyQt4.QtGui import *
import astroapi as aa
import pyfant as pf
# from a_WState import WState
# import moldb as db
from .a_WStateConst import WStateConst
from .a_WMolConst import WMolConst
from . import hapi
import os
import datetime


class _DataSource(aa.AttrsPart):
    """Represents a data source for molecular lines"""

    def __init__(self, name):
        aa.AttrsPart.__init__(self)
        self.name = name
        self.widget = None

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.name)


_SOURCES = [_DataSource("HITRAN"),
            _DataSource("TurboSpectrum"),
            _DataSource("Kurucz")]


class _WSource(aa.WBase):
    """Lists sources for molecular lines data"""


    @property
    def index(self):
        return self._get_index()

    @index.setter
    def index(self, x):
        self._buttons[x].setChecked(True)

    @property
    def source(self):
        """Returns _DataSource object or None"""
        i = self._get_index()
        if i < 0:
            return None
        return _SOURCES[i]

    index_changed = pyqtSignal()

    def __init__(self, *args):
        aa.WBase.__init__(self, *args)

        self._buttons = []
        self._last_index = -1

        lw = QVBoxLayout()
        self.setLayout(lw)

        for ds in _SOURCES:
            b = self.keep_ref(QRadioButton(ds.name))
            b.clicked.connect(self._button_clicked)
            self._buttons.append(b)
            lw.addWidget(b)

    def _button_clicked(self):
        i = self._get_index()
        if i != self._last_index:
            self._last_index = i
            self.index_changed.emit()


    def _get_index(self):
        for i, b in enumerate(self._buttons):
            assert isinstance(b, QRadioButton)
            if b.isChecked():
                return i
        return -1


class _WSelectSaveFile(aa.WBase):
    @property
    def value(self):
        return self._get_value()

    @value.setter
    def value(self, x):
        self.edit.setText(x)

    # # Emitted whenever the valu property changes **to a valid value**
    wants_auto = pyqtSignal()

    def __init__(self, *args):
        aa.WBase.__init__(self, *args)

        self._last_value = None

        self._type = None
        self.dialog_title = "Save output as"
        self.dialog_path = "."
        self.dialog_wild = "*.*;;*.dat"

        lw = QHBoxLayout()
        self.setLayout(lw)

        t = self.label = self.keep_ref(QLabel("Save output as"))
        lw.addWidget(t)

        e = self.edit = QLineEdit()
        e.textChanged.connect(self.edit_changed)
        t.setBuddy(e)
        lw.addWidget(e)
        # e.setReadOnly(True)

        b = self.button_auto = QToolButton()
        lw.addWidget(b)
        b.clicked.connect(self.wants_auto)
        b.setIcon(aa.get_icon("leaf-plant"))
        b.setFixedWidth(30)

        b = self.button = QToolButton()
        lw.addWidget(b)
        b.clicked.connect(self.on_button_clicked)
        b.setIcon(aa.get_icon("document-save"))
        b.setFixedWidth(30)

        # Forces paint red if invalid
        self.edit_changed()

    def on_button_clicked(self, _):
        self._on_button_clicked()

    def edit_changed(self):
        flag_valid = self.validate()
        aa.style_widget_valid(self.edit, not flag_valid)
        # if flag_valid:
        #     self._wanna_emit()

    def validate(self):
        """Returns True/False whether value is valid, i.e., existing file or directory"""
        value = self._get_value().strip()
        return len(value) > 0 and not os.path.isdir(value)

    def _on_button_clicked(self):
        path_ = self.edit.text().strip()
        if len(path_) == 0:
            path_ = self.dialog_path
        res = QFileDialog.getSaveFileName(self, self.dialog_title, path_, self.dialog_wild)
        if res:
            self.edit.setText(res)
            self.dialog_path = res

    # def _wanna_emit(self):
    #     value_now = self._get_value()
    #     if value_now != self._last_value:
    #         self._last_value = value_now
    #         self.valueChanged.emit()

    def _get_value(self):
        return self.edit.text().strip()



class _WHitranPanel(aa.WBase):

    @property
    def data(self):
        """
        Returns value in hapi.LOCAL_TABLE_CACHE, or None. This variable is a dictionary

        See hapi.py for structure of this variable
        """
        idx = self.tableWidget.currentRow()
        if idx < 0:
            return None
        return hapi.LOCAL_TABLE_CACHE[self.tableWidget.item(idx, 0).text()]

    def __init__(self, *args):
        aa.WBase.__init__(self, *args)

        self._flag_populating = False

        lw = QVBoxLayout()
        self.setLayout(lw)

        lw.addWidget(self.keep_ref(QLabel(_SOURCES[0].name)))


        w = self.w_dir = aa.WSelectDir(self.parent_form)
        w.label.setText("HITRAN 'data cache' directory")
        w.valueChanged.connect(self.dir_changed)
        lw.addWidget(w)

        a = self.tableWidget = QTableWidget()
        lw.addWidget(a)
        a.setSelectionMode(QAbstractItemView.SingleSelection)
        a.setSelectionBehavior(QAbstractItemView.SelectRows)
        a.setEditTriggers(QTableWidget.NoEditTriggers)
        a.setFont(aa.MONO_FONT)
        a.setAlternatingRowColors(True)
        a.currentCellChanged.connect(self.on_tableWidget_currentCellChanged)

        # forces populate table with 'Python HITRAN API data cache' in local directory
        self.dir_changed()

    def on_tableWidget_currentCellChanged(self, curx, cury, prevx, prevy):
        print("OLEOLEOLA", curx, cury, prevx, prevy)

    def dir_changed(self):
        print("dir_changed Ahhh nego", self.w_dir.value)
        self._populate()


    def _populate(self):
        self._flag_populating = True
        try:
            # Changed HAPI working directory
            hapi.VARIABLES['BACKEND_DATABASE_NAME'] = self.w_dir.value
            # Loads all molecular lines data to memory
            hapi.loadCache()

            # Discounts "sampletab" table from HAPI cache, hence the "-1" below
            nr, nc = len(hapi.LOCAL_TABLE_CACHE)-1, 2
            t = self.tableWidget
            aa.reset_table_widget(t, nr, nc)
            t.setHorizontalHeaderLabels(["Table filename (.data & .header)", "Number of spectral lines"])

            i = 0
            for h, (name, data) in enumerate(hapi.LOCAL_TABLE_CACHE.items()):
                if name == "sampletab":
                    continue

                header = data["header"]

                item = QTableWidgetItem(name)
                t.setItem(i, 0, item)

                item = QTableWidgetItem(str(header["number_of_rows"]))
                t.setItem(i, 1, item)

                i += 1

            t.resizeColumnsToContents()

            # self._data = rows
            #
            # if restore_mode == "formula":
            #     if curr_row:
            #         self._find_formula(curr_row["formula"])
            # elif restore_mode == "index":
            #     if -1 < curr_idx < t.rowCount():
            #         t.setCurrentCell(curr_idx, 0)
        finally:
            self._flag_populating = False
            # self._wanna_emit_id_changed()



class _WTurboSpectrumPanel(aa.WBase):
    def __init__(self, *args):
        aa.WBase.__init__(self, *args)

        lw = QVBoxLayout()
        self.setLayout(lw)

        lw.addWidget(self.keep_ref(QLabel(_SOURCES[1].name)))


class _WKuruczPanel(aa.WBase):
    def __init__(self, *args):
        aa.WBase.__init__(self, *args)

        lw = QVBoxLayout()
        self.setLayout(lw)

        lw.addWidget(self.keep_ref(QLabel(_SOURCES[2].name)))


class XConvMol(aa.XLogMainWindow):
    def __init__(self, *args):
        aa.XLogMainWindow.__init__(self, *args)

        tw0 = self.keep_ref(QTabWidget())
        self.setCentralWidget(tw0)

        # # First tab: polluted!!

        sp = self.keep_ref(QSplitter(Qt.Vertical))
        tw0.addTab(sp, "Molecular constants (Alt+&1)")

        # ## First widget of splitter
        w0 = self.keep_ref(QWidget())
        l0 = QVBoxLayout(w0)
        l0.setMargin(2)
        l0.setSpacing(2)

        a = self.title_mol = QLabel(aa.format_title0("Select a molecule:"))
        l0.addWidget(a)

        w = self.w_mol = WMolConst(self)
        w.layout().setContentsMargins(15, 1, 1, 1)
        w.id_changed.connect(self.mol_id_changed)
        l0.addWidget(w)


        # ## Second widget of splitter
        w1 = self.keep_ref(QWidget())
        l1 = QVBoxLayout(w1)
        l1.setMargin(2)
        l1.setSpacing(2)

        a = self.title_state = self.keep_ref(QLabel(aa.format_title0("States")))
        l1.addWidget(a)

        w = self.w_state = WStateConst(self)
        w.layout().setContentsMargins(15, 1, 1, 1)
        l1.addWidget(w)

        sp.addWidget(w0)
        sp.addWidget(w1)


        # # Second tab: files

        w = self.keep_ref(QWidget())
        tw0.addTab(w, "Conversion (Alt+&2)")


        # ## Vertical layout: source and destination stacked
        lsd = self.keep_ref(QVBoxLayout(w))

        # ### Horizontal layout: sources radio buttons, source-specific setup area

        lh = self.keep_ref(QHBoxLayout())
        lsd.addLayout(lh)

        # #### Vertical layout: source radio group box

        lss = QVBoxLayout()
        lh.addLayout(lss)

        # ##### Source radio buttons
        lss.addWidget(self.keep_ref(QLabel("<b>Source</b>")))
        w = self.w_source = _WSource(self)
        w.index_changed.connect(self.source_changed)
        lss.addWidget(w)
        lss.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))


        # #### Adds configuration panels for various sources
        # Only one panel should be visible at a time
        p0 = self.w_hitran = _WHitranPanel(self)
        p1 = self.w_turbo = _WTurboSpectrumPanel(self)
        p2 = self.w_kurucz = _WKuruczPanel(self)
        pp = [p0, p1, p2]
        for ds, p in zip(_SOURCES, pp):
            ds.widget = p
            lh.addWidget(p)


        # tw1 = self.wt_source = QTabWidget()
        # lh.addWidget(tw1)
        # tw1.addTab(self.keep_ref(QLabel(_SOURCES[0].name)), _SOURCES[0].name)
        # tw1.addTab(self.keep_ref(QLabel(_SOURCES[1].name)), _SOURCES[1].name)
        # tw1.addTab(self.keep_ref(QLabel(_SOURCES[2].name)), _SOURCES[2].name)


        # ### Output file specification

        w0 = self.w_out = _WSelectSaveFile(self)
        w0.wants_auto.connect(self.wants_auto)
        lsd.addWidget(w0)

        # ### "Convert" button

        lmn = QHBoxLayout()
        lsd.addLayout(lmn)
        lmn.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        b = self.button_convert = QPushButton("&Run Conversion")
        b.clicked.connect(self.convert_clicked)
        lmn.addWidget(b)


        # # Log facilities

        sb = self.statusBar()
        l = self.label_last_log = QLabel()
        sb.addWidget(l)

        w = self.textEdit_log = QTextEdit()
        w.setReadOnly(True)
        tw0.addTab(w, "Log messages (Alt+&L)")

        # # Final adjustments

        tw0.setCurrentIndex(1)
        # Forces only one of the source panels to visible
        self.w_source.index = 0
        self.source_changed()

        aa.nerdify(self)


    def wants_auto(self):
        idx = self.w_source.index
        filename = None
        if idx == 0:
            lines = self.w_hitran.data
            if lines:
                filename = "{}.dat".format(lines["header"]["table_name"])

        if filename is None:
            # Default
            filename = aa.new_filename("mol", "dat")

        self.w_out.value = filename



    def source_changed(self):
        idx = self.w_source.index
        print("SOURCE IS NOW ", _SOURCES[idx])
        for i, ds in enumerate(_SOURCES):
            pass
            ds.widget.setVisible(i == idx)
            print("Widget", ds.widget, "is visible?", ds.widget.isVisible())

    def mol_id_changed(self):
        id_ = self.w_mol.w_mol.id
        row = self.w_mol.w_mol.row
        self.w_state.set_id_molecule(id_)
        s = "States (no molecule selected)" if not row else "Select a State for molecule '{}'".format(row["formula"])
        self.title_state.setText(aa.format_title0(s))

    def convert_clicked(self):
        try:
            errors = []
            idx = self.w_source.index
            mol_row = self.w_mol.row
            mol_consts = self.w_mol.constants
            state_consts = self.w_state.constants
            filename = self.w_out.value
            if not mol_row:
                errors.append("Molecule not selected")
            if any([x is None for x in mol_consts.values()]):
                errors.append("There are empty molecule-wide constants")
            if any([x is None for x in state_consts.values()]):
                errors.append("There are empty state-wide constants")
            if not self.w_out.validate():
                errors.append("Output filename is invalid")

            lines, sols_calculator = None, None
            if len(errors) == 0:
                # Source-dependant calculation of "sets of lines"
                if idx == 0:
                    lines = self.w_hitran.data

                    if lines is None:
                        errors.append("HITRAN table not selected")
                    else:
                        sols_calculator = pf.hitran_to_sols
                else:
                    aa.show_message("{}-to-PFANT conversion not implemented yet, sorry".
                                    format(_SOURCES[idx].name))
                    return

            if len(errors) == 0:
                # Finnaly the conversion to PFANT molecular lines file

                # TODO **MAYBE NOT TIO-LIKE***
                f = pf.make_file_molecules(mol_row, mol_consts, state_consts, lines,
                                           pf.calc_qgbd_tio_like, sols_calculator)
                f.save_as(filename)

                self.add_log("File '{}' generated successfully")
            else:
                aa.show_error("Cannot convert:\n  - " + ("\n  - ".join(errors)))

        except Exception as e:
            aa.get_python_logger().exception("Conversion failed")
            self.add_log_error("Conversion failed: {}".format(aa.str_exc(e)), True)
