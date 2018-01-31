from igorconsole import utils

import numpy as np

def prod_test():
    assert utils.prod([1, 2, 3, 4, 5]) == 120
    assert utils.prod(np.arange(1, 6)) == 120

def obvious_dtype_test():
    pass

def to_list_test():
    assert utils.to_list(None) == [None]
    assert utils.to_list(1.2) == [1.2]
    assert utils.to_list([1.2]) == [1.2]
    assert utils.to_list([]) == []
    assert utils.to_list("") == [""]
    assert utils.to_list(np.arange(3)) == [0, 1, 2]

def isbool_test():
    assert utils.isbool(True)
    assert utils.isbool(False)
    assert utils.isbool(np.bool_(True))
    assert utils.isbool(np.bool_(False))
    assert not utils.isbool(1)
    assert not utils.isbool(1.2)
    assert not utils.isbool(1+4J)
    assert not utils.isbool(type(True))
    assert not utils.isbool("Bool")
    assert not utils.isbool([])

def isint_test():
    assert utils.isint(True)
    assert utils.isint(False)
    assert utils.isint(np.bool_(True))
    assert utils.isint(np.bool_(False))
    assert utils.isint(1)
    assert utils.isint(np.int32(1))
    assert not utils.isint(1.2)
    assert not utils.isint(1+4J)
    assert not utils.isint(type(1))
    assert not utils.isint("1")
    assert not utils.isint([])

def isreal_test():
    assert utils.isreal(True)
    assert utils.isreal(False)
    assert utils.isreal(np.bool_(True))
    assert utils.isreal(np.bool_(False))
    assert utils.isreal(1)
    assert utils.isreal(np.int32(1))
    assert utils.isreal(1.2)
    assert not utils.isreal(1+4J)
    assert not utils.isreal(type(1))
    assert not utils.isreal("1")
    assert not utils.isreal([])

def isfloat_test():
    assert not utils.isfloat(True)
    assert not utils.isfloat(False)
    assert not utils.isfloat(np.bool_(True))
    assert not utils.isfloat(np.bool_(False))
    assert not utils.isfloat(1)
    assert not utils.isfloat(np.int32(1))
    assert utils.isfloat(1.2)
    assert not utils.isfloat(1+4J)
    assert not utils.isfloat(type(1))
    assert not utils.isfloat("1")
    assert not utils.isfloat([])

def iscomplex_test():
    assert not utils.iscomplex(True)
    assert not utils.iscomplex(False)
    assert not utils.iscomplex(np.bool_(True))
    assert not utils.iscomplex(np.bool_(False))
    assert not utils.iscomplex(1)
    assert not utils.iscomplex(np.int32(1))
    assert not utils.iscomplex(1.2)
    assert utils.iscomplex(1+4J)
    assert not utils.iscomplex(type(1))
    assert not utils.iscomplex("1")
    assert not utils.iscomplex([])

def isstr_test():
    assert not utils.isstr(True)
    assert not utils.isstr(False)
    assert not utils.isstr(np.bool_(True))
    assert not utils.isstr(np.bool_(False))
    assert not utils.isstr(1)
    assert not utils.isstr(np.int32(1))
    assert not utils.isstr(1.2)
    assert not utils.isstr(1+4J)
    assert not utils.isstr(type(1))
    assert utils.isstr("1")
    assert utils.isstr("")
    assert not utils.isstr([])

if __name__ == "__main__":
    prod_test()
    obvious_dtype_test()
    to_list_test()
    isbool_test()
    isint_test()
    isreal_test()
    isfloat_test()
    iscomplex_test()
    isstr_test()
    print("Passed!")
