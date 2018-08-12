# Igor Waveに変換可能なオブジェクトの作製方法
Igor Waveに変換可能なオブジェクトを作製するには、
1. `_igorconsole_to_igorvariable()`
2. `_igorconsole_to_igorwave()`
3. `_igorconsole_to_igorfolder()`

のいずれかのメソッドを持ったオブジェクトを作製すればよい。
各メソッドはそれぞれ
1. `folderobject.v[name] = object_convertable_to_igor_variable`
2. `folderobject.w[name] = object_convertable_to_igor_wave`
3. `folderobject.f[name] = object_convertable_to_igor_folder`

の最中に呼ばれる。なお、`folderobject.name = object_convertable_to_igor_folder`の形で代入された場合には、3つのメソッドのうちどれが存在するかという情報を元にして、Variable、Wave、Folderのいずれかとして代入操作を行う。


各メソッドは以下の仕様を満たす必要がある。
## _igorconsole_to_igorvariable()メソッドの仕様
1. _igorconsole_to_igorvariable()は条件2～3を満たす`dict`を返す。
2. keyに`"type"`を持ち、その値は`"IgorVariable"`である。
3. keyに`"value"`を持ち、その値は代入すべき数値もしくは文字列である。
4. `"type"`、`"value"`以外のkeyは無視される。
### 例
```python
class AsVariable:
    def __init__(self, value):
        self.value = value
    
    def _igorconsole_to_igorvariable(self):
        info = {
            "type": "IgorVariable", #必須、case sensitive
            "value": self.value #必須
        }
        return info

if __name__ == "__main__":
    import igorconsole
    igor = igorconsole.start()
    variablelike = AsVariable(1.3)
    igor.root.val = variablelike
```
## _igorconsole_to_igorwave()メソッドの仕様
1. `_igorconsole_to_igorwave()`メソッドは以下の仕様を満たす1～6を満たす`dict`を返す。
2. keyに`"type"`を持ち、その値は`"IgorWave"`である。
3. keyに`"array"`を持ち、その値は`np.ndarray`オブジェクトである。値であるnp.ndarrayのdtypeはそのまま代入後のwaveの型となる。別途dtypeの指定はできない。
4. 必要であれば、keyに`"scalings"`、`"units"`を持つことができる。scalingsは軸のスケール指定、unitsは軸の単位指定に用いられる。
5. scalingsを指定する場合、keyに`"scalings"`を持つ。その値は5つのタプルを含むリスト`[(データのみなし最小値, データのみなし傾き), (x軸の最小値, x軸の感覚), (y軸の最小値, y軸の感覚), (z軸の最小値, z軸の感覚), (t軸の最小値, t軸の感覚)]`である。たとえ作製するwaveが3次元以下であったとしても長さの変更は認められない。scalingが無指定の場合のデフォルト値は`[(0.0, 0.0), (0.0, 1.0), (0.0, 1.0), (0.0, 1.0), (0.0, 1.0)]`である。
6. unitsを指定する場合、keyに`"units"`を持つ。その値は5つのタプルを含むリスト`["データの単位", "x軸の単位", "y軸の単位", "z軸の単位", "t軸の単位"]`である。たとえ作製するwaveが3次元以下であったとしても長さの変更は認められない。scalingが無指定の場合のデフォルト値は`["", "", "", "", ""]`である。

##例
```python
import numpy as np

class AsMatrix:
    def __init__(self, matrix):
        self.matrix = matrix

    def _to_igorwave(self):
        info = {}
        info["array"] = self.matrix #必須

        data_init, data_grad = (0, 0)
        x_init, x_grad = (0, 1)
        y_init, y_grad = (0, 1)
        z_init, z_grad = (0, 1)
        t_init, t_grad = (0, 1)
        info["scalingｓ"] = [
            (data_init, data_grad),
            (x_init, x_grad),
            (y_init, y_grad),
            (z_init, z_grad),
        ] #optional

        data_unit = "N"
        x_unit = "um"
        y_unit = "um"
        z_unit = "um"
        t_unit = "s"
        info["units"] = [
            data_unit,
            x_unit
            y_unit
            z_unit
        ]
        return info

if __name__ == "__main__":
    import igorconsole
    igor = igorconsole.start()
    wavelike = As3x2ZeroMatrix()
    igor.root.wave1 = wavelike
```
## _igorconsole_to_igorfolder()メソッドの仕様
1. `_igorconsole_to_igordatafolder()`メソッドは以下の仕様を満たす2～を満たす`dict`を返す。
2. keyに`"type"`を持ち、その値は`"IgorFolder"`である。
3. keyに`"subfolders"`を持ち、その値は`dict`型インスタンスである。サブフォルダが存在しない場合`"subfolders"`の値は`{}`である。サブフォルダが存在する場合`dict`のkeyはサブフォルダの名前であり、その値は本項目2～を満たす`dict`である。
4. keyに`"contents"`を持ち、その値は`dict`型である。フォルダ内にwaveもvariableも存在しない場合`"contents"`の値は`{}`である。
5. lllllllllllllllllllllllllllllllllllllllllllllll

## 補足
`_igorconsole_to_igordatafolder()`が返す`dict`は、サブフォルダが、dict`["subfolders"]`に、waveとvariableがdict`["contents"]`に含まれることに注意する。
これは少々分かりづらいが、waveとvariableが共通の名前空間で扱われているのに対し、フォルダが独立した名前空間を与えられているという、igorの仕様に由来する。

つまり、igorでは同一フォルダ内のwaveとvariableに同じ名前を付けることはできないが、サブフォルダと名前がかぶるのは問題が無い。dictはkeyがユニークであるので、フォルダとwave,dictに別のdictを用いることで自然とこの仕様が満たされるようにしている。
## 例
例として、igorconsole内のFolderクラスの実装を示す。
```python
    def _igorconsole_to_igorfolder(self):
        folders = {}
        for f in self.subfolders:
            folders[f.name] = f._igorconsole_to_igorfolder()
        contents = {}
        for v in self.variables:
            contents[v.name] = v._igorconsole_to_igorvariable()
        for w in self.waves:
            contents[w.name] = w._igorconsole_to_igorwave()
        info = {
            "type": "IgorFolder", #必須
            "subfolders": folders, #必須
            "contents": contents #必須
        }
        return info
```
リターンされる辞書は、少なくとも`"type"`、`"subfolders"`、`"subfolders"`を含んでいる。

```python
import json

import numpy as np

class Spectrum:
    def __init__(self, xarray: np.ndarray, yarray: np.ndarray, metadata: dict):
        self.xarray = xarray
        self.yarray = yarray
        self.metadata = metadata
    
    def _igorconsole_to_igorfolder(self):        
        contents = {}
        contents["class"] = {
            "type": "IgorVariable",
            "value": "mydummypackage.mydummymodule.Spectrum"
        }
        contents["metadata"] = {
            "type": "IgorVariable",
            "value": json.dumps(self.info)
        }
        contents["xarray"] = {
            "type": "IgorWave",
            "array": self.xarray,
            "units": ["cm\S-1\M", "", "", "", ""]
        }
        contents["yarray"] = {
            "type": "IgorWave",
            "array": self.yarray,
            "units": ["counts s\S-1\M", "", "", "", ""]
        }
        info = {
            "type": "IgorFolder",
            "subfolders": {},
            "contents": contents
        }
        return info
    
    @classmethod
    def from_igor(cls, igorfolder):
        if not hasattr(igorfolder, "_igorconsole_to_igorfolder"):
            raise TypeError("not a igor folder.")
        info = igorfolder._igorconsole_to_igorfolder()
        if ("class" not in info) or info["class"]\
            != "mydummypackage.mydummymodule.Spectrum":
            raise ValueError("not a folder created by this class.")
        xarray = info["contents"]["xarray"]["array"]
        yarray = info["contents"]["yarray"]["array"]
        metadata = json.loads(info["contents"]["metadata"]["value"])
        return cls(xarray, yarray, metadata)


class SpectrumCollection:
    def __init__(self, spectra: list):
        self.spectra = spectra

    def _igorconsole_to_igorfolder(self):
        contents = {}
        contents["class"] = {
            "type": "IgorVariable",
            "value": "mydummypackage.mydummymodule.SpectrumCollection"
        }
        subfolders = {}
        for i, item in enumerate(self.spectra):
            subfolders["Spectrum_" + str(i)] = item._igorconsole_to_igorfolder()
        info = {
            "type": "IgorFolder",
            "subfolders": subfolders,
            "contents": contents
        }
        return info

    @classmethod
    def from_igor(cls, igorfolder):
        if not hasattr(igorfolder, "_igorconsole_to_igorfolder"):
            raise TypeError("not a igor folder.")
        info = igorfolder._igorconsole_to_igorfolder()
        if ("class" not in info) or info["class"]\
            != "mydummypackage.mydummymodule.SpectrumCollection":
            raise ValueError("not a folder created by this class.")
        spectra_list = []
        for folder in info["subfolders"]:
            xarray = info["contents"]["xarray"]["array"]
            yarray = info["contents"]["yarray"]["array"]
            metadata = json.loads(info["contents"]["metadata"]["value"])
            spectra_list.append(Spectrum(xarray, yarray, metadata))
        return cls(spectra_list)
```