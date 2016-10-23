__all__ = ["SNR", "Magnitude"]


from .base import ToScalar
import numpy as np


class SNR(ToScalar):
    """
    Calculates Signal-to-noise ratio (SNR) using a part of the "signal" (i.e. the spectrum)

    Output is **scalar**

    The signal-to-noise ratio (SNR) is often defined as (signal power) / (noise power), herein
    calculated as

        y_RMS**2 / variance(y)     (https://en.wikipedia.org/wiki/Signal-to-noise_ratio)

    It is assumed that the "signal" is *stationary* within [llzero, llfin]
    meaning that the mean and variance of the "signal" is the same for all points within
    this region (more precisely "weak-sense stationary"
    (https://en.wikipedia.org/wiki/Stationary_process#Weak_or_wide-sense_stationarity))
    """

    def __init__(self, llzero, llfin):
        ToScalar.__init__(self)
        self.llzero = llzero
        self.llfin = llfin

    def _do_use(self, inp):
        x = inp.x
        y = inp.y
        signal = y[np.logical_and(x >= self.llzero, x <= self.llfin)]

        output = np.mean(signal**2)/np.var(signal)
        return output


class Magnitude(ToScalar):
    """
    Calculates the magnitude of a spectrum

        Arguments:
            band_name -- U/B/V/R/I/Y/J/H/K/L/M/N/Q
            flag_force_parametric -- (default: False) if set, will use parametric data even for
                the tabulated bands U/B/V/R/I
            flag_always_full_band -- (default: False) if set, will consider that the spectrum
                extends over the full range of the band even if it is narrower than that
    """


    def __init__(self, band_name, flag_force_parametric=False, flag_always_full_band=False):
        ToScalar.__init__(self)
        self.band_name = band_name
        self.flag_force_parametric = flag_force_parametric
        self.flag_always_full_band = flag_always_full_band

    def _do_use(self, inp):
        temp = inp.calculate_magnitude(self.band_name, self.flag_force_parametric,
                                      self.flag_always_full_band)
        return temp["cmag"]