import datetime
import functools
import logging
import operator

from collections import UserString

import numpy as np

from igorconsole.exception import IgorTypeError
from .consts import COMMAND_MAXLEN

logger = logging.getLogger(__name__)

prod = functools.partial(functools.reduce, operator.mul)

def _as_np_type(obj):
    if isinstance(obj, type) and issubclass(obj, (np.number, np.bool_, np.object_)):
        return obj
    elif isinstance(obj, np.dtype):
        return obj.type
    else:
        raise ValueError("{} is not a numpy dtype object.".format(obj))

def obvious_dtype(obj):
    """Return a numpy dtype in obvious precision.
    The precison of np.intc, np.int_, and so on depends on platform,
    and sometimes these have the same precison.
    This function returns spacific unique class for them.
    
    Args:
        obj: np.dtype object or np.dtype.type
    """

    obj = _as_np_type(obj)
    if issubclass(obj, np.bool_):
        return np.bool_

    if issubclass(obj, np.signedinteger):
        dtypes = {
            1: np.int8,
            2: np.int16,
            4: np.int32,
            8: np.int64
        }
    elif issubclass(obj, np.unsignedinteger):
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
            8: np.complex64,
            16: np.complex128
        }
    size = np.dtype(obj).itemsize
    try:
        return dtypes[size]
    except KeyError:
        raise TypeError("Unknown dtype.")

def array_dtype(array):
    return obvious_dtype(array.dtype)
NP_DTYPE = {
    0x02: np.float32,
    0x01 | 0x02: np.complex64,
    0x04: np.float64,
    0x01 | 0x04: np.complex128,
    0x08: np.int8,
    0x10: np.int16,
    0x20: np.int32,
    0x48: np.uint8,
    0x50: np.uint16,
    0x60: np.uint32,
    0x00: str
}
def to_npdtype(igor_data_type: int):
    return NP_DTYPE[igor_data_type]

IGORDTYPE = {v:k for k, v in NP_DTYPE.items()}
@functools.lru_cache(maxsize=30)
def to_igor_data_type(np_dtype):
    if isinstance(np_dtype, type) and issubclass(np_dtype, str):
        return IGORDTYPE[str]
    else:
        return _to_igor_data_type_numeric(np_dtype)

def _to_igor_data_type_numeric(np_dtype):
    np_dtype = _as_np_type(np_dtype)
    if np_dtype is np.float16:
        np_dtype = np.float32
        logger.info("implicit cast from float16 to float32.")
    dtype = obvious_dtype(np_dtype)
    try:
        returnval = IGORDTYPE[dtype]
    except KeyError:
        logger.error("Unsupported datatype. Cannot covert to igor data type.")
        raise IgorTypeError("np.dtype, {}, cannot be converted to igor data type.".format(np_dtype))
    return returnval


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

def current_time(prefix, base=36):
    result = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    result = np.base_repr(int(result), base)
    return prefix + result

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

def from_pd_DataFrame(df):
    df = df.fillna(np.nan)
    info = {
        "type": "IgorFolder",
        "version": 1,
        "subfolders": {},
    }
    if obvious_dtype(df.index.dtype) == np.int64:
        if np.all(-2**31 <= df.index) and np.all(df.index <= 2**31 - 1):
            contents = {"index": np.asarray(df.index, dtype=np.int32)}
        elif np.all(0 <= df.index) and np.all(df.index <= 2**32 - 1):
            contents = {"index": np.asarray(df.index, dtype=np.uint32)}
        elif np.all(-2**53 + 1 <= df.index) and np.all(df.index <= 2**53 - 1):
            contents = {"index": np.asarray(df.index, dtype=np.float64)}
        else:
            raise ValueError("index cannot be cast to igor dtype")
    else:
        contents = {"index": np.asarray(df.index)}
    for key, series in df.items():
        contents[str(key)] = series
    info["contents"] = contents
    return info

def to_pd_DataFrame(finfo):
    import pandas as pd
    contents = finfo["contents"]
    waves = {i: v["array"] for i, v in contents.items() if v["type"] == "IgorWave"}
    if "index" in waves:
        index = waves["index"]
        del waves["index"]
        result = pd.DataFrame.from_dict(waves)
        result.index = index
        return result
    else:
        return pd.DataFrame.from_dict(waves)

def merge_commands(commands):
    result = ""
    buff = ""
    for command in commands:
        if not command.endswith(";"):
            command += ";"
        buff += command
        if len(buff) > COMMAND_MAXLEN:
            if result:
                #exeeds max length
                yield result
                buff = command
            else:
                #one comand itself exeeds max len
                yield buff
                buff = ""
        result = buff
    yield result
