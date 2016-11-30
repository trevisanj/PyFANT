
from astroapi import Vis
import astroapi as aa
from pyfant.datatypes import *

class VisModRecord(Vis):
    """
    Plots vectors (nh, teta, pe, pg, log_tau_ross) of ".mod" file in 5 subplots sharing
    the same x-axis.
    """

    input_classes = (FileModBin,)
    action = "Visualize single record"

    def __init__(self):
        Vis.__init__(self)
        # 1-based (first is 1 (as in Fortran), not 0) record index in .mod file
        self.inum = None

    def _do_use(self, obj):
        assert isinstance(obj, FileModBin)
        n = len(obj.records)

        if n == 1 and self.inum is None:
            self.inum = 1
        if n > 1 and self.inum is None:
            inum, ok = QInputDialog.getInt(None, "Record number",
             "Enter record number (1 to %d)" % n, 1, 1, n)
            if ok:
                self.inum = inum

        if self.inum is not None:
            r = obj.records[self.inum-1]
            _plot_mod_record("%s - %s" % (self.title, repr(r)), r)


class VisMarcs(Vis):
    """
    Similar to VisModRecord but accepts FileModTxt
    """

    input_classes = (FileModTxt,)
    action = "Visualize model"

    def __init__(self):
        Vis.__init__(self)

    def _do_use(self, obj):
        _plot_mod_record(self.title, obj.record)


class VisMarcsSaveAsMod(Vis):
    """
    Asks user for file name and saves as a binary .mod file
    """

    input_classes = (FileModTxt,)
    action = 'Save as a binary ".mod" file'

    def __init__(self):
        Vis.__init__(self)

    def _do_use(self, obj):
        d = "."  # todo find a way to pass current directory in a_Xexplorer (not pwd)
        new_filename = QFileDialog.getSaveFileName(None,
         self.action.capitalize(), d, "*.mod")
        if new_filename:
            f = FileModBin()
            f.records = [obj.record]
            f.save_as(str(new_filename))
        return False


def _plot_mod_record(title, r):
    f, axarr = plt.subplots(5, sharex=True)
    f.canvas.set_window_title(title)
    x = np.linspace(1, r.ntot, r.ntot)

    axarr[0].plot(x, r.nh)
    axarr[0].set_ylabel('nh')
    axarr[1].plot(x, r.teta)
    axarr[1].set_ylabel('teta')
    axarr[2].plot(x, r.pe)
    axarr[2].set_ylabel('pe')
    axarr[3].plot(x, r.pg)
    axarr[3].set_ylabel('pg')
    axarr[4].plot(x, r.log_tau_ross)
    axarr[4].set_ylabel('log_tau_ross')
    axarr[4].set_xlabel("Atmospheric layer #")
    for i in range(5):
        ax = axarr[i]
        ax.set_xlim([.5, r.ntot+.5])
    plt.tight_layout()
    plt.show()


class VisModCurves(Vis):
    """
    Plots vectors
    (teff, glog, asalog, asalalf, nhe) in 2D (record #)x(value) plots, and
    (nh, teta, pe, pg, log_tau_ross) (layer #)x(record #)x(value) 3D plots
    """

    input_classes = (FileMoo, FileModBin)
    action = "(nh, teta, pe, pg, log_tau_ross) per layer curves in 3D"

    def _do_use(self, m):
        nr = len(m)

        #################
        # 3D plots
        vars = ['nh', 'teta', 'pe', 'pg', 'log_tau_ross']
        for var in vars:

            fig = plt.figure()
            if self.parent_form:
                fig.canvas.setParent(self.parent_form)
            ax = fig.gca(projection='3d')
            fig.canvas.set_window_title('%s -- %s' % (self.title, var))
            rr = m.records

            for i, r in enumerate(rr):
                x = np.linspace(1, r.ntot, r.ntot)
                y = np.ones(len(x)) * (i + 1)
                z = r.__getattribute__(var)
                ax.plot(x, y, z, label='a', color='k')

            ax.set_xlabel('Atmospheric layer #')
            ax.set_ylabel('Record number')
            ax.set_zlabel(var)

        plt.show()


class VisGrid(Vis):
    __doc__ = """(glog, teff, [Fe/H]) 3D scatterplot"""

    input_classes = (FileMoo, FileModBin)
    action = __doc__

    def _do_use(self, m):
        asalog, teff, glog = [], [], []
        for r in m.records:
            asalog.append(r.asalog)
            teff.append(r.teff)
            glog.append(r.glog)

        # teff-glog-asalog scatterplot
        fig = plt.figure()
        ax = fig.gca(projection='3d')
        ax.scatter(asalog, teff, glog, c='r', s=60, marker='o')
        ax.set_xlabel('asalog ([Fe/H] relative to Sun)')
        ax.set_ylabel('teff')
        ax.set_zlabel('glog')
        fig.canvas.set_window_title(self.title+" -- asalog-teff-glog scatterplot")
        plt.tight_layout()
        plt.show()


class VisVector(Vis):
    __doc__ = """(glog, teff, [Fe/H]) same-x-axis stacked subplots"""

    input_classes = (FileMoo, FileModBin)
    action = __doc__

    def _do_use(self, m):
        asalog, teff, glog = [], [], []
        for r in m.records:
            asalog.append(r.asalog)
            teff.append(r.teff)
            glog.append(r.glog)

        # 3 subplots sharing same x-axis
        aa = ['asalog', 'teff', 'glog']
        f, axarr = plt.subplots(len(aa), sharex=True)
        nr = len(asalog)
        x = np.linspace(1, nr, nr)
        rr = m.records
        for i, a in enumerate(aa):
            v = eval(a)
            axarr[i].plot(x, v)
            axarr[i].set_ylabel(a)
        axarr[len(aa)-1].set_xlabel("Record #")
        f.canvas.set_window_title("%s -- %s" % (self.title, 'one-value-per-model'))
        plt.tight_layout()

        plt.show()


class VisFileToH(Vis):
    """
    Plots hydrogen lines: each atmospheric layer is plotted as a y-axis-dislocated
    Spectrum in a 3D plot.
    """

    input_classes = (FileToH,)
    action = "Visualize hydrogen lines profiles"

    def _do_use(self, r):
        fig = plt.figure()
        mpl.rcParams['legend.fontsize'] = 10
        fig.canvas.set_window_title(self.title)  # requires the Axes3D module
        ax = fig.gca(projection='3d')
        x = np.concatenate((2 * r.lambdh[0] - r.lambdh[-2::-1], r.lambdh))
        _y = np.ones(len(x))
        for i in range(r.th.shape[1]):
            z = np.concatenate((r.th[-2::-1, i], r.th[:, i]))
            # ax.plot(x, _y * (i + 1), np.log10(z), label='a', color='k')
            ax.plot(x, _y * (i + 1), z, label='a', color='k')
        ax.set_xlabel('Wavelength ($\AA$)')
        ax.set_ylabel("Atmospheric layer #")
        # ax.set_zlabel('log10(Intensity)')
        # ax.set_zlabel('?')
        plt.tight_layout()
        plt.show()


class VisOpa(Vis):
    """
    Visualizer for FileOpa class

    Plots vectors ???
    """

    input_classes = (FileOpa,)
    action = "Visualize opacities file"

    def _do_use(self, obj):
        assert isinstance(obj, FileOpa)

        # 8 subplots sharing same x-axis
        aa = ["rad", "tau", "t", "pe", "pg", "rho", "xi", "ops"]
        titles = ["spherical radiative transfer",
                  "continuumm optical depth at %g angstrom" % obj.swave,
                  "temperature (K)",
                  "electron pressure (dyn/cm**2)",
                  "total gas pressure (dyn/cm**2)",
                  "densigy (g/cm**3)",
                  "microturbulence parameter (km/s)",
                  "continuumm opacity at %g angstrom (cm**2/g)" % obj.swave]

        f, axarr = plt.subplots(nrows=4, ncols=2, sharex=True)
        x = np.linspace(1, obj.ndp, obj.ndp)
        i = 0
        for m in range(4):
            for n in range(2):
                a = aa[i]
                ax = axarr[m, n]
                ax.plot(x, obj.__getattribute__(a))
                ax.set_title("%s: %s" % (a, titles[i]))

                i += 1
        axarr[3, 0].set_xlabel("Layer #")
        axarr[3, 1].set_xlabel("Layer #")

        f.canvas.set_window_title("%s -- %s" % (self.title, 'one-value-per-model'))
        plt.tight_layout()

        #################
        # 3D plots
        vars = ["abs", "sca"]
        titles = ["specific continuous absorption opacity (cm**2/g)",
                  "specific continuous scattering opacity (cm**2/g)"]

        for var, title in zip(vars, titles):
            attr = obj.__getattribute__(var)
            x = np.log10(obj.wav)

            fig = plt.figure()
            if self.parent_form:
                fig.canvas.setParent(self.parent_form)
            ax = fig.gca(projection='3d')
            fig.canvas.set_window_title('%s -- %s' % (self.title, var))

            for k in range(obj.ndp):
                y = np.ones(len(x)) * (k + 1)
                # z = attr[:, k]
                z = np.log10(attr[:, k])
                ax.plot(x, y, z, label='a', color='k')
                # ax.set_xscale("log")
                # ax.semilogx(x, y, z, label='a', color='k')

            ax.set_xlabel('log10(wavelength)')
            ax.set_ylabel('Layer #')
            ax.set_zlabel('log10(%s)' % var)
            ax.set_title("%s: %s" % (var, title))

        plt.show()



# # Editors

class VisAtoms(Vis):
    """Opens the ated window."""
    input_classes = (FileAtoms,)
    action = "Edit using atomic lines editor"

    def _do_use(self, r):
        from pyfant.gui import XFileAtoms
        form = XFileAtoms(self.parent_form)
        _forms.append(form)
        form.load(r)
        form.show()


class VisMolecules(Vis):
    """Opens the mled window."""
    input_classes = (FileMolecules,)
    action = "Edit using molecular lines editor"

    def _do_use(self, r):
        from pyfant.gui import XFileMolecules
        form = XFileMolecules(self.parent_form)
        _forms.append(form)
        form.load(r)
        form.show()


class VisMain(Vis):
    """Opens the mained window."""
    input_classes = (FileMain,)
    action = "Edit using main configuration file editor"

    def _do_use(self, r):
        from pyfant.gui import XFileMain
        form = XFileMain(self.parent_form, r)
        _forms.append(form)
        form.show()


class VisAbonds(Vis):
    """Opens the abed window."""
    input_classes = (FileAbonds,)
    action = "Edit using abundances file editor"

    def _do_use(self, r):
        from pyfant.gui import XFileAbonds
        form = XFileAbonds(self.parent_form, r)
        _forms.append(form)
        form.show()