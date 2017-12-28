from collections import UserString
import datetime
import functools
import operator

import numpy as np

prod = functools.partial(functools.reduce, operator.mul)

def obvious_dtype(obj):
    """Return a numpy dtype in obvious precision.
    The precisou of np.intc, np.int_, and so on depends on platform,
    and sometimes these have the same precison.
    This function returns spacific unique class for them.
    
    Args:
        obj: np.dtype object or np.dtype.type
    """
    if issubclass(obj, np.number):
        pass
    elif issubclass(obj, np.dtype):
        obj = obj
    else:
        raise ValueError("Not numpy dtype object.")

    if issubclass(obj, np.bool_):
        return np.bool_

    if issubclass(obj, np.signedinteger):
        dtypes = {
            1: np.int8,
            2: np.int16,
            4: np.int32,
            8: np.int64
        }
    elif issubclass(obj, np.unsinedinteger):
        dtypes = {
            1: np.uint8,
            2: np.uint16,
            4: np.uint32,
            8: np.uint64
        }
    elif issubclass(obj, np.floating):
        dtypes = {
            2: np.float16,
            4: np.float32,
            8: np.float64
        }
    elif issubclass(obj, np.complexfloating):
        dtypes = {
            8: np.float64,
            16: np.float128
        }
    size = np.dtype(obj).itemsize
    try:
        return dtypes[size]
    except KeyError:
        raise TypeError("Unknown dtype.")

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
    # array[i_real and i_imag][j][k][l]
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

def current_time(prefix, base=36):
    result = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    result = np.base_repr(int(result), base)
    return prefix + result

# def to_unique(strings):
#     result = []
#     apd = result.append
#     for s in strings:
#         if s not in result:
#             apd(s)
#         else:
#             i = 0
#             candidate = s + str(i)
#             while candidate in result:
#                 i += 1
#             apd(candidate)
#     return result

def _str_insert(basestr, index, istr):
    return basestr[:index] + istr + basestr[index:]

def to_unique_key(strings):
    result = []
    apd = result.append
    for s in strings:
        s = s.replace("'", "")
        if s not in result:
            apd(s)
        else:
            i = 0
            candidate = _str_insert(s, s.rfind("."), "_{}".format(i))
            while candidate in result:
                i += 1
                candidate = _str_insert(s, s.rfind("."), "_{}".format(i))
            apd(candidate)
    return result

BOOLS = (bool, np.bool_)
INT_NUMS = (int, np.bool_, np.integer)
REAL_NUMS = (int, float, np.bool_, np.integer, np.floating)
FLOAT_NUMS = (float, np.floating)
COMP_NUMS = (complex, np.complexfloating)

def isbool(obj):
    return isinstance(obj, BOOLS)

def isint(obj):
    return isinstance(obj, INT_NUMS)

def isreal(obj):
    return isinstance(obj, REAL_NUMS)

def isfloat(obj):
    return isinstance(obj, FLOAT_NUMS)

def iscomplex(obj):
    return isinstance(obj, COMP_NUMS)

def isstr(obj):
    return isinstance(obj, (str, UserString))