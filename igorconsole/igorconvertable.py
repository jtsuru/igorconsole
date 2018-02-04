import abc
import operator as op
import numpy as np


class ConvertableToIgorWaveBase(abc.ABC):
    @abc.abstractmethod
    def _to_igorwave(self):
        pass

def wave_operator(self, other, operator):
    from .oleconsole import Wave
    array, scalings, units = self._to_igorwave()
    if isinstance(other, Wave):
        array = operator(array, other.array)
    elif hasattr(other, "_to_igorwave"):
        other_array, _, _ = other._to_igorwave()
        array = operator(array, other_array)
    else:
        array = operator(array, other)
    return IgorWaveConvertableNdArray(array, scalings, units)

def wave_roperator(self, other, operator):
    array, scalings, units = self._to_igorwave()
    if hasattr(other, "_to_igorwave"):
        #use left side scalings and units
        other_array, scalings, units = other._to_igrwave()
        array = operator(other_array, array)
    else:
        array = operator(other, array)
    return IgorWaveConvertableNdArray(array, scalings, units)

class IgorWaveConvertableNdArray(np.ndarray, ConvertableToIgorWaveBase):
    def __new__(cls, array, scalings=None, units=None):
        if scalings is None or units is None:
            array, scalings, units = array._to_igorwave()
        result = np.asarray(array).view(cls)
        result.scalings = scalings
        result.units = units
        return result
    
    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.scalings = getattr(obj, "scalings", None)
        self.units = getattr(obj, "units", None)
    
    def _to_igorwave(self):
        return np.asarray(self), self.scalings, self.units

    _operator = wave_operator

    _roperator = wave_roperator

    def __gt__(self, other):
        return self._operator(other, op.gt)

    def __ge__(self, other):
        return self._operator(other, op.ge)

    def __add__(self, other):
        return self._operator(other, op.add)

    def __radd__(self, other):
        return self._roperator(other, op.add)

    def __mul__(self, other):
        return self._operator(other, op.mul)

    def __rmul__(self, other):
        return self._roperator(other, op.mul)

    def __sub__(self, other):
        return self._operator(other, op.sub)
    
    def __rsub__(self, other):
        return self._roperator(other, op.sub)

    def __truediv__(self, other):
        return self._operator(other, op.truediv)

    def __rtruediv__(self, other):
        return self._roperator(other, op.truediv)
    
    def __floordiv__(self, other):
        return self._operator(other, op.floordiv)
    
    def __rfloordiv__(self, other):
        return self._roperator(other, op.floordiv)

    def __matmul__(self, other):
        return self._operator(other, op.matmul)

    def __rmatmul__(self, other):
        return self._roperator(other, op.matmul)

    def __mod__(self, other):
        return self._operator(other, op.mod)

    def __rmod__(self, other):
        return self._roperator(other, op.mod)