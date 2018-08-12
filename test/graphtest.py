import igorconsole
import numpy as np
import time

def display_test():
    igor = igorconsole.start()
    igor.show()
    igor.root.ywave1 = np.arange(10)
    #igor.root.ywave2 = -2.3*igor.root.ywave1 バグ
    igor.root.ywave2 = -2.3*igor.root.ywave1.array
    ywaves = [igor.root.ywave1, (igor.root.ywave1, igor.root.ywave2)]
    
    igor.root.xwave1 = np.arange(10)
    xwaves = [None, igor.root.xwave1]

    winname = [None, "test"]
    title = [None, "testtitle"]
    yaxis = [None, "L", "R"]
    xaxis = [None, "T", "B"]
    frame = [None]
    hide = [False, True]
    #host?
    win_location = [None, (0,0,100,100), (100,100,200,200)]
    unit = [None, "cm", "inch"]
    win_behavior = [0, 1, 2, 3]
    #category_plot?
    #inset_frame?
    vertical = [True, False]
    overwrite = [True, False]
    
    from itertools import product
    from tqdm import tqdm
    for yw, xw, wn, t, ya, xa, frm, h, wl, u, wb, v, o in\
            tqdm(list(product(ywaves, xwaves, winname, title, yaxis, xaxis, frame, hide, win_location, unit, win_behavior, vertical, overwrite))):
        g = igor.display(yw, xwave=xw,
                winname=wn, title=t, yaxis=ya, xaxis=xa,
                frame=frm, hide=h, host=None, win_location=wl,
                unit=u, win_behavior=wb, category_plot=False,
                inset_frame=None, vertical=v, overwrite=o)
        g.kill()
    igor.quit_wo_save()


def graph_mothods_test(graphs):
    pass

if __name__ == "__main__":
    display_test()
    graph_mothods_test([])
    print("OK!")