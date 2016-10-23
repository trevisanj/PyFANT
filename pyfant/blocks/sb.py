__all__ = ["Rubberband", "AddNoise", "FNuToFLambda", "ElementWise", "Extend", ]


import numpy as np
from pyfant import *
from pyfant.datatypes.filesplist import SpectrumList
import copy
from .base import *

class Rubberband(SpectrumBlock):
    """
    Convex polygonal line (aka "rubberband")

    Arguments:
        flag_upper=True -- whether to stretch rubberband from above the
            spectrum; otherwise, stretches line from below

    Stretches a polygonal line from below/above the spectrum. The vertices of this multi-segment
    line will touch "troughs" of the spectrumvx without crossing the spectrum

    This was inspired on -- but is not equivalent to -- OPUS Rubberband baseline correction [1].
    However, this one is parameterless, whereas OPUS RBBC asks for a number of points

    References:
        [1] Bruker Optik GmbH, OPUS 5 Reference Manual. Ettlingen: Bruker, 2004.
    """

    def __init__(self, flag_upper=True):
        SpectrumBlock.__init__(self)
        # Upper or lower rubberband
        self.flag_upper = flag_upper

    def _do_use(self, inp):
        output = self._new_output()
        y = inp.y
        if self.flag_upper:
            y = -y
        output.y = rubberband(y)
        if self.flag_upper:
            output.y = -output.y
        return output


class AddNoise(SpectrumBlock):
    """
    Adds normally distributed (Gaussian) random noise

    Arguments:
        std=1. -- standard deviation of Gaussian noise
    """
    def __init__(self, std=1.):
        SpectrumBlock.__init__(self)
        # Standard deviation of noise
        self.std = std

    def _do_use(self, inp):
        n = len(inp)
        output = self._new_output()
        output.y = np.copy(inp.y) + np.random.normal(0, self.std, n)
        return output


class FNuToFLambda(SpectrumBlock):
    """
    Flux-nu to flux-lambda conversion. Assumes the wavelength axis is in angstrom
    """
    def _do_use(self, inp):
        raise NotImplementedError()
        output = self._new_output()
        output.y = inp.y


class ElementWise(SpectrumBlock):
    """
    Applies specified function to spectrum flux

    Arguments:
        func -- a function that takes a vector (_i.e._, NumPy 1-D array) as input. It must return
            vector of same dimension as input.NumPy ufunc's are suited for this.
            Examples:
                np.square
                np.exp
            It also be a lambda using list comprehension, for example:
                lambda v: [x**2 for x in v]
    """

    def __init__(self, func):
        SpectrumBlock.__init__(self)
        self.func = func

    def _do_use(self, inp):
        output = self._new_output()
        output.wavelength = np.copy(inp.wavelength)
        output.flux = self.func(inp.flux)
        if len(output.flux) != len(output.wavelength):
            raise RuntimeError(
                "func returned vector of length %d, but should be %d" % (len(output.flux), len(output.wavelength)))
        if not isinstance(output.flux, np.ndarray):
            output.flux = np.array(output.flux)
        return output


class Extend(SpectrumBlock):
    """
    Extends to left and/or right side

    Arguments:
        fraction -- amount relative to number of points. Note that this
                    applies individually to left and right (see below)
        flag_left -- whether to extend by fraction to left
        flag_right -- whether to extend by fraction to right

    The y-value to use is found by using a "coarse" 2nd-order polynomial baseline.
    The baseline is "coarse" because it does not allow for many iterations until the
    baseline is found

    Examples:
        Extend(.1, True, True)  # if original has 100 points, resulting will have 120 points

        Extend(.1, True, False)  # if original has 100 points, resulting will have 110 points
    """

    def __init__(self, fraction=.1, flag_left=True, flag_right=False):
        SpectrumBlock.__init__(self)
        self.fraction = fraction
        self.flag_left = flag_left
        self.flag_right = flag_right

    def _do_use(self, inp):
        output = self._copy_input(inp)

        if not (self.flag_left or self.flag_right):
            return output
        num_add = int(self.fraction*len(output.wavelength))
        if num_add <= 0:
            return output

        x_left, x_right, y_left, y_right = np.array([]), np.array([]), np.array([]), np.array([])

        rubber = -poly_baseline(-output.y, 2, maxit=15)

        if self.flag_left:
            x_left = np.arange(num_add)*output.delta_lambda+(output.x[0]-output.delta_lambda*num_add)
            y_left = np.ones(num_add)*rubber[0]

        if self.flag_right:
            x_right = np.arange(num_add) * output.delta_lambda + (output.x[-1] + output.delta_lambda)
            y_right = np.ones(num_add) * rubber[-1]

        output.x = np.concatenate((x_left, output.x, x_right))
        output.y = np.concatenate((y_left, output.y, y_right))

        return output

