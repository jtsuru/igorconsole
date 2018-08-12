import math
import numpy as np

from pythoncom import com_error

import igorconsole
from igorconsole.exception import *

import logging
from tqdm import tqdm

igor = igorconsole.run()
assert igor.is_visible == False
igor.show()
assert igor.is_visible == True
igor.hide()
assert igor.is_visible == False
igor.show()
assert igor.is_visible == True
igor.get_application #なぜプロパティ？
igor.execute("print 1+1", logged=True)
assert -igor.get_value("-pi") == float(igor.get_value("pi"))
assert igor.fullpath[-8:] == "Igor.exe"
assert igor.name == "Igor Pro"
assert type(igor.version) == float
assert igor.is_experiment_modified == True
assert igor.is_experiment_never_saved == True
igor.write_history("testing...")
igor.new_experiment(only_when_saved=False)
igor.new_experiment(only_when_saved=True)
igor.new_experiment_wo_save()
igor.quit()
igor = igorconsole.run()
igor.root.chdir()
assert igor.cwd.path == "root:"

#Variable test
igor.root.text = "test"
assert igor.root.text == "test"
igor.root.float1 = 2.3
assert igor.root.float1 == 2.3

#Wave test
array = np.arange(100)/4
array2d = np.arange(100).reshape(10,10)*1.5
array4d = (np.arange(10**4)/0.2).reshape(10,10,10,10)
igor.root.wave1 = array
igor.root.wave2 = array2d
igor.root.wave3 = array4d
assert np.allclose(igor.root.wave1.array, array)
assert np.allclose(igor.root.wave2.array, array2d)
assert np.allclose(igor.root.wave3.array, array4d)
try:
    igor.root.asdfjkdlalsdf
    raise AssertionError()
except AttributeError:
    pass

w3 = igor.root.wave3

igor.root["wave3"]
assert w3.app == igor
assert w3.path == "root:wave3"
assert w3.name == "wave3"
assert w3.parent.path == "root:"
w3.reference

assert igorconsole.Wave("root:wave3", igor).reference.Path(False, False) == "root:wave3"
assert igorconsole.Wave(w3.reference, igor).reference.Path(False, False) == "root:wave3"

assert not w3.is_inuse
igor.display(igor.root.wave1)
assert igor.root.wave1.is_inuse

w3.set_unit("cm")
assert w3.get_unit() == "cm"
assert w3.get_scaling(0) == (0.0, 1.0)
assert w3.get_scaling(1) == (0.0, 1.0)
assert w3.get_scaling(2) == (0.0, 1.0)
assert w3.get_scaling(3) == (0.0, 1.0)
try:
    w3.get_scaling(4)
    raise AssertionError
except com_error:
    pass
assert igor.root.wave1.get_scaling(0) == (0.0, 1.0)

assert w3[1,1,1,1] == 5555.0
pos = np.array([1.2, 4.5, 3,2])
assert np.allclose(w3.position(pos), pos)
assert igor.root.wave1.parray.shape == (100,)
assert igor.root.wave2.parray.shape == (10,10,2)
assert w3.parray.shape == (10,10,10,10,4)
assert w3.index(3.2,3,3,2.7) == (3,3,3,3)
assert w3.dtype == np.float64
assert igor.root.wave1.ndim == 1
assert w3.ndim == array4d.ndim
assert w3.shape == array4d.shape
assert w3.size == array4d.size
assert len(w3) == len(array4d)
assert igor.root.wave1[5] == array[5]
assert np.allclose(w3[3:5,3,4], array4d[3:5,3,4])
assert np.allclose(-1 + w3/8 + 0.5*w3 - w3 + 4, -0.375*array4d + 3)

complex_list = [1+1J, 2+3J, 4+5J]
igor.root.comp1 = complex_list
assert (igor.root.comp1.array == np.array(complex_list)).all()
complex_2d = np.arange(100).reshape(10, 10)
complex_2d = complex_2d + 1J*complex_2d
igor.root.comp2d = complex_2d
assert (igor.root.comp2d.array == complex_2d).all()

try:
    igor.root.intc = np.arange(10, dtype=np.intc)
except IgorTypeError:
    pass
try:
    igor.root.intp = np.arange(10, dtype=np.intp)
except IgorTypeError:
    pass
igor.root.nppow = np.arange(10) ** 2

#folder test
igor.root.make_folder("abc")
igor.root.make_folder("123")
igor.root.make_folder("___123")
assert igor.root.abc.path == igor.root["abc"].path
igor.root["123"].aaa = [1.2,1.4,1.5]
igor.root.abc.ppp = np.arange(10)
igor.root["123"].chdir()
assert igor.root["123"].path == "root:123:"
igor.display(igor.root["123"].aaa)
igor.root.abc.chdir()
assert igor.root.abc.path == igor.root["abc"].path
igor.display(igor.cwd.ppp)

#graph test
igor.root.testx = [1,2,3,4,5]
igor.root.testy1 = [7.0,6.5,6.0,5.5,5.0]
igor.root.testy2 = [1,1,1,1,1]
graph = igor.display([igor.root.testy1, igor.root.testy2],
                     igor.root.testx,
                     title="testgraph")

assert graph.app == igor

#append to waves short
igor.root.a = []
igor.root.b = []
igor.root.c = []
igor.root.d = []
igor.root.g = []
igor.root.h = []
waves = [igor.root.a, igor.root.b, igor.root.c, igor.root.d, igor.root.g, igor.root.h]
igor.display([igor.root.b], igor.root.a)
for i in tqdm(range(100)):
	igor.append_to_waves(waves,[i/10 * math.cos(i)/10,i/10 * math.sin(i)/10,3,4,5,6])

#append to waves short diff length
igor.root.a = []
igor.root.b = [1.0]
igor.root.c = [1]
igor.root.d = [1,2]
igor.root.g = [1]
igor.root.h = [1,2,3]
waves = [igor.root.a, igor.root.b, igor.root.c, igor.root.d, igor.root.g, igor.root.h]
igor.display([igor.root.b], igor.root.a)
for i in tqdm(range(100)):
	igor.append_to_waves(waves,[i/10 * math.cos(i)/10,i/10 * math.sin(i)/10,3,4,5,6])

#append to waves long
f = igor.root
for _ in range(2):
    f = f.make_folder("a"* 30)
    f.chdir()
igor.cwd.aaaaaaaaaa = []
igor.cwd.bbbbbbbbbb = []
igor.cwd.cccccccccc = []
igor.cwd.dddddddddd = []
igor.cwd.ffffffffff = []
igor.cwd.gggggggggg = []
waves = [igor.cwd.aaaaaaaaaa,igor.cwd.bbbbbbbbbb,igor.cwd.cccccccccc,
igor.cwd.dddddddddd,igor.cwd.ffffffffff,igor.cwd.gggggggggg]
igor.display([igor.cwd.bbbbbbbbbb], igor.cwd.aaaaaaaaaa)
for i in range(100):
	igor.append_to_waves(waves,[i/10 * math.cos(i)/10,i/10 * math.sin(i)/10,3,4,5,6])

#append to waves long diff length
igor.cwd.aaaaaaaaaa = []
igor.cwd.bbbbbbbbbb = [1]
igor.cwd.cccccccccc = [1,2]
igor.cwd.dddddddddd = [1,2,3]
igor.cwd.ffffffffff = []
igor.cwd.gggggggggg = [1]
waves = [igor.cwd.aaaaaaaaaa,igor.cwd.bbbbbbbbbb,igor.cwd.cccccccccc,
igor.cwd.dddddddddd,igor.cwd.ffffffffff,igor.cwd.gggggggggg]
igor.display([igor.cwd.bbbbbbbbbb], igor.cwd.aaaaaaaaaa)
for i in tqdm(range(100)):
	igor.append_to_waves(waves,[i/10 * math.cos(i)/10,i/10 * math.sin(i)/10,3,4,5,6])

#append to waves too long
f = igor.root
for _ in range(10):
    f = f.make_folder("b"* 30)
    f.chdir()
igor.cwd.aaaaaaaaaa = []
igor.cwd.bbbbbbbbbb = []
igor.cwd.cccccccccc = []
igor.cwd.dddddddddd = []
igor.cwd.ffffffffff = []
igor.cwd.gggggggggg = []
waves = [igor.cwd.aaaaaaaaaa,igor.cwd.bbbbbbbbbb,igor.cwd.cccccccccc,
igor.cwd.dddddddddd,igor.cwd.ffffffffff,igor.cwd.gggggggggg]
igor.display([igor.cwd.bbbbbbbbbb], igor.cwd.aaaaaaaaaa)
for i in tqdm(range(100)):
	igor.append_to_waves(waves,[i/10 * math.cos(i)/10,i/10 * math.sin(i)/10,3,4,5,6])


igor.cwd.aaaaaaaaaa = []
igor.cwd.bbbbbbbbbb = [1,2]
igor.cwd.cccccccccc = [1,2,3]
igor.cwd.dddddddddd = []
igor.cwd.ffffffffff = [1]
igor.cwd.gggggggggg = [1,2]
waves = [igor.cwd.aaaaaaaaaa,igor.cwd.bbbbbbbbbb,igor.cwd.cccccccccc,
igor.cwd.dddddddddd,igor.cwd.ffffffffff,igor.cwd.gggggggggg]
igor.display([igor.cwd.bbbbbbbbbb], igor.cwd.aaaaaaaaaa)
for i in tqdm(range(100)):
	igor.append_to_waves(waves,[i/10 * math.cos(i)/10,i/10 * math.sin(i)/10,3,4,5,6])

#toomany
waves = []
for i in range(500):
    waves.append(igor.root.make_wave("a" + str(i)))
for i in tqdm(range(100)):
    igor.append_to_waves(waves, np.arange(500).tolist())

print("Test passed!")