"""
CaseClass.py - Scala-like CaseClasses for Python

----
Copyright (c) 2016 Tom Wiesing

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

----

Part of this code (see in the comments below) has been adapted from the six
Python library. It is licensed as follows:

Copyright (c) 2010-2015 Benjamin Peterson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import inspect
import sys


class _Utilities(object):
    """ Object containing all utility functions.  """

    ARGUMENT_POS = "pos"
    VAR_POS = "pvar"
    ARGUMENT_KW = "kw"
    VAR_KW = "kwvar"

    @staticmethod
    def get_signature(f):
        """ Extract a signature from a function.

        :param f: Function to extract signature from.

        :return: A pair of (arguments, mapping) as a list of arguments and a
        mapping from names to finding the variables.
        :rtype: tuple
        """

        # STEP 1: Inspect the function
        try:
            # try with get full argspec
            (pa, van, kwvan, pdef, kwonly, kwdef, annots) \
                = inspect.getfullargspec(f)

        # work around <slot_wrapper> objects by giving a sensible defaults
        except TypeError:
                (pa, van, kwvan, pdef, kwonly, kwdef, annots) = (
                    ['self'],
                    None,
                    None,
                    [],
                    {},
                    {},
                    {}
                )

        # in case there is getfullargspec
        except AttributeError:

            try:
                # try the regular one
                (pa, van, kwvan, pdef) = inspect.getargspec(f)
                annots = {}
                kwonly = {}
                kwdef = {}

            # work around <slot_wrapper> objects by giving a sensible defaults
            except TypeError:
                (pa, van, kwvan, pdef, kwonly, kwdef, annots) = (
                    ['self'],
                    None,
                    None,
                    [],
                    {},
                    {},
                    {}
                )

        # STEP 2: Merge the defaults
        defaults = kwdef.copy() if kwdef is not None else {}

        for (i, d) in enumerate(pdef if pdef is not None else []):
            defaults[pa[-(i + 1)]] = d

        # STEP 3: Go over them one by one
        arguments = []
        mapping = {}
        nkwvar = []

        # Positionals
        for (i, a) in enumerate(pa):
            arg = {'name': a}
            mapping[a] = (_Utilities.ARGUMENT_POS, i,
                          defaults[a] if a in defaults else None)

            if a in defaults:
                arg['type'] = _Utilities.ARGUMENT_KW
                arg['default'] = defaults[a]
                nkwvar.append(a)
            else:
                arg['type'] = _Utilities.ARGUMENT_POS
                nkwvar.append(a)

            if a in annots:
                arg['annot'] = annots[a]

            arguments.append(arg)

        # VARARG
        if van is not None:
            arg = {'name': van, 'type': _Utilities.VAR_POS}
            mapping[van] = (_Utilities.VAR_POS, len(pa), None)

            if van in annots:
                arg['annot'] = annots[van]

            arguments.append(arg)

        # Keyword-only
        for a in kwonly:
            arg = {'name': a, 'type': _Utilities.ARGUMENT_KW,
                   'default': defaults[a]}

            mapping[a] = (_Utilities.ARGUMENT_KW, a, defaults[a])
            nkwvar.append(a)

            if a in annots:
                arg['annot'] = annots[a]

            arguments.append(arg)

        # KW VARAGR
        if kwvan is not None:
            arg = {'name': kwvan, 'type': _Utilities.VAR_KW}
            mapping[kwvan] = (_Utilities.VAR_KW, nkwvar, None)

            if kwvan in annots:
                arg['annot'] = annots[kwvan]

            arguments.append(arg)

        # and return the arguments
        return arguments, mapping

    @staticmethod
    def with_signature(name, sig):
        """ Function decorator that returns a function with the given
        signature.

        :param name: Name of new function.
        :type name: str

        :param sig: Signature to apply. As returned by get_signature.
        :type sig: tuple
        """

        (arguments, _) = sig

        name_prefix = ''.join(map(lambda arg: arg['name'], arguments)) + name
        func_name = '%sorig' % (name_prefix,)

        # dictionary of default variables
        default_vars = {}
        default_var_name = '%sdefaults' % (name_prefix, )

        def argument_to_str(arg):
            a_str = ''

            tp = arg['type']
            nm = arg['name']

            if tp == _Utilities.VAR_POS:
                a_str += '*%s' % (nm, )
            elif tp == _Utilities.VAR_KW:
                a_str += '**%s' % (nm, )
            else:
                a_str += '%s' % (nm, )

            b_str = a_str

            if 'default' in arg:
                b_str += '=%s[%r]' % (default_var_name, nm)
                a_str = '%s=%s' % (a_str, a_str)
                default_vars[nm] = arg['default']

            return a_str, b_str

        call_strs = []
        param_strs = []

        for (a, b) in map(argument_to_str, arguments):
            call_strs.append(a)
            param_strs.append(b)

        call_str = ','.join(call_strs)
        param_str = ','.join(param_strs)

        code = 'def %s(%s):\n    return %s(%s)' % \
               (name, param_str, func_name, call_str)

        def wrapper(f):
            local_vars = {default_var_name: default_vars, func_name: f}

            _Utilities.exec_(code, local_vars)

            return local_vars[name]

        return wrapper

    @staticmethod
    def get_init_signature(cls):
        """ Gets the signature of an init function of a class.

        :param cls: Class to get init signature of.
        :type cls: type

        :return: A pair of (arguments, mapping) as a list of arguments and a
        mapping from names to finding the variables.
        :rtype: tuple
        """

        # get the init method
        init_method = \
            _Utilities.get_method("__init__", cls.__dict__, cls.__bases__)

        # HACK: Do not allow object.__init
        if init_method is object.__init__:
            def init_method(self):
                return None

        return _Utilities.get_signature(init_method)

    @staticmethod
    def get_class_parameters(cls, *args, **kwargs):
        """ Substitutes parameters passed to a class with the correct defaults.

        :param cls: Class parameters to clean up.
        :type cls: type

        :param args: Arguments passed to class.
        :type args: list

        :param kwargs: Keyword arguments passed to class
        :type kwargs: dict

        :return: a tuple (args, kwargs) of normal and keyword arguments.
        :rtype: tuple
        """

        init_sig = _Utilities.get_init_signature(cls)

        @_Utilities.with_signature('__init__', init_sig)
        def get_signature(*a, **kw):
            return a, kw

        return get_signature(None, *args, **kwargs)

    @staticmethod
    def get_argument_by_name(name, mapping, args, kwargs):
        """ Gets a function argument by name. """

        # if we do not have it, throw an error
        if name not in mapping:
            raise AttributeError

        # look up where it is
        (tp, spec, default) = mapping[name]

        # positional argument ==> return it
        if tp == _Utilities.ARGUMENT_POS:
            try:
                return args[spec]
            except IndexError:
                return kwargs[name]
            except KeyError:
                return default

        # VARARG ==> take the ones that are not others
        elif tp == _Utilities.VAR_POS:
            return args[spec:]

        # KEYWORD_ARGUMENTS ==> return it.
        elif tp == _Utilities.ARGUMENT_KW:
            try:
                return kwargs[spec]
            except KeyError:
                return default

        # KWVARARG ==> remove all the others.
        elif tp == _Utilities.VAR_KW:
            kwargs = kwargs.copy()

            for p in spec:
                try:
                    kwargs.pop(p)
                except KeyError:
                    pass

            return kwargs

    @staticmethod
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

    @staticmethod
    def get_method(name, attrs, bases):
        """ Gets a method of a class by name.

        :param name: Name of method to get.
        :type name: str

        :param attrs: Dictionary of class attributes.
        :type attrs: dict

        :param bases: Bases for the class to use for lookup.
        :type bases: list

        :return: The class method or None
        """

        # If the method is present return it directly.
        if name in attrs:
            return attrs[name]

        # Try to find the method one by one
        for b in bases:
            sub_method = _Utilities.get_method(name, b.__dict__, b.__bases__)

            if sub_method is not None:
                return sub_method

        # else return None
        return None

    @staticmethod
    def add_metaclass(meta):
        """ Class decorator for creating a class with a metaclass. Adapted
        from the six library. See license notice above. """

        def wrapper(cls):
            org_cls = cls.__dict__.copy()
            slots = org_cls.get('__slots__')

            if slots is not None:
                if isinstance(slots, str):
                    slots = [slots]
                for slots_var in slots:
                    org_cls.pop(slots_var)

            org_cls.pop('__dict__', None)
            org_cls.pop('__weakref__', None)

            return meta(cls.__name__, cls.__bases__, org_cls)

        return wrapper
#
# Meta-classes for the case class
#


class CaseClassMeta(type):
    """ Meta-Class for case classes. """

    instance_keys = {}
    instance_values = {}
    instance_list = []

    def __new__(mcs, name, bases, attrs):
        """ Creates a new class with MetaClass CaseClassMeta.
        :param name: Name of the class to create.
        :type name: str

        :param bases: Base classes for the class.
        :type bases: list

        :param attrs: Attributes of this class.
        :type attrs: dict

        :rtype: CaseClassMeta
        """

        # no case-to-case inheritance outside of the base classes
        if _CaseClass not in bases and \
                CaseClassMeta.inherits_from_case_class(bases):
            raise NoCaseToCaseInheritanceException(name)

        # now we can just create it normally.
        return super(CaseClassMeta, mcs).__new__(mcs, name, bases, attrs)

    def __call__(cls, *args, **kwargs):
        """ Creates a new CaseClass() instance.

        :param args: Arguments to this CaseClass instance.
        :type args: list

        :param kwargs: Keyword arguments to this CaseClass instance.
        :type kwargs: dict

        :rtype: CaseClass
        """

        # Can not instantiate Abstract Case Class
        if AbstractCaseClass in cls.__bases__:
            raise NotInstantiableAbstractCaseClassException(cls)

        # may not instantiate sub classes of _CaseClass
        if _CaseClass in cls.__bases__:
            raise NotInstantiableClassException(
                "Cannot instantiate %s: " % (cls.__name__, ) +
                "Classes inheriting directly from _CaseClass may not be " +
                "instantiated. ", cls)

        # make sure we have the dictionary
        if cls not in CaseClassMeta.instance_keys:
            CaseClassMeta.instance_keys[cls] = []
            CaseClassMeta.instance_values[cls] = {}

        # Extract the instances for this class
        ckey = CaseClassMeta.instance_keys[cls]
        cval = CaseClassMeta.instance_values[cls]

        # key we will use for this instance.
        key = _Utilities.get_class_parameters(cls, *args, **kwargs)

        # try and return an existing instance.
        try:
            return cval[ckey.index(key)]
        except ValueError:
            pass

        # create a new instance
        instance = super(CaseClassMeta, cls).__call__(*args, **kwargs)

        # store the instance
        idx = len(ckey)
        ckey.append(key)
        cval[idx] = instance

        # and return it
        return instance

    def __getitem__(cls, item):
        """ Syntactic sugar to create new CaseClass instances.

        :param item: Tuple representing parameters or slice instance.
        :type item: Any

        :rtype: CaseClass
        """

        # allow CaseClass[:] to create a new CaseClass()
        if isinstance(item, slice):
            if item.start is None and item.stop is None and item.step is None:
                return CaseClassMeta.__call__(cls)

        # if we get a single item, it needs to be turned into a tuple.
        elif not isinstance(item, tuple):
            item = (item,)

        # finally just do the same as in call.
        return CaseClassMeta.__call__(cls, *item)

    @staticmethod
    def get_hash(cc):
        """ Gets a hash for a CaseClass or None.

        :param cc: CaseClass instance to get hash for
        :type cc: CaseClass

        :rtype: int
        """

        if not isinstance(cc, CaseClass):
            raise ValueError("Argument is not a CaseClass, can not get hash. ")

        # get a key for the instance
        cls = cc.__class__
        key = (cc.case_args, cc.case_kwargs)

        # extract the key
        ckey = CaseClassMeta.instance_keys[cls]
        idx = ckey.index(key)

        # and return a hash of it
        return hash((CaseClassMeta, ckey, idx))

    @staticmethod
    def is_concrete_caseclass(cls):
        """ Checks if a class is a concrete case class via inheritance.

        :param cls: Class to check.
        :type cls: type

        :rtype: bool
        """

        return cls != AbstractCaseClass and CaseClass in cls.__bases__

    @staticmethod
    def inherits_from_case_class(bases):
        """ Checks if this class inherits from a non-inheritable case class.

        :param bases: List of bases of the class to check
        :type bases: list

        :rtype: bool
        """

        # if we can inherit from it, we are already done.
        if InheritableCaseClass in bases:
            return False

        for b in bases:
            if CaseClassMeta.is_concrete_caseclass(b):
                return True

        return False


class _CaseClass(object):
    """ A class used as base for all CaseClasses"""

    pass


@_Utilities.add_metaclass(CaseClassMeta)
class CaseClass(_CaseClass):
    """ Represents a normal CaseClass. """

    def __new__(cls, *args, **kwargs):
        """ Creates a new CaseClass instance.

        :param args: Parameters for this CaseClass instance.
        :type args: list

        :param kwargs: Keyword Arguments for this CaseClass instance.
        :type kwargs: dict

        :rtype: CaseClass
        """

        # create a new instance
        inst = super(CaseClass, cls).__new__(cls)

        # get the init signature
        init_sig = _Utilities.get_init_signature(inst.__class__)

        # cleanup the arguments
        (cargs, kwcargs) = _Utilities.\
            get_class_parameters(inst.__class__, *args, **kwargs)

        # HACK: remove the first element
        cargs = cargs[1:]

        # Name of the class
        inst.__name = inst.__class__.__name__

        # The signature of the original function
        inst.__init_sig = init_sig

        # The arguments given to this case class
        inst.__args = list(cargs)

        # The keyword arguments given to this case class
        inst.__kwargs = kwcargs

        # and return the instance
        return inst

    def __hash__(self):
        """ Returns a hash representing this case class.

        :rtype: int
        """

        return CaseClassMeta.get_hash(self)

    @property
    def case_params(self):
        """ Returns the parameters originally given to this CaseClass.

        :rtype: CaseParameters
        """

        return CaseParameters(self.__init_sig, self.__args, self.__kwargs)

    def __repr__(self):
        """ Implements a representation for CaseClass instances. This is given
        by the class name and the representation of all the parameters.

        :rtype: str
        """

        # name of the class and parameters
        return "%s(%s)" % (self.__name, self.case_params)


class AbstractCaseClass(CaseClass, _CaseClass):
    """ Represents a CaseClass that may not be instantiated but only inherited
    from. """

    pass


class InheritableCaseClass(CaseClass, _CaseClass):
    """ Represent a CaseClass that may be inherited from. """

    pass


class CaseParameters(CaseClass, dict):
    """ Represents arguments given to a CaseClass. """

    def __init__(self, init_sig, args, kwargs):
        """ Creates a new CaseArguments() instance.

        :param init_sig: Signature of the original __init__ function, as
        returned by _Utilities.get_signature.
        :type init_sig: tuple

        :param args: Arguments to wrap
        :type args: list

        :param kwargs: Keyword Arguments to wrap.
        :type kwargs: dict
        """

        # unpack arguments
        (arg_list, arg_map) = init_sig

        # Build a true dictionary of arguments
        self.__params = {}
        self.__arg_list = arg_list
        self.__args = args

        args_with_none = [None] + self.__args

        for arg in arg_list[1:]:
            n = arg['name']
            self.__params[n] = _Utilities.get_argument_by_name(n, arg_map,
                                                               args_with_none,
                                                               kwargs)

        super(CaseParameters, self).__init__(self.__params)

    def __getitem__(self, n):
        """ Returns a positional CaseClass parameter.

        :param n: Number of item to get.
        :type n: int
        :rtype: object
        """

        return self.__args[n]

    def __len__(self):
        """ Returns the number of positional arguments this CaseParameters
        instance has.

        :rtype: int
        """

        return len(self.__args)

    def __iter__(self):
        """ Yields all positional arguments this CaseParameters instance
        has. """

        for a in self.__args:
            yield a

    def __getattr__(self, name):
        """ Gets a parameter given to this CaseParameters instance by name.

        :param name: Name of parameter to get
        :type name: str
        """

        return self.__params[name]

    def __str__(self):
        def type_str(a):

            tp = a['type']
            name = a['name']
            value = self.__params[name]

            if tp == _Utilities.ARGUMENT_POS:
                return '%r' % (value,)
            elif tp == _Utilities.VAR_POS:
                return '*%s=%r' % (name, tuple(value))
            elif tp == _Utilities.ARGUMENT_KW:
                return '%s=%r' % (name, value)
            elif tp == _Utilities.VAR_KW:
                return '**%s=%r' % (name, value)

        return ', '.join(map(type_str, self.__arg_list[1:]))

    def __repr__(self):
        super(CaseParameters, self).__repr__()


class NotInstantiableClassException(Exception):
    """ Exception that is raised when a class can not be
    instantiated. """

    def __init__(self, msg, cls):
        """ Creates a new NotInstantiableClassException instance.

        :param msg: Message representing this NotInstantiableException.
        :type msg: str

        :param cls: Class that the user tried to instantiate.
        :type cls: type
        """

        super(NotInstantiableClassException, self).__init__(msg)

        self.msg = msg
        self.cls = cls


class NotInstantiableAbstractCaseClassException\
            (NotInstantiableClassException):
    """ Represents an exception that is raised when an AbstractCaseClass is
     instantiated. """

    def __init__(self, cls):
        """ Creates a new NotInstantiableAbstractCaseClassException instance.

        :param cls: AbstractCaseClass that can not be instantiated
        :type cls: type
        """

        super(NotInstantiableAbstractCaseClassException, self).__init__(
            "Can not instantiate AbstractCaseClass %s" % (cls.__name__, ), cls)


class NoCaseToCaseInheritanceException(Exception):
    """ Represents an exception that is raised when the user tries to
    inherit from a CaseClass or AbstractCaseClass subclass. """

    def __init__(self, name):
        """ Creates a new NoCaseToCaseInheritanceException instance.

        :param name: Name of the class the user tried to create.
        :type name: str
        """

        super(NoCaseToCaseInheritanceException, self).__init__(
            "Unable to create class %s: " % (name, ) +
            "Case-to-case inheritance is prohibited. ")

        self.name = name


__all__ = ["AbstractCaseClass", "CaseClass", "InheritableCaseClass",
           "NotInstantiableClassException",
           "NotInstantiableAbstractCaseClassException",
           "NoCaseToCaseInheritanceException"]
