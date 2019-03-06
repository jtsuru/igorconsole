from pythoncom import com_error

IgorComError = com_error

class IgorExceptionBase(Exception):
    pass

class IgorTypeError(IgorExceptionBase, TypeError):
    pass

class IgorExcectionError(IgorExceptionBase, RuntimeError):
    pass

class IgorValueError(IgorExceptionBase, ValueError):
    pass
