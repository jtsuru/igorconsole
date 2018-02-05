import abc
import operator as op
import numpy as np


class ConvertableToIgorWaveBase(abc.ABC):
    @abc.abstractmethod
    def _igorconsole_to_igorwave(self):
        pass

def wave_unary_operator(self, operator):
    info = self._igorconsole_to_igorwave()
    array, scalings, units = info["array"], info["scalings"], info["units"]
    return ArrayOperatableLikeWave(operator(array), scalings, units)

def wave_binary_operator(self, other, operator):
    from .oleconsole import Wave
    info = self._igorconsole_to_igorwave()
    array, scalings, units = info["array"], info["scalings"], info["units"]
    if isinstance(other, Wave):
        array = operator(array, other.array)
    elif hasattr(other, "_igorconsole_to_igorwave"):
        otherinfo = other._igorconsole_to_igorwave()
        array = operator(array, otherinfo["array"])
    else:
        array = operator(array, other)
    return ArrayOperatableLikeWave(array, scalings, units)

def wave_binary_roperator(self, other, operator):
    info = self._igorconsole_to_igorwave()
    array, scalings, units = info["array"], info["scalings"], info["units"]
    if hasattr(other, "_igorconsole_to_igorwave"):
        #use left side scalings and units
        otherinfo = other._igorconsole_to_igrwave()
        array = operator(otherinfo["array"], array)
        scalings = otherinfo["scalings"]
        units = otherinfo["units"]
    else:
        array = operator(other, array)
    return ArrayOperatableLikeWave(array, scalings, units)

class OperatableLikeIgorWave(ConvertableToIgorWaveBase):
    def __len__(self):
        info = self._igorconsole_to_igorwave()
        return len(info["array"])

    def __getitem__(self, key):
        info = self._igorconsole_to_igorwave()
        return info["array"][key]

    #unary operations
    def __neg__(self):
        return wave_unary_operator(self, op.neg)

    def __pos__(self):
        return wave_unary_operator(self, op.pos)

    def __abs__(self):
        return wave_unary_operator(self, op.abs)

    def __invert__(self):
        return wave_unary_operator(self, op.invert)

    def __lt__(self, other):
        return wave_binary_operator(self, other, op.lt).array

    def __le__(self, other):
        return wave_binary_operator(self, other, op.le).array

    def __eq__(self, other):
        return wave_binary_operator(self, other, op.eq).array

    def __gt__(self, other):
        return wave_binary_operator(self, other, op.gt).array

    def __ge__(self, other):
        return wave_binary_operator(self, other, op.ge).array

    def __add__(self, other):
        return wave_binary_operator(self, other, op.add)

    def __radd__(self, other):
        return wave_binary_roperator(self, other, op.add)

    def __mul__(self, other):
        return wave_binary_operator(self, other, op.mul)

    def __rmul__(self, other):
        return wave_binary_roperator(self, other, op.mul)

    def __sub__(self, other):
        return wave_binary_operator(self, other, op.sub)
    
    def __rsub__(self, other):
        return wave_binary_roperator(self, other, op.sub)

    def __truediv__(self, other):
        return wave_binary_operator(self, other, op.truediv)

    def __rtruediv__(self, other):
        return wave_binary_roperator(self, other, op.truediv)
    
    def __floordiv__(self, other):
        return wave_binary_operator(self, other, op.floordiv)
    
    def __rfloordiv__(self, other):
        return wave_binary_roperator(self, other, op.floordiv)

    def __matmul__(self, other):
        return wave_binary_operator(self, other, op.matmul)

    def __rmatmul__(self, other):
        return wave_binary_roperator(self, other, op.matmul)

    def __mod__(self, other):
        return wave_binary_operator(self, other, op.mod)

    def __rmod__(self, other):
        return wave_binary_roperator(self, other, op.mod)

class ArrayOperatableLikeWave(OperatableLikeIgorWave):
    def __init__(self, *args):
        if isinstance(args, dict):
            raise NotImplementedError()
        else:
            self.array = np.asarray(args[0])
            self.scalings = args[1]
            self.units = args[2]
    
    def __repr__(self):
        return repr(self.array)

    def _igorconsole_to_igorwave(self):
        info = {
            "type": "IgorWave",
            "array": self.array,
            "scalings": self.scalings,
            "units": self.units
        }
        return info
