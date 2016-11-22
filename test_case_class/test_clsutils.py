"""
testing case_class.clsutils

Copyright (c) 2016 Tom Wiesing -- licensed under MIT, see LICENSE
"""

from unittest import TestCase

from case_class import clsutils
from case_class import signature


class TestUtils(TestCase):
    """ Tests the Utilities. """

    def test_get_method(self):
        """ Tests that the get_method function can get methods. """

        class Test(object):
            def f(self):
                pass

        class Test2(Test):
            pass

        self.assertTrue(
            clsutils.get_method('f', Test2.__dict__, Test2.__bases__) is
            Test.__dict__['f'], 'get method of superclass')

        self.assertTrue(
            clsutils.get_method('f', Test.__dict__, Test.__bases__) is
            Test.__dict__['f'], 'get method of class')

    def test_get_init_signature(self):
        """ Tests if get_init_signature works as expected. """

        class Foo(object):
            pass

        class Bar(object):
            def __init__(self, x):
                pass

        class Baz(Bar):
            pass

        # Signature of the bar_init function
        def bar_init(x):
            pass

        sBar = signature.Signature(bar_init)

        # Signature of the empty signature
        def obj_init():
            pass

        sObj = signature.Signature(obj_init)

        self.assertEqual(clsutils.get_init_signature(Bar), sBar,
                         "Signature of non-inheriting class")

        self.assertEqual(clsutils.get_init_signature(Baz), sBar,
                         "Signature of inherited class")

        self.assertEqual(clsutils.get_init_signature(Foo), sObj,
                         "Signature of object-inheriting class")

    def test_get_class_parameters(self):
        """ Test if get_class_parameters works as expected. """

        class Foo(object):
            def __init__(self, key, value=None):
                pass

        self.assertEqual(clsutils.get_class_parameters(Foo, 1, 2),
                         {'key': 1, 'value': 2},
                         'provide kw as positional')
        self.assertEqual(clsutils.get_class_parameters(Foo, 1),
                         {'key': 1, 'value': None},
                         'provide no kw')
        self.assertEqual(clsutils.get_class_parameters(Foo, value=1, key=2),
                         {'key': 2, 'value': 1},
                         'provide positional as kw')
