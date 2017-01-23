# Put in const.py...
# from http://code.activestate.com/recipes/65207-constants-in-python
class _const:
    class ConstError(TypeError): pass  # base exception class
    class ConstCaseError(ConstError): pass

    __shared_state = {
        'POOL_STATUS_OWNER' : 1,
        'POOL_STATUS_SHARED' : 100,
        'POOL_STATUS_SHARED_WAITING' : 110,
        'POOL_STATUS_SHARED_ACCEPTED' : 120,
        'POOL_STATUS_SHARED_REJECTED' : 130,
        'POOL_STATUS_SHARED_UNLINKED' : 140,
    }
    def __init__(self):
        self.__dict__ = self.__shared_state

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise self.ConstError("Can't change const.%s" % name)
        if not name.isupper():
            raise self.ConstCaseError('const name %r is not all uppercase' % name)
        self.__dict__[name] = value

# replace module entry in sys.modules[__name__] with instance of _const
# (and create additional reference to module so it's not deleted --
#  see Stack Overflow question: http://bit.ly/ff94g6)
import sys
_ref, sys.modules[__name__] = sys.modules[__name__], _const()

if __name__ == '__main__':
    import dbconst  # test this module...

    print "dbconst.POOL_STATUS_OWNER", dbconst.POOL_STATUS_OWNER
    try:
        dbconst.Answer = 42  # not OK, mixed-case attribute name
    except dbconst.ConstCaseError as exc:
        print(exc)
    else:  # test failed - no ConstCaseError exception generated
        raise RuntimeError("Mixed-case const names should't have been allowed!")

    dbconst.ANSWER = 42  # should be OK, all uppercase

    try:
        dbconst.ANSWER = 17  # not OK, attempts to change defined constant
    except dbconst.ConstError as exc:
        print(exc)
    else:  # test failed - no ConstError exception generated
        raise RuntimeError("Shouldn't have been able to change const attribute!")