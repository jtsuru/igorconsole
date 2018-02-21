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
        if hasattr(args[0], "_igorconsole_to_igorwave"):
            info = args[0]._igorconsole_to_igorwave()
            self.array = info["array"]
            self.scalings = info["scalings"]
            self.units = info["units"]
        elif isinstance(args[0], dict):
            info = args[0]
            self.array = info["array"]
            self.scalings = info["scalings"]
            self.units = info["units"]
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

    #ndarray attributed
    @property
    def T(self):
        return type(self)(self.array.T, self.scalings, self.units)

    @property
    def data(self):
        return self.array.data

    @property
    def dtype(self):
        return self.array.dtype

    @property
    def flags(self):
        return self.array.flags

    @property
    def flat(self):
        return self.array.flat

    @property
    def imag(self):
        return self.array.imag

    @property
    def real(self):
        return self.array.real
    
    @property
    def size(self):
        return self.array.size

    @property
    def imtemsize(self):
        return self.array.imtemsize

    @property
    def nbytes(self):
        return self.array.nbytes

    @property
    def ndim(self):
        return self.array.ndim

    @property
    def shape(self):
        return self.array.shape

    @property
    def strides(self):
        return self.array.strides

    @property
    def ctypes(self):
        return self.array.ctypes

    @property
    def base(self):
        return self.array.base

    #ndarray methods
    def all(self, *args, **kwargs):
        return self.array.all(*args, **kwargs)

    def any(self, *args, **kwargs):
        return self.array.any(*args, **kwargs)

    def argmax(self, *args, **kwargs):
        return self.array.argmax(*args, **kwargs)

    def argmin(self, *args, **kwargs):
        return self.array.argmin(*args, **kwargs)

    def argpartition(self, *args, **kwargs):
        return self.array.argpartition(*args, **kwargs)

    def argsort(self, *args, **kwargs):
        return self.array.argsort(*args, **kwargs)

    def astype(self, *args, **kwargs):
        return type(self)(self.array.astype(*args, **kwargs), self.scalings, self.units)

    def byteswap(self, *args, **kwargs):
        self.array.byteswap(*args, **kwargs)

    def choose(self, *args, **kwargs):
        raise NotImplementedError()

    def clip(self, *args, **kwargs):
        return type(self)(self.array.clip(*args, **kwargs), self.scalings, self.units)

    def compress(self, *args, **kwargs):
        return type(self)(self.array.compress(*args, **kwargs), self.scalings, self.units)

    def conj(self, *args, **kwargs):
        return type(self)(self.array.conj(*args, **kwargs), self.scalings, self.units)

    def conjugate(self, *args, **kwargs):
        return type(self)(self.array.conjugate(*args, **kwargs), self.scalings, self.units)

    def copy(self, *args, **kwargs):
        return type(self)(self.array.copy(*args, **kwargs), self.scalings, self.units)

    def cumprod(self, *args, **kwargs):
        return self.array.cumprod(*args, **kwargs)

    def cumsum(self, *args, **kwargs):
        return self.array.cumsum(*args, **kwargs)

    def diagonal(self, *args, **kwargs):
        return self.array.diagonal(*args, **kwargs)

    def dot(self, b):
        return self.__matmul__(b)

    def fill(self, value):
        self.array.fill(value)

    def flatten(self, *args, **kwargs):
        return type(self)(self.array.flatten(*args, **kwargs), self.scalings, self.units)

    def item(self, *args):
        return self.array.item(*args)

    def itemset(self, *args):
        self.array.itemset(*args)

    def max(self, *args, **kwargs):
        return self.array.max(*args, **kwargs)

    def mean(self, *args, **kwargs):
        return self.array.mean(*args, **kwargs)

    def min(self, *args, **kwargs):
        return self.array.min(*args, **kwargs)

    def newbyteorder(self, *args, **kwargs):
        return type(self)(self.array.newbyteorder(*args, **kwargs), self.scalings, self.units)

    def nonzero(self):
        return self.array.nonzero()

    def partition(self, *args, **kwargs):
        self.array.partition(*args, **kwargs)

    def prod(self, *args, **kwargs):
        return self.array.prod(*args, **kwargs)

    def ptp(self, *args, **kwargs):
        return self.array.ptp(*args, **kwargs)

    def put(self, *args, **kwargs):
        self.array.put(*args, **kwargs)

    def ravel(self, *args, **kwargs):
        return self.array.ravel(*args, **kwargs)

    def repeat(self, *args, **kwargs):
        return self.array.repeat(*args, **kwargs)

    def reshape(self, *args, **kwargs):
        return self.array.reshape(*args, **kwargs)

    def resize(self, *args, **kwargs):
        self.array.resize(*args, **kwargs)

    def round(self, *args, **kwargs):
        return type(self)(self.array.round(*args, **kwargs), self.scalings, self.units)

    def searchsorted(self, *args, **kwargs):
        return self.array.searchsorted(*args, **kwargs)

    def setfield(self, *args, **kwargs):
        self.array.setfield(*args, **kwargs)

    def setflags(self, *args, **kwargs):
        self.array.setflags(*args, **kwargs)

    def sort(self, *args, **kwargs):
        self.array.sort(*args, **kwargs)

    def squeeze(self, *args, **kwargs):
        return self.array.squeeze(*args, **kwargs)

    def std(self, *args, **kwargs):
        return self.array.std(*args, **kwargs)

    def sum(self, *args, **kwargs):
        return self.array.sum(*args, **kwargs)

    def swapaxes(self, *args, **kwargs):
        #unit, scaling
        return self.array.swapaxes(*args, **kwargs)

    def take(self, *args, **kwargs):
        return self.array.take(*args, **kwargs)

    def tobytes(self, *args, **kwargs):
        return self.array.tobytes(*args, **kwargs)

    def tolist(self):
        return self.array.tolist()

    def tostring(self, *args, **kwargs):
        return self.array.tostring(*args, **kwargs)

    def trace(self, *args, **kwargs):
        return self.array.trace(*args, **kwargs)

    def transpose(self, *args, **kwargs):
        return self.array.transpose(*args, **kwargs)

    def var(self, *args, **kwargs):
        return self.array.var(*args, **kwargs)

    def view(self, *args, **kwargs):
        return type(self)(self.array.view(*args, **kwargs), self.scalings, self.units)
