"""
General utilitity functions for the case_class module.

Copyright (c) 2016 Tom Wiesing -- licensed under MIT, see LICENSE
"""

import sys
import types


def exec_(_code_, _globs_=None, _locs_=None):
    """
    Like the built-in function exec(), but for Python 2 and 3. Adapted from
    the six library.

    :param _code_: Code to run.
    :type _code_: str

    :param _globs_: Global variables to use.
    :type _globs_: dict

    :param _locs_: Local variables to use.
    :type _locs_: dict

    :return: nothing
    """

    # Python 3: It just works
    if sys.version_info[0] == 3:
        import builtins
        getattr(builtins, "exec")(_code_, _globs_, _locs_)

    # Python 2: More work needed
    else:
        if _globs_ is None:
            frame = sys._getframe(1)
            _globs_ = frame.f_globals
            if _locs_ is None:
                _locs_ = frame.f_locals
            del frame
        elif _locs_ is None:
            _locs_ = _globs_

        exec("exec _code_ in _globs_, _locs_")


def is_string(o):
    """ Checks if an object is a string.

    :param o: Object to check
    :type o: object

    :rtype: bool
    """
    try:
        return isinstance(o, basestring)
    except NameError:
        return isinstance(o, str)


def is_lambda(o):
    """ Checks if an object is a Lambda function.
    Adapted from http://stackoverflow.com/a/23852434

    :param o: Object to check
    :type o: object

    :rtype: bool
    """

    return isinstance(o, types.LambdaType) and o.__name__ == "<lambda>"


__all__ = ["exec_"]
