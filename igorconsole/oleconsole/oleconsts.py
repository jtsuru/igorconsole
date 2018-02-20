class CompileProcedure:
    NoErrorDialog = 1

class DataType:
    Complex = 1
    Double = 4
    Float = 2
    SignedByte = 8
    SignedLong = 32
    SignedShort = 16
    Text = 0
    UnsignedByte = 72
    UnsignedLong = 96
    UnsignedShort = 80

class Execute2:
    Silent = 1

class ExpFileType:
    Default = -1
    Packed = 1
    Unpacked = 0

class FileKind:
    Help = 13
    Notebook = 11
    Procedure = 12

class LoadType:
    Merge = 5
    Open = 2
    Stationery = 4

class OpenFile:
    Invisible = 2
    ReadOnly = 1

class SaveType:
    Save = 1
    SaveAs = 2
    SaveCopy = 3

class Status:
    ExperimentModified = 5
    ExperimentNeverSaved = 6
    IgorVersion = 1
    OperationQueueIsEmpty = 3
    PauseForUser = 4
    ProceduresCompiled = 7
    RunningProcedure = 2

class WindowType:
    Graph = 1
    Table = 2
    Layout = 4
    Panel = 64

class WaveDimension:
    Row = 1
    Column = 2
    Layer = 3
    Chunk = 4
    Data = -1
