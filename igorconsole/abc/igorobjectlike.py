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

class ConvertableToNdArray(ABC):
    @abstractmethod
    def toarray(self):
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

class NdArrayMethodMixin:
    @property
    def _return_type(self):
        return ArrayOperatableLikeWave

    @abstractmethod
    def fill(self, value):
        pass

    @abstractmethod
    def itemset(self, *args):
        pass

    @abstractmethod
    def partition(self, *args, **kwargs):
        pass

    @abstractmethod
    def put(self, *args, **kwargs):
        pass

    @abstractmethod
    def resize(self, *args, **kwargs):
        pass

    @abstractmethod
    def setfield(self, *args, **kwargs):
        pass

    @abstractmethod
    def sort(self, *args, **kwargs):
        pass

    #ndarray attributed
    @property
    def T(self):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        ndim = array.ndim

        array = array.T
        if ndim <= 1:
            pass
        elif ndim == 2:
            scalings = (scalings[0], scalings[2], scalings[1], scalings[3], scalings[4])
            units = (units[0], units[2], units[1], units[3], units[4])
        elif ndim == 3:
            scalings = (scalings[0], scalings[3], scalings[2], scalings[1], scalings[4])
            units = (units[0], units[3], units[2], units[1], units[4])
        elif ndim == 4:
            scalings = (scalings[0], scalings[4], scalings[3], scalings[2], scalings[1])
            units = (units[0], units[4], units[3], units[2], units[1])
        else:
            raise ValueError("ndim or igorwave must be 4 or less.")
        return self._return_type(array, scalings, units)

    @property
    def dtype(self):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.dtype

    @property
    def flat(self):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        
        array = array.flat
        scalings = (scalings[0], (0.0, 1.0), (0.0, 1.0), (0.0, 1.0), (0.0, 1.0))
        units = (units[0], "", "", "", "")
        return self._return_type(array, scalings, units)

    @property
    def imag(self):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        return self._return_type(array.imag, scalings, units)

    @property
    def real(self):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        return self._return_type(array.real, scalings, units)
    
    @property
    def size(self):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.size

    @property
    def imtemsize(self):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.itemsize

    @property
    def nbytes(self):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.nbytes

    @property
    def ndim(self):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.ndim

    @property
    def shape(self):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.shape

    @property
    def strides(self):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.strides

    #ndarray methods
    def all(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.all(*args, **kwargs)

    def any(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.any(*args, **kwargs)

    def argmax(self, axis=None):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.argmax(axis=axis)

    def argmin(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.argmin(*args, **kwargs)

    def argpartition(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.argpartition(*args, **kwargs)

    def argsort(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.argsort(*args, **kwargs)

    def astype(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        return self._return_type(array.astype(*args, **kwargs), scalings, units)

    def byteswap(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        array = array.byteswap(*args, **kwargs)
        scalings = ((0.0, 0.0), scalings[1], scalings[2], scalings[3], scalings[4])
        units = ("", units[1], units[2], units[3], units[4])
        return self._return_type(array, scalings, units)

    def choose(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        array = array.choose(*args, **kwargs)
        scalings = (scalings[0], (0.0, 1.0), (0.0, 1.0), (0.0, 1.0), (0.0, 1.0))
        units = (units[0], "", "", "", "")
        return self._return_type(array, scalings, units)

    def clip(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        array = array.clip(*args, **kwargs)
        return self._return_type(array, scalings, units)

    def compress(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        array = array.compress(*args, **kwargs)
        scalings = (scalings[0], (0.0, 1.0), (0.0, 1.0), (0.0, 1.0), (0.0, 1.0))
        units = (units[0], "", "", "", "")
        return self._return_type(array, scalings, units)

    def conjugate(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        array = array.conjugate(*args, **kwargs)
        return self._return_type(array, scalings, units)

    conj = conjugate

    def copy(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        array = array.copy(*args, **kwargs)
        return self._return_type(array, scalings, units)

    def cumprod(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        array = array.cumprod(*args, **kwargs)
        return self._return_type(array, scalings, units)

    def cumsum(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        array = array.cumsum(*args, **kwargs)
        return self._return_type(array, scalings, units)

    def diagonal(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        array = array.cumsum(*args, **kwargs)
        return array.diagonal(*args, **kwargs)

    def dot(self, b):
        return self.__matmul__(b)

    def flatten(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        array = array.flatten(*args, **kwargs)
        scalings = (scalings[0], (0.0, 1.0), (0.0, 1.0), (0.0, 1.0), (0.0, 1.0))
        units = (units[0], "", "", "", "")
        return self._return_type(array, scalings, units)

    def item(self, *args):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.item(*args)

    def max(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.max(*args, **kwargs)

    def mean(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.mean(*args, **kwargs)

    def min(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.min(*args, **kwargs)

    def newbyteorder(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        array = array.newbyteorder(*args, **kwargs)
        scalings = ((0.0, 0.0), scalings[1], scalings[2], scalings[3], scalings[4])
        units = ("", units[1], units[2], units[3], units[4])
        return self._return_type(array, scalings, units)

    def nonzero(self):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.nonzero()

    def prod(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.prod(*args, **kwargs)

    def ptp(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.ptp(*args, **kwargs)

    def ravel(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        array = array.ravel(*args, **kwargs)
        scalings = (scalings[0], (0.0, 1.0), (0.0, 1.0), (0.0, 1.0), (0.0, 1.0))
        units = (units[0], "", "", "", "")
        return self._return_type(array, scalings, units)

    def repeat(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        array = array.repeat(*args, **kwargs)
        scalings = (scalings[0], (0.0, 1.0), (0.0, 1.0), (0.0, 1.0), (0.0, 1.0))
        units = (units[0], "", "", "", "")
        return self._return_type(array, scalings, units)

    def reshape(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        array = array.reshape(*args, **kwargs)
        return self._return_type(array, scalings, units)

    def round(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        array = array.round(*args, **kwargs)
        return self._return_type(array, scalings, units)

    def searchsorted(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.searchsorted(*args, **kwargs)

    def squeeze(self, axis=None):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        shape = array.shape
        array = array.squeeze(axis=axis)
        if axis is None:
            axis = tuple(i for i, v in enumerate(shape) if v == 1)
        elif not hasattr(axis, "__len__"):
            axis = (axis,)
        units = (units[0],) + tuple(u for i, u in enumerate(units[1:]) if i not in axis)
        units += ("",) * (4 - len(units))
        scalings = (scalings[0],) + tuple(s for i, s in enumerate(scalings[1:]) if i not in axis)
        scalings += ((0.0, 1.0),) * (4 - len(scalings))
        return self._return_type(array, scalings, units)

    def std(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.std(*args, **kwargs)

    def sum(self, *args, **kwargs):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        return array.sum(*args, **kwargs)

    def swapaxes(self, axis1, axis2):
        info = self._igorconsole_to_igorwave()
        array = info["array"]
        scalings = info["scalings"]
        units = info["units"]
        array = array.swapaxes(axis1, axis2)
        return_scalings = scalings[0],
        return_units = units[0],
        for i in range(4):
            if i == axis1:
                return_scalings += scalings[axis2+1]
                return_units += units[axis2+1]
            elif i == axis2:
                return_scalings += scalings[axis1+1]
                return_units += units[axis1+1]
            else:
                return_scalings += scalings[i+1]
                return_units += units[i+1]
        return self._return_type(array, return_scalings, return_units)

    def take(self, *args, **kwargs):
        return self.array.take(*args, **kwargs)

    def tolist(self):
        return self.array.tolist()

    def tostring(self, *args, **kwargs):
        return self.array.tostring(*args, **kwargs)

    def trace(self, *args, **kwargs):
        return self.array.trace(*args, **kwargs)

    def transpose(self, *args, **kwargs):
        return self.T

    def var(self, *args, **kwargs):
        return self.array.var(*args, **kwargs)

class ArrayOperatableLikeWave(OperatableLikeIgorWave,
    NdArrayMethodMixin, ConvertableToNdArray):
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

    #inplace
    def fill(self, value):
        self.array.fill(value)

    #inplace
    def itemset(self, *args):
        self.array.itemset(*args)

    #inplace
    def partition(self, *args, **kwargs):
        self.array.partition(*args, **kwargs)

    #inplace
    def put(self, *args, **kwargs):
        self.array.put(*args, **kwargs)

    #inplace
    def resize(self, *args, **kwargs):
        self.array.resize(*args, **kwargs)

    #inplace
    def setfield(self, *args, **kwargs):
        self.array.setfield(*args, **kwargs)

    #inplace
    def sort(self, *args, **kwargs):
        self.array.sort(*args, **kwargs)
    
    def toarray(self):
        return np.array(self.array)