import numpy as np
import pandas as pd

import igorconsole

def folder_setattr_test():
    igor = igorconsole.start(visible=True)
    #str
    igor.root.strval = "test"
    assert igor.root.strval == "test"
    assert igor.root.strval.value == "test"

    #float
    igor.root.floatval = 1.25
    assert igor.root.floatval == 1.25
    assert igor.root.floatval.value == 1.25

    #iterable
    igor.root.wave1 = np.arange(10)
    assert np.all(igor.root.wave1 == np.arange(10))

    #wave
    igor.root.wave2 = igor.root.wave1
    igor.root.wave2.is_equiv(igor.root.wave1)


    igor.quit_wo_save()

def folder_setitem_test():
    igor = igorconsole.start(visible=True)
    #str
    igor.root["strval"] = "test"
    assert igor.root["strval"] == "test"
    assert igor.root["strval"].value == "test"

    #float
    igor.root["floatval"] = 1.25
    assert igor.root["floatval"] == 1.25
    assert igor.root["floatval"].value == 1.25

    #iterable
    igor.root["wave1"] = np.arange(10)
    assert np.all(igor.root["wave1"] == np.arange(10))

    #wave
    igor.root["wave2"] = igor.root["wave1"]
    igor.root["wave2"].is_equiv(igor.root["wave1"])

    igor.quit_wo_save()

def wavecollection_setitem_test():
    igor = igorconsole.start(visible=True)
    def check(name, dim, dtype):
        name = "{0}_{1}d".format(name, dim)
        size = 10**dim
        array = np.arange(size, dtype=dtype).reshape(*[10]*dim)
        igor.root.w[name] = array
        assert np.all(igor.root.w[name] == array)
        assert np.all(igor.root[name] == array)
        igor.root.w[name+"2"] = igor.root.w[name]
        assert np.all(igor.root.w[name+"2"] == igor.root.w[name])
        assert np.all(igor.root[name+"2"] == igor.root.w[name])

    dim = [1,2,3,4]
    dtype = {
        "aint32": np.int32,
        "afloat64": np.float64,
        "afloat32": np.float32,
        "acomplex64": np.complex64,
        "acomplex128": np.complex128
        }
    for d in dim:
        for n, t in dtype.items():
            check(n, d, t)
    igor.quit_wo_save()

def variablecollection_setitem_test():
    igor = igorconsole.start(visible=True)
    igor.root.v["str"] = "test"
    assert igor.root.v["str"] == "test"
    assert igor.root["str"] == "test"
    igor.root.v["str2"] = igor.root.v["str"]
    assert igor.root.v["str"] == igor.root.v["str2"]

    igor.root.v["f1"] = 1.5
    assert igor.root.v["f1"] == 1.5
    assert igor.root.f1 == 1.5
    igor.root.v["f2"] = igor.root.f1
    assert igor.root.v["f1"] == igor.root.v["f2"]

    igor.root.v["c1"] = 1.5+1J
    assert igor.root.v["c1"] == 1.5+1J
    assert igor.root.c1 == 1.5+1J
    igor.root.v["c2"] = igor.root.c1
    assert igor.root.v["c1"] == igor.root.v["c2"]
    igor.quit_wo_save()

def foldercollection_setitem_test():
    igor = igorconsole.start(visible=True)
    data = {
        "wave1": np.arange(10),
        "wave2": np.arange(10) + 1J*np.arange(10),
        "wave3": np.arange(100).reshape(10,10),
        "wave4": np.arange(1000).reshape(10,10,10),
        "wave5": np.arange(10000).reshape(10,10,10,10),
        "numval": 10,
        "strval": "test"
    }
    data["subfolder1"] = {
        "wave1": np.arange(10),
        "wave2": np.arange(10) + 1J*np.arange(10),
        "wave3": np.arange(100).reshape(10,10),
        "wave4": np.arange(1000).reshape(10,10,10),
        "wave5": np.arange(10000).reshape(10,10,10,10),
        "numval": 10,
        "strval": "test"
    }
    igor.root.f["foldertest1"] = data
    igor.root["foldertest2"] = data
    igor.root.foldertest3 = data
    def check(folder):
        for i, v in data.items():
            if isinstance(v, np.ndarray):
                assert np.all(folder[i] == v)
            elif isinstance(v, dict):
                pass
            else:
                assert folder[i] == v
        if "subfolder1" in folder:
            check(folder.subfolder1)
    check(igor.root.foldertest1)
    check(igor.root.foldertest2)
    check(igor.root.foldertest3)

    array2d = np.random.rand(10, 3)
    df = pd.DataFrame(array2d, columns=["A", "B", "C"])
    igor.root.f["dftest"] = df
    assert np.all(igor.root.dftest.A == array2d[:,0])
    assert np.all(igor.root.dftest.B == array2d[:,1])
    assert np.all(igor.root.dftest.C == array2d[:,2])
    igor.quit_wo_save()

if __name__ == "__main__":
    folder_setattr_test()
    folder_setitem_test()
    wavecollection_setitem_test()
    variablecollection_setitem_test()
    foldercollection_setitem_test()
    print("OK!")
