"""
General functions for the case_class module.

Copyright (c) 2016 Tom Wiesing -- licensed under MIT, see LICENSE
"""

import sys


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


__all__ = ["exec_"]
