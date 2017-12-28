import functools
import operator

import numpy as np

prod = functools.partial(functools.reduce, operator.mul)

def to_list(val):
    if (not isinstance(val, str)) and hasattr(val, "__len__"):
        return list(val)
    else:
        return [val]

def to_igor_complex_wave_order(array):
    array = np.asarray(array)
    tmp_shape = list(array.shape)
    tmp_shape.insert(1, 2)
    # dtype手抜き
    result = np.empty(tmp_shape, dtype=np.float64)
    real = 0
    imag = 1
    result[:, real] = array.real
    result[:, imag] = array.imag
    tmp_shape = list(array.shape)
    tmp_shape[0] *= 2
    return result.reshape(tmp_shape)

def from_igor_complex_wave_order(array, dtype=np.complex128):
    #array[i_real and i_imag][j][k][l]
    #-> array[i_real][i_imag][j][k][l]
    array = np.asarray(array)
    shape = list(array.shape)
    shape[0] //= 2
    result = np.empty(shape, dtype=dtype)
    shape.insert(1, 2)
    array = array.reshape(*shape)

    real = 0
    imag = 1
    result.real = array[:, real]
    result.imag = array[:, imag]
    return result