import operator as op

import numpy as np
from abc import ABC, abstractclassmethod, abstractstaticmethod, abstractmethod, abstractproperty 

class ConvertableToIgorVariableMixin(ABC):
    @abstractmethod
    def _igorconsole_to_igorvariable(self):
        pass


class ConvertableToIgorWaveMixin(ABC):
    @abstractmethod
    def _igorconsole_to_igorwave(self):
        pass


class ConvertableToIgorFolderMixin(ABC):
    @abstractmethod
    def _igorconsole_to_igorfolder(self):
        pass


class OperatableLikeIgorObject:
    @abstractmethod
    def _unary_operation(self, operator):
        pass

    @abstractmethod
    def _binary_operation(self, other, operator):
        pass

    @abstractmethod
    def _binary_roperation(self, other ,operator):
        pass

    #unary operations
    def __neg__(self):
        return self._unary_operation(op.neg)

    def __pos__(self):
        return self._unary_operation(op.pos)

    def __abs__(self):
        return self._unary_operation(op.abs)

    def __invert__(self):
        return self._unary_operation(op.invert)

    def __lt__(self, other):
        return self._binary_operation(other, op.lt)

    def __le__(self, other):
        return self._binary_operation(other, op.le)

    def __eq__(self, other):
        return self._binary_operation(other, op.eq)

    def __gt__(self, other):
        return self._binary_operation(other, op.gt)

    def __ge__(self, other):
        return self._binary_operation(other, op.ge)

    def __add__(self, other):
        return self._binary_operation(other, op.add)

    def __radd__(self, other):
        return self._binary_roperation(other, op.add)

    def __mul__(self, other):
        return self._binary_operation(other, op.mul)

    def __rmul__(self, other):
        return self._binary_roperation(other, op.mul)

    def __sub__(self, other):
        return self._binary_operation(other, op.sub)
    
    def __rsub__(self, other):
        return self._binary_roperation(other, op.sub)

    def __truediv__(self, other):
        return self._binary_operation(other, op.truediv)

    def __rtruediv__(self, other):
        return self._binary_roperation(other, op.truediv)
    
    def __floordiv__(self, other):
        return self._binary_operation(other, op.floordiv)
    
    def __rfloordiv__(self, other):
        return self._binary_roperation(other, op.floordiv)

    def __matmul__(self, other):
        return self._binary_operation(other, op.matmul)

    def __rmatmul__(self, other):
        return self._binary_roperation(other, op.matmul)

    def __mod__(self, other):
        return self._binary_operation(other, op.mod)

    def __rmod__(self, other):
        return self._binary_roperation(other, op.mod)

class OperatableLikeIgorWave(OperatableLikeIgorObject, ConvertableToIgorWaveMixin):
    def _unary_operation(self, operator):
        info = self._igorconsole_to_igorwave()
        array, scalings, units = info["array"], info["scalings"], info["units"]
        return ArrayOperatableLikeWave(operator(array), scalings, units)

    def _binary_operation(self, other, operator):
        info = self._igorconsole_to_igorwave()
        array, scalings, units = info["array"], info["scalings"], info["units"]
        if hasattr(other, "_igorconsole_to_igorwave"):
            otherinfo = other._igorconsole_to_igorwave()
            array = operator(array, otherinfo["array"])
        else:
            array = operator(array, other)
        return ArrayOperatableLikeWave(array, scalings, units)

    def _binary_roperation(self, other, operator):
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

    def __len__(self):
        info = self._igorconsole_to_igorwave()
        return len(info["array"])

    def __getitem__(self, key):
        info = self._igorconsole_to_igorwave()
        return info["array"][key]

    def __lt__(self, other):
        return super().__lt__(other).array

    def __le__(self, other):
        return super().__le__(other).array

    def __eq__(self, other):
        return super().__eq__(other).array

    def __gt__(self, other):
        return super().__gt__(other).array

    def __ge__(self, other):
        return super().__ge__(other).array

    def __matmul__(self, other):
        return self._binary_operation(other, op.matmul)

    def __rmatmul__(self, other):
        return self._binary_roperation(other, op.matmul)

    def __mod__(self, other):
        return self._binary_operation(other, op.mod)

    def __rmod__(self, other):
        return self._binary_roperation(other, op.mod)

class OperatableLikeIgorVariable(OperatableLikeIgorObject, ConvertableToIgorVariableMixin):
    def _unary_operation(self, operator):
        return operator(self._igorconsole_to_igorvariable()["value"])

    def _binary_operation(self, other, operator):
        value = self._igorconsole_to_igorvariable()["value"]
        if hasattr(other, "_igorconsole_to_igorvariable"):
            othervalue = other._igorconsole_to_igorvariable()["value"]
            return operator(value, othervalue)
        else:
            return operator(value, other)

    def _binary_roperation(self, other, operator):
        value = self._igorconsole_to_igorvariable()["value"]
        return operator(other, value)

    def __complex__(self):
        return complex(self._igorconsole_to_igorvariable()["value"])

    def __float__(self):
        return float(self._igorconsole_to_igorvariable()["value"])
    
    def __str__(self):
        return str(self._igorconsole_to_igorvariable()["value"])


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
