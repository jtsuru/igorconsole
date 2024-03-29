
import platform

__version__ = "0.4.6"

if platform.system() == "Windows":
    from .oleconsole import oleconsts
    from .oleconsole.oleconsole import IgorApp, OLEIgorWave, OLEIgorVariable, OLEIgorFolder, OLEIgorWaveCollection, OLEIgorVariableCollection, OLEIgorFolderCollection

    connect = IgorApp().connect
    run = IgorApp().run
    start = IgorApp().start
    
    Wave = OLEIgorWave
    Variable = OLEIgorVariable
    Folder = OLEIgorFolder

    WaveCollection = OLEIgorWaveCollection
    VariableCollection = OLEIgorVariableCollection
    FolderCollection = OLEIgorFolderCollection
else:
    raise NotImplementedError("This package currently works only on Windows.")

