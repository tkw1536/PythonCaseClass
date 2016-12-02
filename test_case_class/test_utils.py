"""
testing case_class.utils

Copyright (c) 2016 Tom Wiesing -- licensed under MIT, see LICENSE
"""

from unittest import TestCase

from case_class import utils


class TestUtils(TestCase):
    """ Tests the Utilities. """

    def test_exec_(self):
        """ Tests that the exec_ function can run code. """

        local_vars = {
            'x': 1
        }

        local_vars_after = {
            'x': 1,
            'y': 2
        }

        utils.exec_('y = x + 1', local_vars, local_vars)

        self.assertEqual(local_vars['x'], local_vars_after['x'], "kept x")
        self.assertEqual(local_vars['y'], local_vars_after['y'], "set y")

    def test_is_string(self):
        """ Tests that the is_string method works properly. """

        self.assertTrue(utils.is_string("hello world"), "normal string is a "
                                                        "string")
        self.assertTrue(utils.is_string('hello world'), "single char string "
                                                        "is a string")
        self.assertTrue(utils.is_string("""A docstring"""), "docstring is a "
                                                            "string")
        self.assertFalse(utils.is_string(1), "Number is not a string")
        self.assertFalse(utils.is_string(dict()), "Dictionary is not a string")

    def test_is_lambda(self):
        """ Tests that the is_lambda method works properly. """

        class C(object):
            def __call__(self):
                return False

        def f():
            return 1

        self.assertTrue(utils.is_lambda(lambda q:q), "Lambda function is a "
                                                     "lambda function")
        self.assertFalse(utils.is_lambda(f), "Normal function is not a lambda")
        self.assertFalse(utils.is_lambda(C), "Callable function is not a "
                                             "lambda")
