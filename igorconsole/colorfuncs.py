import numpy as np

def to_igor_rgb(obj):
    if isinstance(obj, str):
        result = obj.replace("#", "")
        return tuple(round(int(result[i : i+2], 16)*65535/255)
                     for i in range(0, len(result), 2))

#def geometic_gradation_(ratio, init_rgb=(0,0,0), last_rgb=(1,1,1)):
#    init_rgb = np.asarray(init_rgb, dtype=np.float)
#    last_rgb = np.asarray(last_rgb, dtype=np.float)
#    result = (last_rgb - init_rgb) * ratio + init_rgb
#    return tuple((result * 65535).round().astype(np.uint16))

def geometic_gradation(ratio, rgbs=((1,1,0), (1,0,0))):
    if ratio < 0 or ratio > 1:
        raise ValueError()
    rgbs = [np.asarray(rgb, dtype=np.float) for rgb in rgbs]
    length = len(rgbs)
    section = length - 1
    section_distances = [0] * section
    for i in range(section):
        section_distances[i] = np.linalg.norm(rgbs[i+1] - rgbs[i])
    total_distances = np.fromiter(
        (sum(section_distances[:i]) for i in range(length)),
        dtype=np.float,
        count=length
        )
    total_distances /= total_distances[-1]
    for i in range(section):
        if ratio <= total_distances[i+1]:
            left = ratio - total_distances[i]
            right = total_distances[i+1] - ratio
            result = (right*rgbs[i] + left*rgbs[i+1]) / (left + right)
            break
    return tuple((result * 65535).round().astype(np.uint16))

def arithmetical_gradation(ratio, center_rgb,
                           down_limit=0, upper_limit=1):
    center_rgb = np.asarray(center_rgb, dtype=np.float32)
    min_rgb = center_rgb.min()
    max_rgb = center_rgb.max()
    result = (upper_limit - max_rgb + min_rgb) * ratio + center_rgb
    return tuple((result * 65535).round().astype(np.uint16))

def hot_to_cold_gradation(ratio):
    return geometic_gradation(ratio, rgbs=[(1,0,0),(1,1,0),(0,1,0),(0,1,1),(0,0,1)])

#def hot_to_cold_gradation(ratio):
#    red = np.array([1, 0, 0])
#    yellow = np.array([1, 1, 0])
#    green = np.array([0, 1, 0])
#    cyan = np.array([0, 1, 1])
#    blue = np.array([0, 0, 1])
#    if ratio < 0:
#        raise ValueError()
#    elif ratio < 0.25:
#        result = red + (yellow - red) * ratio
#    elif ratio < 0.5:
#        result = yellow + (green - yellow) * (ratio - 0.25)
#    elif ratio < 0.75:
#        result = green + (cyan - green) * (ratio - 0.5)
#    elif ratio <= 1:
#        result = cyan + (blue - cyan) * (ratio - 0.75)
#    else:
#        raise ValueError()
#    return tuple((result * 65535).round().astype(np.uint16))

gradation = {
    "geometic": geometic_gradation,
    "arithemetical": arithmetical_gradation,
    "hot-to-cold": hot_to_cold_gradation,
    "rainbow": lambda ratio: geometic_gradation(ratio, 
        rgbs=[(1,0,0),(1,1,0),(0,1,0),(0,1,1),(0,0,1),(0.5,0,0.8)]),
    "1-rgb": lambda ratio: geometic_gradation(ratio, 
        rgbs=[(0, 0, 0.8),(0, 0, 1),(0, 0.9, 1),(1, 0.9, 0)]),
    "1-cmyk":lambda ratio: geometic_gradation(ratio, 
        rgbs=[(0, 0, 1),(0.1, 1, 1),(1, 0.9, 0.1)]),
    "2-rgb": lambda ratio: geometic_gradation(ratio, 
        rgbs=[(0, 0, 1),(1, 0.5, 1),(1, 0.5, 0.5)]),
    "2-cmyk": lambda ratio: geometic_gradation(ratio, 
        rgbs=[(0, 0, 1),(1, 0.3, 1),(1, 0, 0.5)]),
    "3-rgb": lambda ratio: geometic_gradation(ratio, 
        rgbs=[(0.35, 0, 0),(1, 0, 0),(1, 0.5, 0.5),(1,0.92,0)]),
    "3-cmyk": lambda ratio: geometic_gradation(ratio, 
        rgbs=[(0.35, 0, 0),(1, 0, 0),(1,0.92,0.92)]),
    "4-rgb": lambda ratio: geometic_gradation(ratio, 
        rgbs=[(1, 0.5, 0.5),(0,0,0.7)]),
    "4-cmyk": lambda ratio: geometic_gradation(ratio, 
        rgbs=[(1, 0.5, 0.5),(0.2,0.2,0.7)]),
}