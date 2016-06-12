from six import add_metaclass


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
        if CaseClassBase in bases:
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

        # Define a new __init__ function that (1) makes sure the cc is
        # instantiated and (2) calls the old_init function.

        def __init__(self, *args, **kwargs):

            CaseClass.__case_class_init__(self, *args, **kwargs)

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

        if CaseClassBase in cls.__bases__:
            raise TypeError("Cannot instantiate %s: Classes inheriting "
                            "directly from CaseClassBase may not be "
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


class CaseClassBase(object):
    """ Internal base class for CaseClasses.  """
    pass


@add_metaclass(CaseClassMeta)
class CaseClass(CaseClassBase):
    """ Super-class used for all case classes. """

    def __case_class_init__(self, *args, **kwargs):
        """ Initialises case class parameters.

        :param args: Parameters for this CaseClass instance.
        :type args: list
        :param kwargs: Keyword Arguments for this CaseClass instance.
        :type kwargs: dict
        """

        # The name of this case class
        self.__name = self.__class__.__name__

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
    def case_args(self):
        """ Returns the arguments originally given to this CaseClass.

        :rtype: list
        """

        return list(self.__args)

    @property
    def case_kwargs(self):
        """ Returns the keyword arguments given to this CaseClass.

        :rtype: dict
        """

        return self.__kwargs

    def __repr__(self):
        """ Implements a representation for Case classes. This is given by the
        class name and the representation of all the parameters.

        :rtype: str
        """

        # string representations of the arguments and keyword arguments
        a_list = list(map(repr, self.case_args))
        kwarg_list = list(map(lambda p: "%s=%r" % p, self.case_kwargs.items()))

        # join them
        a_repr = ",".join(a_list+kwarg_list)

        # and put them after the name of the class
        return "%s[%s]" % (self.__name, a_repr)


@add_metaclass(AbstractCaseClassMeta)
class AbstractCaseClass(CaseClass, CaseClassBase):
    """ Represents a non-instatiable abstract case class. """

    pass


class InheritableCaseClass(CaseClass, CaseClassBase):
    """ Represent a caseClass that may be inherited from. """

    pass
