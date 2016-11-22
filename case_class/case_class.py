"""
CaseClass implementation for the case_class module

Copyright (c) 2016 Tom Wiesing -- licensed under MIT, see LICENSE
"""

import inspect

from . import exceptions, clsutils, signature


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
            raise exceptions.NoCaseToCaseInheritanceException(name)

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
            raise exceptions.NotInstantiableAbstractCaseClassException(cls)

        # may not instantiate sub classes of _CaseClass
        if _CaseClass in cls.__bases__:
            raise exceptions.NotInstantiableClassException(
                "Cannot instantiate %s: " % (cls.__name__,) +
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
        key = clsutils.get_class_parameters(cls, *args, **kwargs)

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


@clsutils.add_metaclass(CaseClassMeta)
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

        # set the class name
        inst.__name = inst.__class__.__name__

        # get the init signature
        inst.__sig = clsutils.get_init_signature(inst.__class__)

        # and the arguments
        inst.__applied = inst.__sig(*args, **kwargs)

        # and return the instance
        return inst

    def __hash__(self):
        """ Returns a hash representing this case class.

        :rtype: int
        """

        return CaseClassMeta.get_hash(self)

    def copy(self, *args, **kwargs):
        """ Makes a copy of this CaseClass instance and exchanges the given
        values.

        :rtype: CaseClass
        """

        updated = self.case_params.signature(*args, **kwargs)
        return updated.call(self.__class__)

    @property
    def case_params(self):
        """ Returns the parameters originally given to this CaseClass.

        :rtype: CaseParameters
        """

        return CaseParameters(self.__applied)

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

    def __init__(self, sig):
        """ Creates a new CaseArguments() instance.

        :param sig: Applied Signature of the original init function.
        :type sig: signature.AppliedSignature
        """

        self.__sig = sig

        # super(CaseParameters, self).__init__(self.__params)

    def __getitem__(self, n):
        """ Returns a positional CaseClass parameter.

        :param n: Number of item to get.
        :type n: int
        :rtype: object
        """

        # TODO: Check into the numerical things

        return self.__sig[n]

    def __getattr__(self, name):
        """ Gets a parameter given to this CaseParameters instance by name.

        :param name: Name of parameter to get
        :type name: str
        """

        return self.__sig[name]

    @property
    def signature(self):
        """ Returns the applied Signature belonging to this CaseClasss.

        :rtype: signature.AppliedSignature
        """
        return self.__sig

    def __str__(self):
        """ Turns this CaseParameters instance into a string.

        :rtype: str
        """
        return str(self.__sig)


__all__ = ["AbstractCaseClass", "CaseClass", "InheritableCaseClass"]
