from abc import ABC, abstractclassmethod, abstractstaticmethod, abstractmethod, abstractproperty
import collections.abc as c_abc

from igorconsole.abc.igorobjectlike import OperatableLikeIgorWave, OperatableLikeIgorVariable

class IgorObjectBase(ABC):
    @abstractproperty
    def path(self):
        pass

    @abstractproperty
    def quoted_path(self):
        pass

    @abstractproperty
    def name(self):
        pass

    @abstractproperty
    def parent(self):
        pass

    @abstractmethod
    def delete(self):
        pass


class IgorFolderBase(IgorObjectBase):
    @abstractmethod
    def __getattr__(self, key):
        pass

    @abstractmethod
    def __setattr__(self, item, val):
        pass

    @abstractmethod
    def __getitem__(self, key):
        pass

    @abstractmethod
    def __setitem__(self, key, val):
        pass

    @abstractmethod
    def __contains__(self, name):
        pass

    @abstractproperty
    def subfolders(self):
        pass

    @abstractproperty
    def waves(self):
        pass

    @abstractproperty
    def variables(self):
        pass

    @abstractproperty
    def f(self):
        pass

    @abstractproperty
    def w(self):
        pass

    @abstractproperty
    def v(self):
        pass

    @abstractmethod
    def chdir(self):
        pass

    @abstractproperty
    def delete_folder(self, target):
        pass
    
    @abstractmethod
    def walk(self, limit_depth=float("inf"), shallower_limit=0, method="dfs"):
        pass

    @abstractmethod
    def _igorconsole_to_igorfolder(self):
        pass


class IgorVariableBase(IgorObjectBase, OperatableLikeIgorVariable):
    @abstractproperty
    def dtype(self):
        pass

    @abstractproperty
    def value(self):
        pass


class IgorWaveBase(IgorObjectBase, OperatableLikeIgorWave):
    @abstractproperty
    def dtype(self):
        pass

    @abstractproperty
    def array(self):
        pass

    @abstractmethod
    def append(self, obj, keepscalings=True, keepunits=True):
        pass

    @abstractproperty
    def ndim(self):
        pass

    @abstractproperty
    def shape(self):
        pass

    @abstractproperty
    def size(self):
        pass

    @abstractproperty
    def is_(self, other):
        pass

    @abstractproperty
    def is_equiv(self, other):
        pass


class IgorObjectCollectionBase(ABC, c_abc.MutableMapping):
    @abstractmethod
    def add(self, name, overwrite=False):
        pass

    @abstractstaticmethod
    def addable(self, obj):
        pass


class FolderCollection(IgorObjectCollectionBase):
    pass


class WaveCollection(IgorObjectCollectionBase):
    pass

class VariableCollection(IgorObjectCollectionBase):
    pass