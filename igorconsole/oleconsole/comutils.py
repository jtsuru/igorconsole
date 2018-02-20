import numpy as np
from win32com.client import VARIANT
import pythoncom as com

from .utils import array_dtype

variant_num = {
    np.int8: com.VT_I1,
    np.int16: com.VT_I2,
    np.int32: com.VT_I4,
    np.int64: com.VT_I8,
    np.uint8: com.VT_I1,
    np.uint16: com.VT_UI2,
    np.uint32: com.VT_UI4,
    np.uint64: com.VT_UI8,
    np.float32: com.VT_R4,
    np.float64: com.VT_R8,
    np.bool_: com.VT_BOOL
}
variant_num[float] = com.VT_R8
variant_num[int] = com.VT_I8

def list_to_variant_array(list_, vttype=com.VT_R8):
    vttype = com.VT_ARRAY | vttype
    return VARIANT(vttype, list_)

def nptype_vttype_and_variant_array(array, dtype=None):
    array = np.asarray(array, dtype=dtype)
    nptype = array_dtype(array)
    vttype = variant_num[nptype]
    return nptype, vttype, list_to_variant_array(array.tolist(), vttype)

def to_variant_array(array, dtype=None):
    return nptype_vttype_and_variant_array(array, dtype)[2]
