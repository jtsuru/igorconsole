この文書は現在、仕様書として存在。未実装。

# Igor Waveに変換可能なオブジェクトの作製方法
Igor Waveに変換可能なオブジェクトを作製するには、duck type的には`_to_igorwave()`メソッドを持ったオブジェクトを作製すればよい。その`_to_igorwave()`メソッドは以下の仕様を満たす必要がある。

`_to_igorwave()`メソッドは辞書を返す。辞書は少なくとも、`np.ndarray`オブジェクトを含む必要がある。
```python
import numpy as np

class As3x2ZeroMatrix:
    def __init__(self):
        pass

    def _to_igorwave(self):
        info = {}
        array = np.zeros(3, 2)
        info["array"] = array #必須

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
