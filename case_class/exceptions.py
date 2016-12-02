"""
Exceptions for the case_class module

Copyright (c) 2016 Tom Wiesing -- licensed under MIT, see LICENSE
"""


class CaseClassException(Exception):
    """ Base Exception for all exceptions raised by the case_class module. """
    pass


#
# Instantiation of CaseClasses
#

class NotInstantiableClassException(CaseClassException):
    """ Exception that is raised when a class can not be instantiated. """

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


class NotInstantiableAbstractCaseClassException \
            (NotInstantiableClassException):
    """ Exception that is raised when an AbstractCaseClass is instantiated. """

    def __init__(self, cls):
        """ Creates a new NotInstantiableAbstractCaseClassException instance.

        :param cls: AbstractCaseClass that can not be instantiated
        :type cls: type
        """

        super(NotInstantiableAbstractCaseClassException, self).__init__(
            "Can not instantiate AbstractCaseClass %s" % (cls.__name__,), cls)


class NoCaseToCaseInheritanceException(Exception):
    """ Exception that is raised when the user tries to
    inherit from a CaseClass or AbstractCaseClass subclass. """

    def __init__(self, name):
        """ Creates a new NoCaseToCaseInheritanceException instance.

        :param name: Name of the class the user tried to create.
        :type name: str
        """

        super(NoCaseToCaseInheritanceException, self).__init__(
            "Unable to create class %s: " % (name,) +
            "Case-to-case inheritance is prohibited. ")

        self.name = name


#
# Signatures
#

class SignatureException(CaseClassException):
    """ Base class for all exceptions related to signatures. """
    pass


class MissingArgument(SignatureException):
    """ Exception indicating that the value for a given argument is not
    specefied fully. """

    def __init__(self, name):
        """ Creates a new NoSuchArgument instance.

        :param,name: Name of the argument that does not have a value.
        :type name. str
        """

        super(MissingArgument, self).__init__("MissingArgument: Missing " +
                                              "value for %s. " % (
                                                  name,))

        self.__name = name  #: str

    @property
    def name(self):
        """ The name of the argument that does not have a value.

        :rtype: str
        """

        return self.__name


class NoSuchArgument(SignatureException):
    """ Exception indicating that an argument does not exist. """

    def __init__(self, name):
        """ Creates a new NoSuchArgument instance.

        :param,name: Name of the argument that does not exist.
        :type name. str
        """

        super(NoSuchArgument, self).__init__("NoSuchArgument: No argument " +
                                             "%s exists. " % (name,))

        self.__name = name  #: str

    @property
    def name(self):
        """ The name of the argument that does not exist.

        :rtype: str
        """

        return self.__name


class NoDefaultValue(SignatureException):
    """ Exception indicating that an argument has no default value. """

    def __init__(self, name):
        """ Creates a new NoDefaultValue instance.

        :param,name: Name of the argument that has no default.
        :type name. str
        """

        super(NoDefaultValue, self).__init__("NoDefaultValue: Argument " +
                                             "%s has no default. " % (name,))

        self.__name = name  #: str

    @property
    def name(self):
        """ The name of the argument that has no associated default value.

        :rtype: str
        """

        return self.__name


class AppliedSignatureException(CaseClassException):
    """ Base class for all exceptions related to applied signatures. """
    pass


class TooManyArguments(AppliedSignatureException):
    """ Exception indicating that too many arguments were passed to a
    signature. """

    def __init__(self):
        """ Creates a new TooManyArguments instance. """

        super(TooManyArguments, self).__init__("TooManyArguments: Too many " +
                                               "arguments were passed to the" +
                                               " signature. ")


class TooManyKeyWordArguments(AppliedSignatureException):
    """ Exception indicating that too many arguments were passed to a
    signature. """

    def __init__(self):
        """ Creates a new TooManyKeyWordArguments instance. """

        super(TooManyKeyWordArguments, self).__init__(
            "TooManyKeyWordArguments: Too many " +
            "arguments were passed to the" +
            " signature. ")


class DoubleArgumentValue(AppliedSignatureException):
    """ Exception indicating that an argument was passed more than once.  """

    def __init__(self, name):
        """ Creates a new DoubleArgumentValue instance.

        :param name: Name of the argument that was passed more than once.
        :type name: str
        """

        super(DoubleArgumentValue, self).__init__(
            "DoubleArgumentValue: Argument %s was passed more " % (name,) +
            "than once. ")

        self.__name = name  #: str

    @property
    def name(self):
        """ The name of the argument that was passed more than once.

        :rtype: str
        """

        return self.__name


class ExtractorException(CaseClassException):
    """ Common base class related to all extractors. """
    pass


class ExtractorDoesNotMatch(ExtractorException):
    """ raised when an extractor does not match a certain pattern. """
    pass


__all__ = ["CaseClassException", "NotInstantiableClassException",
           "NotInstantiableAbstractCaseClassException",
           "NoCaseToCaseInheritanceException", "SignatureException",
           "MissingArgument", "NoSuchArgument", "NoDefaultValue",
           "AppliedSignatureException", "TooManyArguments",
           "TooManyKeyWordArguments", "DoubleArgumentValue"]
