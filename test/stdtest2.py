import numpy as np

import igorconsole

def setattr_test():
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

def setitem_test():
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

if __name__ == "__main__":
    setattr_test()
    setitem_test()
    print("OK!")
