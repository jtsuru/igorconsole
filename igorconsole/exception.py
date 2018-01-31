class IgorExceptionBase(Exception):
    pass

class IgorTypeError(IgorExceptionBase, TypeError):
    pass