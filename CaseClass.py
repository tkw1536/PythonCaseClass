"""
CaseClass.py - Scala-like CaseClasses for Python

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
"""

import inspect

#
# UTILITIES
#

class _Utilities(object):
    """ Object containing all ultity functions.  """

    ARGUMENT_POS = "pos"
    VAR_POS = "pvar"
    ARGUMENT_KW = "kw"
    VAR_KW = "kwvar"

    @staticmethod
    def get_signature(f):
        """ Extract a signature from a function.

        :param f: Function to extract signature from.
        :return: A pair of (arguments, mapping) as a list of arguments and ampping form names to finding the variables
        :rtype: list
        """

        # STEP 1: Inspect the function
        try:
            # try with get full argspec
            (pa, van, kwvan, pdef, kwonly, kwdef, annots) = inspect.getfullargspec(f)
        except AttributeError:
            # fallback to the regular one
            (pa, van, kwvan, pdef) = inspect.getargspec(f)
            annots = {}
            kwonly = {}
            kwdef = {}

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
            mapping[a] = (_Utilities.ARGUMENT_POS, i)

            if a in defaults:
                arg['type'] = _Utilities.ARGUMENT_KW
                arg['default'] = defaults[a]
            else:
                arg['type'] = _Utilities.ARGUMENT_POS
                nkwvar.append(a)

            if a in annots:
                arg['annot'] = annots[a]

            arguments.append(arg)

        # VARARG
        if van is not None:
            arg = {'name': van, 'type': _Utilities.VAR_POS}
            mapping[van] = (_Utilities.VAR_POS, len(pa))

            if van in annots:
                arg['annot'] = annots[van]

            arguments.append(arg)

        # Keyword-only
        for a in kwonly:
            arg = {'name': a, 'type': _Utilities.ARGUMENT_KW,
                   'default': defaults[a]}

            mapping[a] = (_Utilities.ARGUMENT_KW, a)
            nkwvar.append(a)

            if a in annots:
                arg['annot'] = annots[a]

            arguments.append(arg)

        # KW VARAGR
        if kwvan is not None:
            arg = {'name': kwvan, 'type': _Utilities.VAR_KW}
            mapping[van] = (_Utilities.VAR_KW, nkwvar)

            if kwvan in annots:
                arg['annot'] = annots[kwvan]

            arguments.append(arg)

        # and return the arguments
        return arguments, mapping

    @staticmethod
    def get_argument_by_name(name, mapping, args, kwargs):
        """ Gets a function argument by name. """

        # if we do not have it, throw an error
        if not name in mapping:
            raise AttributeError

        # look up where it is
        (tp, spec) = mapping[name]

        # positional argument ==> return it
        if tp == _Utilities.ARGUMENT_POS:
            return args[spec]

        # VARARG ==> take the ones that are not others
        elif tp == _Utilities.VAR_POS:
            return args[spec:]

        # KEYWORD_ARGUMENTS ==> return it.
        elif tp == _Utilities.ARGUMENT_KW:
            return kwargs[spec]

        # KWVARARG ==> remove all the others.
        elif tp == _Utilities.VAR_KW:
            kwargs = kwargs.copy()

            for p in spec:
                kwargs.pop(p)

            return kwargs

    @staticmethod
    def add_metaclass(meta):
        """Class decorator for creating a class with a metaclass. Adapted from the
        six library which is licensed as follows:

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

        # skip the CaseClass and AbstractCaseClass
        if _CaseClass in bases:
            return super(CaseClassMeta, mcs).__new__(mcs, name, bases, attrs)

        # no case-to-case inheritance
        if CaseClassMeta.inherits_from_caseclass(bases):
            # if you know what you are doing, use InheritableCaseClass instead.
            raise ValueError("Cannot create class %s: Case-to-case inheritance"
                             " is prohibited. " % name)

        # store the reference to the old __init__ class in a variable old_init

        # if we have an __oldinit__ this is perfectly fine
        if "__init__" in attrs:
            old_init = attrs["__init__"]

        # else we shall just call the super class manually we need to call the
        # super() __init__

        else:
            def old_init(self, *args, **kwargs):
                super(cls, self).__init__(*args, **kwargs)

        # Extract the old signature
        (_, sigmap) = _Utilities.get_signature(old_init)


        # Define a new __init__ function that (1) makes sure the cc is
        # instantiated and (2) calls the old_init function.
        def __init__(self, *args, **kwargs):
            CaseClass.__case_class_init__(self, sigmap, *args, **kwargs)

            return old_init(self, *args, **kwargs)

        # set that as the __init__
        attrs["__init__"] = __init__

        # create the class
        cls = super(CaseClassMeta, mcs).__new__(mcs, name, bases, attrs)

        # and return it
        return cls

    def __call__(cls, *args, **kwargs):
        """ Creates a new CaseClass() instance.

        :param args: Arguments to this CaseClass instance.
        :type args: list

        :param kwargs: Keyword arguments to this CaseClass instance.
        :type kwargs: dict

        :rtype: CaseClass
        """

        if AbstractCaseClass in cls.__bases__:
            raise TypeError("Cannot instantiate AbstractCaseClass %s"
                            % (cls.__name__, ))

        if _CaseClass in cls.__bases__:
            raise TypeError("Cannot instantiate %s: Classes inheriting "
                            "directly from _CaseClass may not be "
                            "instantiated. " % cls.__name__)

        # make sure we have the dictionary
        if cls not in CaseClassMeta.instance_keys:
            CaseClassMeta.instance_keys[cls] = []
            CaseClassMeta.instance_values[cls] = {}

        # Extract the instances for this class
        ckey = CaseClassMeta.instance_keys[cls]
        cval = CaseClassMeta.instance_values[cls]

        # key we will use for this instance.
        key = (args, kwargs)

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
            item = (item, )

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
    def inherits_from_caseclass(bases):
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


class AbstractCaseClassMeta(CaseClassMeta):
    """ Represents an abstract case class that can not be instantiated. """

    def __call__(cls, *args, **kwargs):
        """ Creates a new CaseClass() instance.
        :param args: Arguments to this CaseClass instance.
        :type args: list
        :param kwargs: Keyword arguments to this CaseClass instance.
        :type kwargs: dict
        :rtype: CaseClass
        """

        if AbstractCaseClass in cls.__bases__:
            raise TypeError("Can not instantiate AbstractCaseClass %s"
                            % cls.__name__)

        return super(AbstractCaseClassMeta, cls).__call__(*args, **kwargs)


class _CaseClass(object):
    """ A class used as base for all CaseClasses"""

    pass


#
# Actual CaseClass
#

@_Utilities.add_metaclass(CaseClassMeta)
class CaseClass(_CaseClass):
    """ Represents a normal CaseClass. """

    def __case_class_init__(self, sigmap, *args, **kwargs):
        """ Initialises case class parameters.

        :param sigmap: Signature of the original __init__ function
        :type sigmap: dict

        :param args: Parameters for this CaseClass instance.
        :type args: list

        :param kwargs: Keyword Arguments for this CaseClass instance.
        :type kwargs: dict
        """

        # Name of the class
        self.__name = self.__class__.__name__

        # The signature of the original function
        self.__sigmap = sigmap

        # The arguments given to this case class
        self.__args = args

        # The keyword arguments given to this case class
        self.__kwargs = kwargs

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

        return CaseParameters(self.__sigmap, self.__args, self.__kwargs)

    def __repr__(self):
        """ Implements a representation for Case classes. This is given by the
        class name and the representation of all the parameters.

        :rtype: str
        """

        # string representations of the arguments and keyword arguments
        a_list = list(map(repr, self.case_params))
        kwarg_list = list(map(lambda p: "%s=%r" % p, self.case_params.items()))

        # join them
        a_repr = ",".join(a_list+kwarg_list)

        # and put them after the name of the class
        return "%s[%s]" % (self.__name, a_repr)


@_Utilities.add_metaclass(AbstractCaseClassMeta)
class AbstractCaseClass(CaseClass, _CaseClass):
    """ Represents a non-instatiable abstract case class. """

    pass


class InheritableCaseClass(CaseClass, _CaseClass):
    """ Represent a caseClass that may be inherited from. """

    pass


#
# ACTUAL CASECLASSES for the arguments
#
class CaseParameters(CaseClass, dict):
    """ Represents arguments given to a CaseClass. """

    def __init__(self, sigmap, args, kwargs):
        """ Creates a new CaseArguments() instance.

        :param sigmap: Signature mapping
        :type sigmap: dict

        :param args: Arguments to wrap
        :type args: list

        :param kwargs: Keyword Arguments to wrap.
        :type kwargs: dict
        """
        super(CaseParameters, self).__init__(kwargs)

        self.__sigmap = sigmap
        self.__args = list(args)
        self.__kwargs = kwargs

        super(CaseParameters, self).__init__()

    def __getitem__(self, item):
        return self.__args[item]

    def __len__(self):
        return len(self.__args)

    def __iter__(self):
        for a in self.__args:
            yield a

    def __getattr__(self, item):
        return _Utilities.get_argument_by_name(item, self.__sigmap,
                                               [None] + self.__args,
                                               self.__kwargs)
