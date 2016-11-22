"""
Class utility functions for the case_class module.

Copyright (c) 2016 Tom Wiesing -- licensed under MIT, see LICENSE
"""

from . import signature


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
        sub_method = get_method(name, b.__dict__, b.__bases__)

        if sub_method is not None:
            return sub_method

    # else return None
    return None


def get_init_signature(cls):
    """ Gets the signature of an init function of a class.

    :param cls: Class to get init signature of.
    :type cls: type

    :rtype: signature.Signature
    """

    # get the init method
    init_method = get_method("__init__", cls.__dict__, cls.__bases__)

    # HACK: Do not allow object.__init
    if init_method is object.__init__:
        def init_method(self):
            return None

    return signature.Signature(init_method, skip_first_argument=True)


def get_class_parameters(cls, *args, **kwargs):
    """ Gets a normalised version of parameters passed to a class.

    :param cls: Class
    :type cls: type

    :rtype: dict
    """

    # Get the init signature
    s = get_init_signature(cls)

    # apply it to some arguments
    a = s(*args, **kwargs)

    # and normalise.
    return a.arguments()


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


__all__ = ["exec_", "get_method", "get_init_signature", "get_class_parameters",
           "add_metaclass"]
