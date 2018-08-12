import igorconsole
import numpy as np

from tqdm import tqdm

igor = igorconsole.start()

a1d = np.arange(10, dtype=float) + 1
a2d = np.arange(100, dtype=float).reshape(10, 10) + 1
a3d = np.arange(1000, dtype=float).reshape(10, 10, 10) + 1
a4d = np.arange(10000, dtype=float).reshape(10, 10, 10, 10) + 1

igor.root.w1d = a1d
igor.root.w2d = a2d
igor.root.w3d = a3d
igor.root.w4d = a4d

arrays = [a1d, a2d, a3d, a4d]
waves = [igor.root.w1d, igor.root. w2d, igor.root. w3d]

def test_scalar():
    igor.root.floatval = 1.2
    igor.root.compval = 3+2J
    scalars = [1, 1.2, 1+4J, igor.root.floatval, igor.root.compval]
    for s in tqdm(scalars):
        for a, w in tqdm(zip(arrays, waves)):
            assert np.all(a + s == w + s)
            assert type(w + s) == igorconsole.abc.igorobjectlike.ArrayOperatableLikeWave
            assert np.all(s + a == s + w)
            assert type(s + w) == igorconsole.abc.igorobjectlike.ArrayOperatableLikeWave
            assert np.all(a - s == w - s)
            assert type(w - s) == igorconsole.abc.igorobjectlike.ArrayOperatableLikeWave
            assert np.all(s - a == s - w)
            assert type(s - w) == igorconsole.abc.igorobjectlike.ArrayOperatableLikeWave
            assert np.all(a * s == w * s)
            assert type(w * s) == igorconsole.abc.igorobjectlike.ArrayOperatableLikeWave
            assert np.all(s * a == s * w)
            assert type(s * w) == igorconsole.abc.igorobjectlike.ArrayOperatableLikeWave
            assert np.all(a / s == w / s)
            assert type(w / s) == igorconsole.abc.igorobjectlike.ArrayOperatableLikeWave
            assert np.all(s / a == s / w)
            assert type(s / w) == igorconsole.abc.igorobjectlike.ArrayOperatableLikeWave
            if isinstance(s, complex) or isinstance(s, igorconsole.Variable) and isinstance(s.value, complex):
                pass
            else:
                assert np.all(a // s == w // s)
                assert type(w // s) == igorconsole.abc.igorobjectlike.ArrayOperatableLikeWave
                assert np.all(s // a == s // w)
                assert type(s // w) == igorconsole.abc.igorobjectlike.ArrayOperatableLikeWave
                assert np.all(a % s == w % s)
                assert type(w % s) == igorconsole.abc.igorobjectlike.ArrayOperatableLikeWave
                assert np.all(s % a == s % w)
                assert type(s % w) ==igorconsole.abc.igorobjectlike.ArrayOperatableLikeWave

def test_array():
    for a, w in zip(arrays, waves):
        assert np.all(a == w)
        assert np.all(a + a == w + a)
        assert type(w + a) == igorconsole.abc.igorobjectlike.ArrayOperatableLikeWave
        assert np.all(a + a == a + w)
        #assert type(a + w) == igorconsole.igorconvertable.ArrayOperatableLikeWave
        assert np.all(a - a == w - a)
        assert type(w - a) == igorconsole.abc.igorobjectlike.ArrayOperatableLikeWave
        assert np.all(a - a == a - w)
        #assert type(a - w) == igorconsole.igorconvertable.ArrayOperatableLikeWave
        assert np.all(a * a == w * a)
        assert type(w * a) == igorconsole.abc.igorobjectlike.ArrayOperatableLikeWave
        assert np.all(a * a == a * w)
        #assert type(a * w) == igorconsole.igorconvertable.ArrayOperatableLikeWave
        assert np.all(a / a == w / a)
        assert type(w / a) == igorconsole.abc.igorobjectlike.ArrayOperatableLikeWave
        assert np.all(a / a == a / w)
        #assert type(a / w) == igorconsole.igorconvertable.ArrayOperatableLikeWave

        assert np.all(a // a == w // a)
        assert type(w // a) == igorconsole.abc.igorobjectlike.ArrayOperatableLikeWave
        assert np.all(a // a == a // w)
        #assert type(a // w) == igorconsole.igorconvertable.ArrayOperatableLikeWave
        assert np.all(a % a == w % a)
        assert type(w % a) == igorconsole.abc.igorobjectlike.ArrayOperatableLikeWave
        assert np.all(a % a == a % w)
        #assert type(a % w) == igorconsole.igorconvertable.ArrayOperatableLikeWave


if __name__ == "__main__":
    test_scalar()
    for _ in range(100):
        test_array()
    print("OK!")
    igor.quit_wo_save()