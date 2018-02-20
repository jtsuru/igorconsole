from abc import ABC, abstractclassmethod, abstractstaticmethod, abstractmethod, abstractproperty 

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


class IgorVariableBase(IgorObjectBase):
    @abstractproperty
    def dtype(self):
        pass

    @abstractproperty
    def value(self):
        pass

    @abstractmethod
    def _igorconsole_to_igorvariable(self):
        pass


class Wave(IgorObjectBase, OperatableLikeIgorWave):
    @abstractproperty
    def dtype(self):
        pass

    @abstractproperty
    def array(self):
        pass

    @abstractproperty
    def append(self, obj, keepscalings=True, keepunits=True):
        length = self._length
        if (length is not None) and length > APPEND_SWITCH:
            self._append2(obj)
        else:
            self._append1(obj, keepscalings, keepunits)
        f.make_wave(self.name, new_array)

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

    @abstractproperty
    def _igorconsole_to_igorwave(self):
        pass


class IgorObjectCollectionBase(ABC, c_abc.MutableMapping):
    @abstractmethod
    def copy(self):
        pass

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