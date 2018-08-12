from itertools import combinations

import igorconsole
import numpy as np

def test(igor, a, array):
    axis = range(array.ndim)
    assert np.all(a.T == array.T)
    if igor:
        igor.root.tmp = a.T
        igor.root.tmp = a.flat
        igor.root.tmp = a.imag
        igor.root.tmp = a.real
        igor.root.tmp = a.astype(np.float32)
        assert igor.root.tmp.dtype.type == np.float32
        igor.root.tmp = a.astype(np.int32)
        assert igor.root.tmp.dtype.type == np.int32
    assert a.dtype == array.dtype
    assert np.all(a.flat == array.flat)
    assert np.all(a.imag == array.imag)
    assert np.all(a.real == array.real)
    assert a.size == array.size
    assert a.itemsize == array.itemsize
    assert a.nbytes == array.nbytes
    assert a.ndim == array.ndim
    assert a.shape == array.shape
    assert a.strides == array.strides
    assert a.all() == array.all()
    assert a.all(keepdims=True) == array.all(keepdims=True)
    for ax in axis:
        assert np.all(a.all(axis=ax) == array.all(axis=ax))
        assert np.all(a.all(axis=ax, keepdims=True) == array.all(axis=ax, keepdims=True))
    assert a.any() == array.any()
    for ax in axis:
        assert np.all(a.any(axis=ax) == array.any(axis=ax))
        assert np.all(a.any(axis=ax, keepdims=True) == array.any(axis=ax, keepdims=True))
    assert a.argmax() == array.argmax()
    for ax in axis:
        assert np.all(a.argmax(axis=ax) == array.argmax(axis=ax))
    assert a.argmin() == array.argmin()
    for ax in axis:
        assert np.all(a.argmin(axis=ax) == array.argmin(axis=ax))
    #assert a.argpartiion(1)
    assert np.all(a.argsort() == array.argsort())
    assert a.astype(np.float32).dtype.type == np.float32
    assert a.astype(np.float64).dtype.type == np.float64
    assert a.astype(np.complex128).dtype.type == np.complex128
    assert np.all(a.byteswap() == array.byteswap())
    #assert np.all(np.array([1,2]).choose(a) == np.array([1,2]).choose(array))
    assert np.all(a.clip(10,100) == array.clip(10,100))
    assert np.all(a.conj() == array.conj())
    assert np.all(a.cumprod() == array.cumprod())
    assert np.all(a.cumsum() == array.cumsum())
    for ax in axis:
        assert np.all(a.cumsum(axis=ax) == array.cumsum(axis=ax))
    assert np.all(a.dot(a) == array.dot(array))
    assert np.all(a.dot(array) == array.dot(a))
    assert np.all(a.flatten() == array.flatten())
    assert np.all(a.max() == array.max())
    for ax in axis:
        assert np.all(a.max(axis=ax) == array.max(axis=ax))
    assert np.all(a.mean() == array.mean())
    for ax in axis:
        assert np.all(a.mean(axis=ax) == array.mean(axis=ax))
    assert np.all(a.min() == array.min())
    for ax in axis:
        assert np.all(a.min(axis=ax) == array.min(axis=ax))
    assert np.all(a.newbyteorder() == array.newbyteorder())
    for bo in ["S", "<", "L", ">", "B", "|", "I"]:
        assert np.all(a.newbyteorder(bo) == array.newbyteorder(bo))
    for item1, item2 in zip(a.nonzero(), array.nonzero()):
        assert np.all(item1 == item2)
    assert np.all(a.prod() == array.prod())
    for ax in axis:
        assert np.all(a.prod(axis=ax) == array.prod(axis=ax))
    assert np.all(a.ptp() == array.ptp())
    for ax in axis:
        assert np.all(a.ptp(axis=ax) == array.ptp(axis=ax))
    assert np.all(a.ravel() == array.ravel())
    assert np.all(a.repeat(3) == array.repeat(3))
    assert np.all(a.round() == array.round())
    assert np.all((a+0.01).round() == (array+0.01).round())
    #assert np.all(a.searchsorted(3) == array.searchsorted(3))
    #squeeze
    assert np.all(a.std() == array.std())
    for ax in axis:
        assert np.all(a.std(axis=ax) == array.std(axis=ax))
    assert np.all(a.sum() == array.sum())
    for ax in axis:
        assert np.all(a.sum(axis=ax) == array.sum(axis=ax))
    assert np.all(a.take([1,2,3]) == array.take([1,2,3]))
    assert a.tolist() == array.tolist()
    assert a.tostring() == array.tostring()
    assert np.all(a.transpose() == array.transpose())

def test2d(igor, w, a):
    assert np.all(w.compress([0,1], axis=0) == a.compress([0,1], axis=0))
    assert np.all(w.compress([0,1], axis=1) == a.compress([0,1], axis=1))
    assert np.all(w.diagonal() == a.diagonal())
    tmp = w.swapaxes(0,1)
    tmp2 = w+0
    assert np.all(tmp == a.swapaxes(0,1))
    assert tmp.scalings[0] == tmp2.scalings[0]
    assert tmp.scalings[1] == tmp2.scalings[2]
    assert tmp.scalings[2] == tmp2.scalings[1]
    assert tmp.scalings[3] == tmp2.scalings[3]
    assert tmp.scalings[4] == tmp2.scalings[4]
    assert tmp.units[0] == tmp2.units[0]
    assert tmp.units[1] == tmp2.units[2]
    assert tmp.units[2] == tmp2.units[1]
    assert tmp.units[3] == tmp2.units[3]
    assert tmp.units[4] == tmp2.units[4]
    assert np.all(w.trace() == a.trace())

def test3d(igor, w, a):
    assert np.all(w.compress([0,1,2], axis=0) == a.compress([0,1,2], axis=0))
    assert np.all(w.compress([0,1,2], axis=1) == a.compress([0,1,2], axis=1))
    assert np.all(w.compress([0,1,2], axis=2) == a.compress([0,1,2], axis=2))

    tmp = w.swapaxes(1,2)
    tmp2 = w+0
    assert np.all(tmp == a.swapaxes(1,2))
    assert tmp.scalings[0] == tmp2.scalings[0]
    assert tmp.scalings[1] == tmp2.scalings[1]
    assert tmp.scalings[2] == tmp2.scalings[3]
    assert tmp.scalings[3] == tmp2.scalings[2]
    assert tmp.scalings[4] == tmp2.scalings[4]
    assert tmp.units[0] == tmp2.units[0]
    assert tmp.units[1] == tmp2.units[1]
    assert tmp.units[2] == tmp2.units[3]
    assert tmp.units[3] == tmp2.units[2]
    assert tmp.units[4] == tmp2.units[4]
def test4d(igor, w, a):
    assert np.all(w.compress([0,1,2,3], axis=0) == a.compress([0,1,2,3], axis=0))
    assert np.all(w.compress([0,1,2,3], axis=1) == a.compress([0,1,2,3], axis=1))
    assert np.all(w.compress([0,1,2,3], axis=2) == a.compress([0,1,2,3], axis=2))
    assert np.all(w.compress([0,1,2,3], axis=3) == a.compress([0,1,2,3], axis=3))

def main():
    igor = igorconsole.start()
    a = np.arange(30, dtype=float) + 1
    igor.root.a = a
    assert np.all(igor.root.a.reshape(5,6) == a.reshape(5,6))
    test(igor, igor.root.a, a)
    test(igor, igor.root.a+1, a+1)
    b = np.arange(100).reshape(10,10) + 1
    igor.root.b = b
    assert np.all(igor.root.b.reshape(10,10) == b.reshape(10,10))
    test(igor, igor.root.b, b)
    test(igor, igor.root.b+1, b+1)
    test2d(igor, igor.root.b, b)
    test2d(igor, igor.root.b+1, b+1)
    c = np.arange(3**3).reshape(3,3,3) + 3J
    igor.root.c = c
    assert np.all(igor.root.c.reshape(3,9) == c.reshape(3,9))
    test(igor, igor.root.c, c)
    test2d(igor, igor.root.c, c)
    test3d(igor, igor.root.c, c)
    test(igor, igor.root.c+1, c+1)
    test2d(igor, igor.root.c+1, c+1)
    test3d(igor, igor.root.c+1, c+1)
    d = np.arange(4**4, dtype=np.float32).reshape([4]*4) + 1
    igor.root.d = d
    assert np.all(igor.root.d.reshape(8,32) == d.reshape(8,32))
    test(igor, igor.root.d, d)
    test2d(igor, igor.root.d, d)
    test3d(igor, igor.root.d, d)
    test4d(igor, igor.root.d, d)
    test(igor, igor.root.d+1, d+1)
    test2d(igor, igor.root.d+1, d+1)
    test3d(igor, igor.root.d+1, d+1)
    test4d(igor, igor.root.d+1, d+1)

if __name__ == "__main__":
    main()
    print("OK")