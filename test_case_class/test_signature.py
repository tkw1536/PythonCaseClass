"""
testing case_class.signature

Copyright (c) 2016 Tom Wiesing -- licensed under MIT, see LICENSE
"""

from unittest import TestCase

from case_class import signature, exceptions


class TestSignature(TestCase):
    """ Tests the SignatureClass. """

    def test___init__(self):
        """ Tests that the signature extraction works properly. """

        def f(a, b="b", *c, **d):
            pass

        s = signature.Signature(f)

        self.assertEqual(s.args, ["a", "b"], "Extracting arguments from " +
                         "a function")
        self.assertEqual(s.defaults, ["b"], "Extracting default arguments " +
                         "from a function. ")
        self.assertEqual(s.vararg, "c", "Extracting vararg from function. ")
        self.assertEqual(s.varkw, "d", "Extracting keyword vararg from "
                                       "function. ")

    def test_get_argument_type(self):
        """ Tests that the get_argument_type works properly. """

        def f(a, b="b", *c, **d):
            pass

        s = signature.Signature(f)

        self.assertEqual(s.get_argument_type("a"),
                         signature.Signature.ARGUMENT,
                         "getting normal argument type")

        self.assertEqual(s.get_argument_type("b"),
                         signature.Signature.ARGUMENT_WITH_DEFAULT,
                         "getting argument with default type")

        self.assertEqual(s.get_argument_type("c"),
                         signature.Signature.VARARG,
                         "getting vararg type")
        self.assertEqual(s.get_argument_type("d"),
                         signature.Signature.KEYWORD_VARARG,
                         "getting keyword vararg")

        self.assertRaises(exceptions.NoSuchArgument,
                          lambda: s.get_argument_type("e"))

    def test_get_default(self):
        """ Tests that the test_get_default works properly. """

        def f(a, b="b", *c, **d):
            pass

        s = signature.Signature(f)

        # check that normal values do not have a default
        self.assertRaises(exceptions.NoDefaultValue,
                          lambda: s.get_default("a"))

        self.assertEqual(s.get_default("b"), "b", "Getting default value of " +
                         "a normal argument. ")

        # check that VARARG has no default
        self.assertRaises(exceptions.NoDefaultValue,
                          lambda: s.get_default("c"))

        # check that the KWVARARG as no default
        self.assertRaises(exceptions.NoDefaultValue,
                          lambda: s.get_default("d"))

        # check that we raise NoSuchArgument for non-existing values
        self.assertRaises(exceptions.NoSuchArgument,
                          lambda: s.get_default("e"))

    def test___eq__(self):
        """ Tests that equality between signatures works properly. """

        def f(a, b=1, *c, **d):
            pass

        sF = signature.Signature(f)

        def g(a, b=1, *c, **d):
            pass

        sG = signature.Signature(g)

        def h(a, b=1):
            pass

        sH = signature.Signature(h)

        self.assertEqual(sF, sF, "Equality of a signature to itself")
        self.assertEqual(sF, sG, "Equality of two signatures")
        self.assertNotEqual(sF, sH, "Inequality of two signatures")

        self.assertEqual(sG, sF, "Equality of two signatures")
        self.assertEqual(sG, sG, "Equality of a signature to itself")
        self.assertNotEqual(sG, sH, "Inequality of two signatures")

        self.assertNotEqual(sH, sF, "Inequality of two signatures")
        self.assertNotEqual(sH, sG, "Inequality of two signatures")
        self.assertEqual(sH, sH, "Equality of a signature to itself")

    def test___iter__(self):
        """ Tests that the iterator works properly. """

        def f(a, b="b", *c, **d):
            pass

        s = signature.Signature(f)

        self.assertEqual(list(s), [
            ("a", signature.Signature.ARGUMENT, None),
            ("b", signature.Signature.ARGUMENT_WITH_DEFAULT, "b"),
            ("c", signature.Signature.VARARG, None),
            ("d", signature.Signature.KEYWORD_VARARG, None)
        ], "iterate over a function signature")

    def test___str__(self):
        """ Tests that the stringifying signatures works properly. """

        def f(a, b="b", *c, **d):
            pass

        s = signature.Signature(f)
        self.assertEqual(str(s), "a, b='b', *c, **d",
                         "turning Signature into a string")


class TestAppliedSignature(TestCase):
    """ Tests the AppliedSignatureClass. """

    def test_passnormal(self):
        """ Tests that normal passing of arguments works. """

        def f(a, b="b", *c, **d):
            pass

        s = signature.Signature(f)

        a = s(1, 2, 3, e=4)

        self.assertEqual(a["a"], 1, "pass normal argument")
        self.assertEqual(a["b"], 2, "pass default argument")
        self.assertEqual(a["c"], (3,), "pass vararg")
        self.assertEqual(a["d"], {"e": 4}, "pass kwvararg")

    def test_passmin(self):
        """ Tests that passing of non-needed arguments works. """

        def f(a, b="b", *c, **d):
            pass

        s = signature.Signature(f)

        a = s(1)

        self.assertEqual(a["a"], 1, "pass normal argument")
        self.assertEqual(a["b"], "b", "using default value")
        self.assertEqual(a["c"], tuple(), "pass vararg")
        self.assertEqual(a["d"], {}, "pass kwvararg")

    def test_passweird(self):
        """ Tests that weird passing of arguments works. """

        def f(a, b="b", *c, **d):
            pass

        s = signature.Signature(f)

        a = s(b=2, a=1)

        self.assertEqual(a["a"], 1, "pass normal argument")
        self.assertEqual(a["b"], 2, "using default value")
        self.assertEqual(a["c"], tuple(), "pass vararg")
        self.assertEqual(a["d"], {}, "pass kwvararg")

    def test_MissingArgument(self):
        """ Tests that you must supply all missing arguments. """

        def f(a):
            pass

        s = signature.Signature(f)

        self.assertRaises(exceptions.MissingArgument, lambda: s())

    def test_DoubleArgumentValue(self):
        """ Tests that arguments can only be passed once. """

        def f(a):
            pass

        s = signature.Signature(f)

        self.assertRaises(exceptions.DoubleArgumentValue, lambda: s(1, a=1))

    def test_TooManyArguments(self):
        """ Tests that we can not pass to many arguments. """

        def f(a):
            pass

        s = signature.Signature(f)

        self.assertRaises(exceptions.TooManyArguments, lambda: s(1, 2))

    def test_TooManyKeyWordArguments(self):
        """ Tests that we can not pass to many keyword arguments. """

        def f(a):
            pass

        s = signature.Signature(f)

        self.assertRaises(exceptions.TooManyKeyWordArguments,
                          lambda: s(a=1, b=2))

    def test___eq__(self):
        """ Tests that equality between applied Signatures works properly. """

        def f(a, b=1, *c, **d):
            pass

        s = signature.Signature(f)
        aF = s(1, 2, k=4)
        aG = s(b=2, a=1, k=4)
        aH = s(1, 2, 3)

        self.assertEqual(aF, aF, "Equality of an applied signature to itself")
        self.assertEqual(aF, aG, "Equality of two applied signatures")
        self.assertNotEqual(aF, aH, "Inequality of two applied signatures")

        self.assertEqual(aG, aF, "Equality of two applied signatures")
        self.assertEqual(aG, aG, "Equality of an applied signature to itself")
        self.assertNotEqual(aG, aH, "Inequality of two applied signatures")

        self.assertNotEqual(aH, aF, "Inequality of two applied signatures")
        self.assertNotEqual(aH, aG, "Inequality of two applied signatures")
        self.assertEqual(aH, aH, "Equality of an applied signature to itself")

    def test___call__(self):
        """ Tests that partially overwriting values in Applied Signatures works
        properly.
        """

        def f(a, b=None, *c, **d):
            pass

        s = signature.Signature(f)
        a1 = s(1, 2, 3, f=4)
        a2 = s('o', 't', 3, f=4)
        a3 = s(1, 't', 3, f=4)
        a4 = s(1, 2, 4, 5, 6, f=4)
        a5 = s(1, 2, 3, f=4, g=5)
        a6 = s(1, 2, 3, f=5, g=6)

        self.assertEqual(a1, a1(), 'applying a signature overwriting nothing')
        self.assertEqual(a1('o', 't'), a2, 'overwriting normal arguments')
        self.assertEqual(a1(b='t'), a3, 'overwriting defaulted arguments')
        self.assertEqual(a1(1, 2, 4, 5, 6), a4, 'overwriting VARARG')
        self.assertEqual(a1(g=5), a5, 'adding KEYWORDVARARG')
        self.assertEqual(a1(f=5, g=6), a6, 'overwriting KEYWORDVARARG')

    def test___str__(self):
        """ Tests that the stringifying applied works properly. """

        def f(a, b="b", *c, **d):
            pass

        s = signature.Signature(f)
        a = s("1", "2", "3", f="4")
        self.assertEqual(str(a), "'1', b='2', *c=('3',), **d={'f': '4'}",
                         "turning Applied Signature into a string")

    def call(self):
        """ Tests that one can call applied signatures. """

        def f(a, b="b", *c, **d):
            return {
                'a': a,
                'b': b,
                'c': c,
                'd': d
            }

        s = signature.Signature(f)

        aF = s(1, 2, k=4)
        bF = f(1, 2, k=4)

        self.assertEqual(aF.call(), bF, 'calling applied signature')

        aG = s(b=2, a=1, k=4)
        bG = f(b=2, a=1, k=4)

        self.assertEqual(aG.call(), bG, 'calling applied signature')

        aH = s(1, 2, 3)
        bH = f(1, 2, 3)

        self.assertEqual(aG.call(), bG, 'calling applied signature')


