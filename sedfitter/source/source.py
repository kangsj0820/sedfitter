from __future__ import print_function, division

import cPickle as pickle

import numpy as np


def is_numpy_array(variable):
    return type(variable) in [np.ndarray,
                              np.core.records.recarray,
                              np.ma.core.MaskedArray]


def validate_1d_array(name, value):

    if type(value) in [list, tuple]:
        value = np.array(value)
    if not is_numpy_array(value) or value.ndim != 1:
        raise ValueError(name + " should be a 1-D sequence")

    return value


class Source(object):

    def __init__(self):

        self.name = ""
        self.x = 0.
        self.y = 0.
        self.valid = None
        self.flux = None
        self.error = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if value is None:
            self._name = value
        elif isinstance(value, basestring):
            self._name = value
        else:
            raise TypeError("name should be a string")

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        if value is None:
            self._x = value
        elif np.isscalar(value) and np.isreal(value):
            self._x = value
        else:
            raise TypeError("x should be a scalar floating point value")

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        if value is None:
            self._y = value
        elif np.isscalar(value) and np.isreal(value):
            self._y = value
        else:
            raise TypeError("y should be a scalar floating point value")

    @property
    def valid(self):
        return self._valid

    @valid.setter
    def valid(self, value):
        if type(value) in [list, tuple]:
            value = np.array(value)
        if value is None:
            self._valid = value
        elif isinstance(value, np.ndarray) and value.ndim == 1:
            if self.n_wav is not None and len(value) != self.n_wav:
                raise ValueError("valid has incorrect length (expected {0} but found {1})".format(self.n_wav, len(value)))
            else:
                if np.any(value.astype(int) != value):
                    raise ValueError("valid values should be integers")
                elif np.any(value < 0) or np.any(value > 4):
                    raise ValueError("valid values should be in the range [0,4]")
                else:
                    self._valid = value
        else:
            raise TypeError("valid should be a 1-d sequence")

    @property
    def flux(self):
        return self._flux

    @flux.setter
    def flux(self, value):
        if type(value) in [list, tuple]:
            value = np.array(value)
        if value is None:
            self._flux = value
        elif isinstance(value, np.ndarray) and value.ndim == 1:
            if self.n_wav is not None and len(value) != self.n_wav:
                raise ValueError("flux has incorrect length (expected {0} but found {1})".format(self.n_wav, len(value)))
            else:
                self._flux = value
        else:
            raise TypeError("flux should be a 1-d sequence")

    @property
    def error(self):
        return self._error

    @error.setter
    def error(self, value):
        if type(value) in [list, tuple]:
            value = np.array(value)
        if value is None:
            self._error = value
        elif isinstance(value, np.ndarray) and value.ndim == 1:
            if self.n_wav is not None and len(value) != self.n_wav:
                raise ValueError("error has incorrect length (expected {0} but found {1})".format(self.n_wav, len(value)))
            else:
                self._error = value
        else:
            raise TypeError("error should be a 1-d sequence")

    @property
    def n_wav(self):
        if self.valid is not None:
            return len(self.valid)
        elif self.flux is not None:
            return len(self.flux)
        elif self.error is not None:
            return len(self.error)
        else:
            return None

    @property
    def n_data(self):
        return np.sum((self.valid == 1) | (self.valid == 4))

    def get_log_fluxes(self):

        # Initialize arrays
        log_flux = np.zeros(flux.shape, dtype=np.float32)
        log_error = np.zeros(error.shape, dtype=np.float32)
        weight = np.zeros(valid.shape, dtype=np.float32)

        # Fluxes
        r = valid == 1
        log_flux[r] = np.log10(flux[r]) - 0.5 * (error[r] / flux[r]) ** 2. / np.log(10.)
        log_error[r] = np.abs(error[r] / flux[r]) / np.log(10.)
        weight[r] = 1. / log_error[r] ** 2.

        # Lower and upper limits
        r = (valid == 2) | (valid == 3)
        log_flux[r] = np.log10(flux[r])
        log_error[r] = error[r]

        # Log10[Fluxes]
        r = valid == 4
        log_flux[r] = flux[r]
        log_error[r] = error[r]
        weight[r] = 1. / log_error[r] ** 2.

        # Ignored points
        r = valid == 9
        log_flux[r] = np.log10(flux[r]) - 0.5 * (error[r] / flux[r]) ** 2. / np.log(10.)
        log_error[r] = np.abs(error[r] / flux[r]) / np.log(10.)

        return weight, log_flux, log_error

    def __str__(self):

        string = "Source name : %s\n" % self.name
        string += "RA   / l    : %9.5f\n" % self.x
        string += "Decl / b    : %9.5f\n" % self.y
        for j in range(self.n_wav):
            string += "F = %12.4e + / - %12.4e mJy (%1i)  Log[F] = %8.5f+ / -%8.5f\n" % \
                      (self.flux[j], self.error[j], self.valid[j], self.logflux[j], self.logerror[j])

        return string

    def read_ascii(self, file_handle):
        line = file_handle.readline().strip()
        if line:
            cols = line.split()
            self.name = cols[0]
            self.x = np.float64(cols[1])
            self.y = np.float64(cols[2])
            self.n_wav = np.int32((len(cols) - 3) / 3)
            self.valid = np.array(cols[3:3 + self.n_wav], dtype=np.int32)
            flux_and_error = np.array(cols[3 + self.n_wav:], dtype=np.float32)
            self.flux = flux_and_error[::2]
            self.error = flux_and_error[1::2]
            self._update_log_fluxes()
        else:
            raise IOError("End of file")

    def write_ascii(self, file_handle):
        file_handle.write("% - 30s " % self.name)
        file_handle.write("%9.5f %9.5f " % (self.x, self.y))
        file_handle.write("%1i " * self.n_wav % tuple(self.valid.tolist()))
        for j in range(self.n_wav):
            file_handle.write("%11.3e %11.3e " % (self.flux[j], self.error[j]))
        file_handle.write("\n")

    @classmethod
    def from_dict(cls, source_dict):
        s = cls()
        s.name = source_dict['name']
        s.x = source_dict['x']
        s.y = source_dict['y']
        s.valid = source_dict['valid']
        s.flux = source_dict['flux']
        s.error = source_dict['error']
        return s

    def to_dict(self):
        return {
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'valid': self.valid,
            'flux': self.flux,
            'error': self.error
        }

    def __eq__(self, other):
        return self.name == other.name and \
            self.x == other.x and \
            self.y == other.y and \
            np.all(self.valid == other.valid) and \
            np.all(self.flux == other.flux) and \
            np.all(self.error == other.error)


def read_sources(filename, n_min_valid=0):

    result = []

    data = np.loadtxt(filename, dtype=str)

    try:
        n_sources = np.shape(data)[0]
        n_wav = (np.shape(data)[1] - 3) / 3
    except:
        n_sources = 1
        n_wav = (len(data) - 3) / 3

    n = n_wav

    name = np.loadtxt(filename, usecols=[0], dtype=str)
    x = np.loadtxt(filename, usecols=[1], dtype=np.float32)
    y = np.loadtxt(filename, usecols=[2], dtype=np.float32)
    valid = np.loadtxt(filename, usecols=range(3, 3 + n), dtype=np.int32)
    flux = np.loadtxt(filename, usecols=range(3 + n, 3 + 3 * n - 1, 2), dtype=np.float32)
    error = np.loadtxt(filename, usecols=range(3 + n + 1, 3 + 3 * n, 2), dtype=np.float32)

    sources = []
    for i in range(n_sources):
        if np.sum((valid[i, :] == 1) | (valid[i, :] == 4)) > n_min_valid:
            sources.append(Source(name[i], x[i], y[i], valid[i, :], flux[i, :], error[i, :]))

    return sources
