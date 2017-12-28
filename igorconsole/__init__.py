
import platform

__version__ = "0.2.2"

if platform.system() == "Windows":
    from . import oleconsole
    from . import oleconsts


    #igorapps
    IgorApp = oleconsole.IgorApp
    connect = IgorApp().connect
    run = IgorApp().run
    start = IgorApp().start

    #oleconsts
    consts = oleconsts

    __all__ = ["IgorApp", "connect", "run", "start", "consts"]

else:
    raise NotImplementedError

