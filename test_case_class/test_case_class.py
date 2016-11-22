"""
testing case_class.case_class

Copyright (c) 2016 Tom Wiesing -- licensed under MIT, see LICENSE
"""

from unittest import main, TestCase

from case_class import case_class
from case_class import exceptions


class TestCaseClass(TestCase):
    """ Tests for the CaseClass class. """

    def test_no_direct(self):
        """ Tests that the CaseClass class can not be
        instantiated directly. """

        self.assertRaises(exceptions.NotInstantiableClassException,
                          case_class.CaseClass)

    def test___init__(self):
        """ Tests that CaseClass subclasses can be instantiated. """

        class Test(case_class.CaseClass):
            pass

        class MoreTest(case_class.CaseClass):
            def __init__(self, a, b, c):
                pass

        self.assertFalse(Test() is None, 'instantiate zero-argument CaseClass')
        self.assertFalse(MoreTest(1, 2, 3) is None, 'instantiate CaseClass '
                                                    'with arguments')

    def test_copy(self):
        """ Tests that the copy() method works properly. """

        class Foo(case_class.CaseClass):
            def __init__(self, x, y=1, *args, **kwargs):
                pass

        instance1 = Foo(1, 2, 4, key='value')

        instance2 = Foo(5, 2, 4, key='value')
        self.assertEqual(instance1.copy(x=5), instance2,
                         'setting positional argument')

        instance3 = Foo(1, 5, 4, key='value')
        self.assertEqual(instance1.copy(y=5), instance3,
                         'setting positional argument with default')

        instance4 = Foo(1, 2, 4, 5, 6, 7, key='value')
        self.assertEqual(instance1.copy(1, 2, 4, 5, 6, 7), instance4,
                         'setting vararg')

        instance5 = Foo(1, 2, 4, key='other')
        self.assertEqual(instance1.copy(key='other'), instance5,
                         'setting keyword vararg')

        instance6 = Foo(1, 2, 4, key='value', unknown='dummy')
        self.assertEqual(instance1.copy(unknown='dummy'), instance6,
                         'setting unknown keyword arg')

    def test___repr__(self):
        """ Tests that repr() calls work as expected. """

        class Test(case_class.CaseClass):
            def __init__(self, x, y=1, *args, **kwargs):
                pass

        inst = Test(1, 2, key='value')

        self.assertEqual(repr(inst),
                         "Test(1, y=2, *args=(), **kwargs={'key': 'value'})",
                         'representation of a CaseClass')

        class Singleton(case_class.CaseClass):
            pass

        s = Singleton()

        self.assertEqual(repr(s), 'Singleton()',
                         'representation of a singleton')

    def test_reference(self):
        """ Tests that CaseClass instances are referentially equal when
        expected. """

        class Test(case_class.CaseClass):
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

        class Test(case_class.CaseClass):
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
            class Test(case_class.CaseClass):
                pass

            class Failure(Test):
                pass

        self.assertRaises(exceptions.NoCaseToCaseInheritanceException, code)


class TestAbstractCaseClass(TestCase):
    """ Tests for the AbstractCaseClass class. """

    def test_no_direct(self):
        """ Tests that the AbstractCaseClass class can not be
        instantiated directly. """

        self.assertRaises(exceptions.NotInstantiableClassException,
                          case_class.AbstractCaseClass)

    def test___init__(self):
        """ Tests that AbstractCaseClass instances can not be instantiated. """

        def code():
            class Tree(case_class.AbstractCaseClass):
                def __init__(self, value, *children):
                    self.value = value
                    self.children = children

            Tree(1, 2, 3)

        self.assertRaises(exceptions.NotInstantiableAbstractCaseClassException,
                          code)

    def test_inheritance(self):
        """ Tests that AbstractCaseClass subclasses can be instantiated. """

        class Tree(case_class.AbstractCaseClass):
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

        self.assertRaises(exceptions.NotInstantiableClassException,
                          case_class.InheritableCaseClass)

    def test___init__(self):
        """ Tests that InheritableCaseClass instances can be instantiated. """

        class Tree(case_class.InheritableCaseClass):
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

        class Tree(case_class.InheritableCaseClass):
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

        class Foo(case_class.AbstractCaseClass):
            pass

        class Bar(Foo):
            pass

        class Baz(case_class.AbstractCaseClass):
            def __init__(self):
                self.test_p1 = True

        class Xyz(Foo, Baz):
            def __init__(self):
                super(Xyz, self).__init__()
                self.test_p2 = True

        xyz = Xyz()

        self.assertTrue(xyz.test_p1 and xyz.test_p2,
                        "multiple-inheritance works with super()")

    def test_default_argument(self):
        """ Tests that we can have optional constructor
        arguments within constructors. """

        class Foo(case_class.CaseClass):
            def __init__(self, key, example=None):
                pass

        self.assertEqual(Foo(0), Foo(0, None),
                         "it is possible to omit default values")

        self.assertEqual(Foo(example=None, key=1), Foo(1),
                         "it is possible to send default values with key names")


if __name__ == '__main__':
    main()
