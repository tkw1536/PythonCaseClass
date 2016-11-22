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