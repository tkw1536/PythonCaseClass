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
"""

from unittest import main, TestCase

from case_class import _Utilities, CaseClass, AbstractCaseClass, \
    InheritableCaseClass, NotInstantiableAbstractCaseClassException, \
    NotInstantiableClassException, NoCaseToCaseInheritanceException


class TestUtilities(TestCase):
    """ Tests for the _Utilities class. """

    sample_signature = (
        [
            {'name': 'x', 'type': _Utilities.ARGUMENT_POS},
            {'default': 1, 'name': 'y', 'type': _Utilities.ARGUMENT_KW},
            {'name': 'args', 'type': _Utilities.VAR_POS},
            {'name': 'kwargs', 'type': _Utilities.VAR_KW}
        ],
        {
            'kwargs': (_Utilities.VAR_KW, ['x', 'y'], None),
            'args': (_Utilities.VAR_POS, 2, None),
            'x': (_Utilities.ARGUMENT_POS, 0, None),
            'y': (_Utilities.ARGUMENT_POS, 1, 1)
        }
    )

    empty_signature = (
        [
            {'name': 'self', 'type': _Utilities.ARGUMENT_POS}
        ],
        {
            'self': (_Utilities.ARGUMENT_POS, 0, None),
        }
    )

    sample_const_signature = (
        [
            {'name': 'self', 'type': _Utilities.ARGUMENT_POS},
            {'name': 'x', 'type': _Utilities.ARGUMENT_POS}
        ],
        {
            'self': (_Utilities.ARGUMENT_POS, 0, None),
            'x': (_Utilities.ARGUMENT_POS, 1, None)
        }
    )

    def test_get_signature(self):
        """ Tests that the get_signature function can extract signatures. """

        def f(x, y=1, *args, **kwargs):
            pass

        self.assertEqual(_Utilities.get_signature(f),
                         TestUtilities.sample_signature,
                         "extracting signature from a function")

    def test_get_init_signature(self):
        """ Tests if get_init_signature works as expected. """

        class Foo(object):
            pass

        class Bar(object):
            def __init__(self, x):
                pass

        class Baz(Bar):
            pass

        self.assertEqual(_Utilities.get_init_signature(Baz),
                         TestUtilities.sample_const_signature)

        self.assertEqual(_Utilities.get_init_signature(Foo),
                         TestUtilities.empty_signature)

        self.assertEqual(_Utilities.get_init_signature(Bar),
                         TestUtilities.sample_const_signature)

    def test_get_class_parameters(self):
        """ Test if get_class_parameters works as expected. """

        class Foo(object):
            def __init__(self, key, value = None):
                pass

        self.assertEqual(_Utilities.get_class_parameters(Foo, 10, 10),
                         ((None, 10), {'value': 10}),
                         'provide kw as positional')
        self.assertEqual(_Utilities.get_class_parameters(Foo, 10),
                         ((None, 10), {'value': None}),
                         'provide no kw')
        self.assertEqual(_Utilities.get_class_parameters(Foo, value=10, key=10),
                         ((None, 10), {'value': 10}),
                         'provide positional as kw')


    def test_with_signature(self):
        """ Tests that the with_signature function can enforce signatures. """

        @_Utilities.with_signature('test', TestUtilities.sample_signature)
        def f(*args, **kwargs):
            pass

        self.assertEqual(f.__name__, 'test', 'set function name')
        self.assertEqual(_Utilities.get_signature(f),
                         TestUtilities.sample_signature,
                         'set function signature')

    def test_get_argument_by_name(self):
        """ Tests that the get_argument_by_name function can get arguments. """

        # Uses the signature of f from above

        # f(x, y = 2, z = 3)
        args = [1]
        kwargs = {'y': 2, 'z': 3}

        self.assertEqual(_Utilities.get_argument_by_name(
            'x', TestUtilities.sample_signature[1], args, kwargs), 1,
            'get positional argument')
        self.assertEqual(_Utilities.get_argument_by_name(
            'y', TestUtilities.sample_signature[1], args, kwargs), 2,
            'get keyword argument')
        self.assertEqual(_Utilities.get_argument_by_name(
            'kwargs', TestUtilities.sample_signature[1], args, kwargs),
            {'z': 3}, 'get kw var')

        # f(1, 2, 3, 4)
        args = [1, 2, 3, 4]
        kwargs = {}

        self.assertEqual(_Utilities.get_argument_by_name(
            'args', TestUtilities.sample_signature[1], args, kwargs), [3, 4],
            'get positional var')

    def test_exec_(self):
        """ Tests that the exec_ function can run code. """

        local_vars = {
            'x': 1
        }

        local_vars_after = {
            'x': 1,
            'y': 2
        }

        _Utilities.exec_('y = x + 1', local_vars, local_vars)

        self.assertEqual(local_vars['x'], local_vars_after['x'], "kept x")
        self.assertEqual(local_vars['y'], local_vars_after['y'], "set y")

    def test_get_method(self):
        """ Tests that the get_method function can get methods. """

        class Test(object):
            def f(self):
                pass

        class Test2(Test):
            pass

        self.assertTrue(
            _Utilities.get_method('f', Test2.__dict__, Test2.__bases__) is
            Test.__dict__['f'], 'get method of superclass')

        self.assertTrue(
            _Utilities.get_method('f', Test.__dict__, Test.__bases__) is
            Test.__dict__['f'], 'get method of class')


class TestCaseClass(TestCase):
    """ Tests for the CaseClass class. """

    def test_no_direct(self):
        """ Tests that the CaseClass class can not be
        instantiated directly. """

        self.assertRaises(NotInstantiableClassException, CaseClass)

    def test___init__(self):
        """ Tests that CaseClass subclasses can be instantiated. """

        class Test(CaseClass):
            pass

        class MoreTest(CaseClass):
            def __init__(self, a, b, c):
                pass

        self.assertFalse(Test() is None, 'instantiate zero-argument CaseClass')
        self.assertFalse(MoreTest(1, 2, 3) is None, 'instantiate CaseClass '
                                                    'with arguments')

    def test___repr__(self):
        """ Tests that repr() calls work as expected. """

        class Test(CaseClass):
            def __init__(self, x, y=1, *args, **kwargs):
                pass

        inst = Test(1, 2, key='value')

        self.assertEqual(repr(inst),
                         "Test(1, y=2, *args=(), **kwargs={'key': 'value'})",
                         'representation of a CaseClass')

        class Singleton(CaseClass):
            pass

        s = Singleton()

        self.assertEqual(repr(s), 'Singleton()',
                         'representation of a singleton')

    def test_reference(self):
        """ Tests that CaseClass instances are referentially equal when
        expected. """

        class Test(CaseClass):
            def __init__(self, x):
                pass

        inst_one_a = Test(1)
        inst_one_b = Test(1)
        inst_two = Test(2)

        self.assertTrue(inst_one_a is inst_one_b, 'referential equality')
        self.assertTrue(inst_one_b is not inst_two, 'referential inequality')

    def test___eq__(self):
        """ Tests that CaseClass instances are equal when
        expected. """

        class Test(CaseClass):
            def __init__(self, x):
                pass

        inst_one_a = Test(1)
        inst_one_b = Test(1)
        inst_two = Test(2)

        self.assertEqual(inst_one_a, inst_one_b, 'normal equality')
        self.assertNotEqual(inst_one_b, inst_two, 'normal inequality')

    def test_no_inheritance(self):
        """ Tests that case-to-case inheritance is disabled by default. """

        def code():
            class Test(CaseClass):
                pass

            class Failure(Test):
                pass

        self.assertRaises(NoCaseToCaseInheritanceException, code)


class TestAbstractCaseClass(TestCase):
    """ Tests for the AbstractCaseClass class. """

    def test_no_direct(self):
        """ Tests that the AbstractCaseClass class can not be
        instantiated directly. """

        self.assertRaises(NotInstantiableClassException, AbstractCaseClass)

    def test___init__(self):
        """ Tests that AbstractCaseClass instances can not be instantiated. """

        def code():
            class Tree(AbstractCaseClass):
                def __init__(self, value, *children):
                    self.value = value
                    self.children = children

            Tree(1, 2, 3)

        self.assertRaises(NotInstantiableAbstractCaseClassException, code)

    def test_inheritance(self):
        """ Tests that AbstractCaseClass subclasses can be instantiated. """

        class Tree(AbstractCaseClass):
            def __init__(self, value, *children):
                self.value = value
                self.children = children

        class InternalNode(Tree):
            pass

        class LeafNode(Tree):
            def __init__(self, value):
                super(LeafNode, self).__init__(value)

        inst = InternalNode(1, LeafNode(1), LeafNode(2), LeafNode(3))
        self.assertEqual(repr(inst),
                         'InternalNode(1, *children=(LeafNode(1), LeafNode(2), '
                         'LeafNode(3)))', 'instantiating subclass of '
                                          'AbstractCaseClass')


class TestInheritableCaseClass(TestCase):
    """ Tests for the InheritableCaseClass class. """

    def test_no_direct(self):
        """ Tests that the InheritableCaseClass class can not be
            instantiated directly. """

        self.assertRaises(NotInstantiableClassException, InheritableCaseClass)

    def test___init__(self):
        """ Tests that InheritableCaseClass instances can be instantiated. """

        class Tree(InheritableCaseClass):
            def __init__(self, value, *children):
                self.value = value
                self.children = children

        inst = Tree(1)
        self.assertEqual(
            repr(inst),
            'Tree(1, *children=())',
            'instantiating InheritableCaseClass')

    def test_inheritance(self):
        """ Tests that InheritableCaseClass subclasses can be instantiated. """

        class Tree(InheritableCaseClass):
            def __init__(self, value, *children):
                self.value = value
                self.children = children

        class InternalNode(Tree):
            pass

        class LeafNode(Tree):
            def __init__(self, value):
                super(LeafNode, self).__init__(value)

        inst = InternalNode(1, LeafNode(1), LeafNode(2), LeafNode(3))
        self.assertEqual(repr(inst),
                         'InternalNode(1, *children=(LeafNode(1), LeafNode(2), '
                         'LeafNode(3)))', 'instantiating subclass of '
                                          'InheritableCaseClass')

    def test_multiple_inheritance(self):
        """ Tests that Multiple Inheritance works as expected. """

        class Foo(AbstractCaseClass):
            pass

        class Bar(Foo):
            pass

        class Baz(AbstractCaseClass):
            def __init__(self):
                self.test_p1 = True

        class Xyz(Foo, Baz):
            def __init__(self):
                super(Xyz, self).__init__()
                print(self)
                self.test_p2 = True

        xyz = Xyz()

        self.assertTrue(xyz.test_p1 and xyz.test_p2,
                        "multiple-inheritance works with super()")

    def test_default_argument(self):
        """ Tests that we can have optional constructor
        arguments within constructors. """

        class Foo(CaseClass):
            def __init__(self, key, example=None):
                pass

        self.assertEqual(Foo(0), Foo(0, None),
                         "it is possible to omit default values")

        self.assertEqual(Foo(example=None, key=1), Foo(1),
                         "it is possible to send default values with key names")


if __name__ == '__main__':
    main()
