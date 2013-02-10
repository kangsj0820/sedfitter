import numpy as np


def validate_scalar(name, value, domain=None):

    if not np.isscalar(value) or not np.isreal(value):
        raise TypeError("{0} should be a scalar floating point value".format(name))

    if domain == 'positive':
        if value < 0.:
            raise ValueError("{0} should be positive".format(name))
    elif domain == 'strictly-positive':
        if value <= 0.:
            raise ValueError("{0} should be strictly positive".format(name))
    elif domain == 'negative':
        if value > 0.:
            raise ValueError("{0} should be negative".format(name))
    elif domain == 'strictly-negative':
        if value >= 0.:
            raise ValueError("{0} should be strictly negative".format(name))
    elif type(domain) in [tuple, list] and len(domain) == 2:
        if value < domain[0] or value > domain[-1]:
            raise ValueError("{0} should be in the range [{1}:{2}]".format(name, domain[0], domain[-1]))


def validate_array(name, value, domain=None, ndim=1, shape=None):
    
    # First convert to a Numpy array:
    if type(value) in [list, tuple]:
        value = np.array(value)

    # Check the value is an array with the right number of dimensions 
    if not isinstance(value, np.ndarray) or value.ndim != ndim:
        if ndim == 1:
            raise TypeError("{0} should be a 1-d sequence".format(name))
        else:
            raise TypeError("{0} should be a {1:d}-d array".format(name, ndim))

    # Check that the shape matches that expected
    if shape is not None and value.shape != shape:
        if ndim == 1:
            raise ValueError("{0} has incorrect length (expected {1} but found {2})".format(name, shape[0], value.shape[0]))
        else:
            raise ValueError("{0} has incorrect shape (expected {1} but found {2})".format(name, shape, value.shape))

    return value