"""
Signature related functions for the case_class module

Copyright (c) 2016 Tom Wiesing -- licensed under MIT, see LICENSE
"""

import inspect

from . import exceptions, utils


class Signature(object):
    """ An object that represents the signature of a callable object. """

    def __init__(self, cobj, skip_first_argument=False):
        """ Creates a new Signature object.

        :param cobj: Callable object to get signature of.
        :type cobj: callable

        :param skip_first_argument: Optional. If set to True, skips the first
        argument of the function. Intended for use with functions that take self.
        :type skip_first_argument: boolean

        """

        self.__callable = cobj

        # STEP 1: Inspect the function
        try:
            # try with get full argspec
            (pa, van, kwvan, pdef, kwonly, kwdef, annots) \
                = inspect.getfullargspec(cobj)

        # HACK HACK HACK
        # work around <slot_wrapper> objects by giving a sensible defaults
        except TypeError:
            (pa, van, kwvan, pdef, kwonly, kwdef, annots) = (
                ['self'],
                None,
                None,
                [],
                {},
                {},
                {}
            )

        # in case there is no getfullargspec
        except AttributeError:

            try:
                # try the regular one
                (pa, van, kwvan, pdef) = inspect.getargspec(cobj)
                annots = {}
                kwonly = {}
                kwdef = {}

            # HACK HACK HACK
            # work around <slot_wrapper> objects by giving a sensible defaults
            except TypeError:
                (pa, van, kwvan, pdef, kwonly, kwdef, annots) = (
                    ['self'],
                    None,
                    None,
                    [],
                    {},
                    {},
                    {}
                )

        self.__args = pa[
                      1:] if skip_first_argument else pa  # a list of the argument names

        self.__vararg = van  # *arg name
        self.__varkw = kwvan  # **kwargs name

        self.__defaults = pdef if pdef is not None else []  # default values of the keyword arguments

        self.__kwonlyargs = kwonly if kwonly is not None else []  # names of keyword-only arguments
        self.__kwonlydefaults = kwdef if kwdef is not None else {}  # keyword-only arguments defaults

        self.__annots = annots

    @staticmethod
    def apply(f, *args, **kwargs):
        """ Shortcut for signature.Signature(f, *args, **kwargs).

        :param f: Wrapped callable to get signature of.
        :type f:
        """

        return Signature(f)(*args, **kwargs)

    @property
    def callable(self):
        """ Returns the callacble that this signature comes from. """
        return self.__callable

    @property
    def args(self):
        """ A list of argument names of this Signature.

        :rtype: list
        """
        return list(self.__args)


    @property
    def vararg(self):
        """ The name of the *args argument or None.

        :rtype: str
        """
        return self.__vararg

    @property
    def varkw(self):
        """ The name of the **kwarfs argument or None.

        :rtype str:
        """
        return self.__varkw

    @property
    def defaults(self):
        """ A list of default arguments. If shorter than args, the defaults are
        located at the back.
        """

        return list(self.__defaults)

    @property
    def kwonlyargs(self):
        """ A list of keyword only arguments.

        :rtype list:
        """

        return list(self.__kwonlyargs)

    @property
    def kwonlydefaults(self):
        """ A dict representing the default vcalues of the keyword only arguments.

         :rtype dict.
         """
        return dict(self.__kwonlydefaults)

    def annots(self):
        """ A dict representing the annotations of this function.

        :rtype: dict
        """

        return dict(self.__annots)

    # TODO: Document these

    ARGUMENT = 0
    ARGUMENT_WITH_DEFAULT = 1
    VARARG = 2
    KEYWORD_VARARG = 3
    KEYWORD_ONLY = 4

    def get_argument_type(self, name):
        """ Gets the type of an argument by name. If the argument does not exist,
        raises NoSuchArgument.

        :raises: exceptions.NoSuchArgument

        :return: One of Signature.ARGUMENT, Signature.ARGUMENT_WITH_DEFAULT,
        Signature.VARARG, Signature.KEYWORD_VARARG or Signature.KEYWORD_ONLY.
        :rtype int:
        """

        try:

            # try to find the index of the argument.
            arg_index = self.args.index(name)

            # check if the argument has a default
            if len(self.args) - arg_index > len(self.defaults):
                return Signature.ARGUMENT
            # otherwise it is a normal argument.
            else:
                return Signature.ARGUMENT_WITH_DEFAULT
        except ValueError:
            pass

        if name == self.vararg:
            return Signature.VARARG

        if name == self.varkw:
            return Signature.KEYWORD_VARARG

        if name in self.kwonlyargs:
            return Signature.KEYWORD_ONLY

        raise exceptions.NoSuchArgument(name)

    def __iter__(self):
        """ Iterates over the arguments in this function signature in the
        order they were specefied.
        Each element is a triple (name, tp, d) where
            - name is a string giving the name of the argument,
            - tp is the type of the argument and is one of Signature.ARGUMENT,
                Signature.ARGUMENT_WITH_DEFAULT, Signature.VARARG,
                Signature.KEYWORD_VARARG or Signature.KEYWORD_ONLY
            - d is the default of the argument (or None if not applicable)
        """

        # 1. Iterate over the argument type.

        # index before which we have no defaults.
        arg_cutoff = len(self.args) - len(self.defaults)

        for (i, name) in enumerate(self.args):
            if i < arg_cutoff:
                yield (name, Signature.ARGUMENT, None)
            else:
                yield (name, Signature.ARGUMENT_WITH_DEFAULT,
                       self.defaults[i - arg_cutoff])

        # 2. The vararg
        if self.vararg is not None:
            yield (self.vararg, Signature.VARARG, None)

        # 3. The keyword only arguments
        for name in self.kwonlyargs:
            yield (name, Signature.KEYWORD_ONLY, self.kwonlydefaults[name])

        # 4. the kwargs
        if self.varkw is not None:
            yield (self.varkw, Signature.KEYWORD_VARARG, None)

    def get_default(self, name):
        """ Returns the default values of an argument.
        Raises NoSuchArgument if the argument with the given value does not
        exist or NoDefaultValue if the argument exists and has not default.

        :raise: exceptions.NoSuchArgument
        :raise: exceptions.NoDefaultValue

        :param name: Name of the argument to get default of.
        :type name. str

        :rtype: object
        """

        # get the argument type (or raise Exception)
        tp = self.get_argument_type(name)

        # get default of a normal argument
        if tp == Signature.ARGUMENT_WITH_DEFAULT:
            idx = self.args.index(name)
            return self.defaults[len(self.args) - idx - 1]

        # return a keyword argument
        elif tp == Signature.KEYWORD_ONLY:
            return self.kwonlydefaults[name]

        # everything else has no default value.
        raise exceptions.NoDefaultValue(name)

    def __call__(self, *args, **kwargs):
        """ Calls an object with the signature.

        :param args: Arguments to pass to the signature.
        :type args: list

        :param kwargs: Keyword arguments to pass to the signature.
        :type kwargs: dict

        :rtype: AppliedSignature
        """

        return AppliedSignature(self, args, kwargs)

    def fake(self, name):
        """ Decorator that fakes this signature for a given function.

        :param name: Name to give to the new function.
        :type name: str
        """

        # the map of defaults
        defaults = {}
        nprefix = name

        # create the default values by iterating
        for (n, t, d) in self:
            nprefix += n
            defaults[n] = d

        arg_list = []
        call_list = []

        # now build the signature.
        for (n, t, d) in self:
            if t == Signature.ARGUMENT or \
                            t == Signature.ARGUMENT_WITH_DEFAULT:
                arg_list.append(n)
                call_list.append(n)
            elif t == Signature.KEYWORD_ONLY:
                arg_list.append('%s=p_%s["%s"]' % (n, nprefix, n))
                call_list.append(n)
            elif t == Signature.VARARG:
                arg_list.append('*%s' % (n,))
                call_list.append('*%s' % (n,))
            elif t == Signature.KEYWORD_VARARG:
                arg_list.append('**%s' % (n,))
                call_list.append('**%s' % (n,))

        # and finally execute some code.
        code = 'def %s(%s):\n    return w_%s(%s)' % (
            name, ','.join(arg_list), nprefix, ','.join(call_list))

        def wrapper(f):
            # Build a local context
            ctx = {
                'w_%s' % (nprefix,): f,
                'p_%s' % (nprefix,): defaults
            }

            utils.exec_(code, ctx)

            return ctx[name]

        return wrapper

    def __str__(self):
        """ Turns this Signature object into a string representation.

        :rtype: str
        """

        arg_list = []

        for (n, t, d) in self:
            if t == Signature.ARGUMENT:
                arg_list.append(str(n))
            elif t == Signature.ARGUMENT_WITH_DEFAULT or \
                            t == Signature.KEYWORD_ONLY:
                arg_list.append('%s=%r' % (n, d))
            elif t == Signature.VARARG:
                arg_list.append('*%s' % (n,))
            elif t == Signature.KEYWORD_VARARG:
                arg_list.append('**%s' % (n,))
        return ', '.join(arg_list)

    def __eq__(self, other):
        """ Checks if this Signature is equal to another signature.

        :param other: Signature to compare with.
        :type other: Signature

        :rtype bool:
        """

        if not isinstance(other, Signature):
            return False

        return (
            self.args == other.args and
            self.vararg == other.vararg and
            self.varkw == other.varkw and
            self.defaults == other.defaults and
            self.kwonlyargs == other.kwonlyargs and
            self.kwonlydefaults == other.kwonlydefaults
        )


class AppliedSignature(object):
    """ Represents an applied signature, i.e. the arguments to a function
    call. """

    def __init__(self, signature, args=None, kwargs=None):
        """ Creates a new AppliedSignature instance.

        Raises MissingArgument in case insufficient arguments are provided.
        Raises DoubleArgumentValue if an argument is passed more than one.
        Raises TooManyArguments if an argument if too many arguments are
        passed.
        Raises TooManyKeyWordArguments if too many keyword arguments are
        passed.


        :raise: exceptions.MissingArgument
        :raise: exceptions.DoubleArgumentValue
        :raise: exceptions.TooManyArguments
        :raise: exceptions.TooManyKeyWordArguments

        :param signature: Signature that is being applied.
        :type signature: Signature

        :param args: Argument to be passed to the applied Signauture.
        :type args: List

        :param kwargs: Keyword arguments to be passed to the function.
        :type kwargs: dict
        """

        # store the signature
        self.__sig = signature

        # Set the default values of the arguments.
        if args is None:
            args = []
        else:
            args = list(args)

        if kwargs is None:
            kwargs = {}
        else:
            kwargs = dict(kwargs)

        # Initialise a dict of values.
        self.__values = {}

        # boolean indicating if we had a keyword argument
        had_keyword = False

        # list of values that have already been passed
        passed_args = []

        # Iterate over the arguments
        for (n, t, d) in signature:

            # normal argument: first try to gobble up the default value
            # from the list.
            if (t == Signature.ARGUMENT or
                        t == Signature.ARGUMENT_WITH_DEFAULT):

                # if we did not yet have a keyword argument.
                if not had_keyword:

                    # check if it is given in the list normally.
                    if len(args) > 0:
                        self.__values[n] = args.pop(0)

                    # check if it is given in the keyword arguments.
                    elif n in kwargs:
                        had_keyword = True
                        self.__values[n] = kwargs.pop(n)
                    # do we perhaps have a default?
                    elif t == Signature.ARGUMENT_WITH_DEFAULT:
                        had_keyword = True
                        self.__values[n] = d
                    # else it is missing
                    else:
                        raise exceptions.MissingArgument(n)

                # if has to be in keyword arguments.
                else:
                    # was it given
                    if n in kwargs:
                        self.__values[n] = kwargs.pop(n)

                    # do we perhaps have a default?
                    elif t == Signature.ARGUMENT_WITH_DEFAULT:
                        self.__values[n] = d
                    # else it is missing
                    else:
                        raise exceptions.MissingArgument(n)
            elif t == Signature.VARARG:
                self.__values[n] = tuple(args)
                args = []
            elif t == Signature.KEYWORD_ONLY:
                # is it given?
                if n in kwargs:
                    self.__values[n] = kwargs.pop(n)
                else:
                    self.__values[n] = d
            elif t == Signature.KEYWORD_VARARG:
                # check if we gave something twice.
                for k in kwargs:
                    if k in passed_args:
                        raise exceptions.DoubleArgumentValue(k)

                self.__values[n] = kwargs
                kwargs = {}

            # we passed this argument.
            passed_args.append(n)

        # check that we didn't pass too many arguments.
        if len(args) > 0:
            raise exceptions.TooManyArguments()

        # check that we didn't pass too many keyword arguments.
        if len(kwargs) > 0:
            for k in kwargs:
                if k in passed_args:
                    raise exceptions.DoubleArgumentValue(k)
            raise exceptions.TooManyKeyWordArguments()

    def call(self, f=None):
        """ Applies this AppliedSignature to a given function.

        :param f: Function to apply this signature to. Defaults to the original
        function wrapped by self.signature.
        :type f: callable
        """

        # load the wrapped function
        if f is None:
            f = self.signature.callable

        # the map of defaults
        values = {}
        nprefix = ''

        # create an unused name
        # and store the values
        for (n, t, v) in self:
            nprefix += n
            values[n] = self[n]

        # build the argument list
        arg_list = []

        for (n, t, v) in self:
            if t == Signature.ARGUMENT or t == Signature.ARGUMENT_WITH_DEFAULT:
                arg_list.append('v_%s[%r]' % (nprefix, n,))
            elif t == Signature.KEYWORD_ONLY:
                arg_list.append('%s=v_%s[%r]' % (n, nprefix, n))
            elif t == Signature.VARARG:
                arg_list.append('*v_%s[%r]' % (nprefix, n,))
            elif t == Signature.KEYWORD_VARARG:
                arg_list.append('**v_%s[%r]' % (nprefix, n,))

        # and run the code.
        code = 'o_%s = w_%s(%s)' % (nprefix, nprefix, ','.join(arg_list))
        ctx = {
            'w_%s' % (nprefix,): f,
            'v_%s' % (nprefix): values
        }

        utils.exec_(code, ctx)

        return ctx['o_%s' % (nprefix,)]

    def __call__(self, *args, **kwargs):
        """ Creates a new AppliedSignature instance by partially overriding the
        arguments given to this function.

        Raises MissingArgument in case insufficient arguments are provided.
        Raises DoubleArgumentValue if an argument is passed more than one.
        Raises TooManyArguments if an argument if too many arguments are
        passed.
        Raises TooManyKeyWordArguments if too many keyword arguments are
        passed.

        :raise: exceptions.MissingArgument
        :raise: exceptions.DoubleArgumentValue
        :raise: exceptions.TooManyArguments
        :raise: exceptions.TooManyKeyWordArguments

        :rtype: AppliedSignature
        """

        args = list(args)

        # Read in the existing values
        existing_values = self.arguments()

        # Prepare what we want to pass
        target_args = []
        target_kwargs = {}


        # boolean indicating if we had a keyword argument
        had_keyword = False

        # list of values that have already been passed
        passed_args = []

        # Iterate over the arguments
        for (n, t, v) in self:

            # normal argument: first try to gobble up the default value
            # from the list.
            if (t == Signature.ARGUMENT or
                        t == Signature.ARGUMENT_WITH_DEFAULT):

                # if we did not yet have a keyword argument.
                if not had_keyword:

                    # check if it is given in the list normally.
                    if len(args) > 0:
                        target_args.append(args.pop(0))

                    # check if it is given in the keyword arguments.
                    elif n in kwargs:
                        had_keyword = True
                        target_args.append(kwargs.pop(n))

                    # else it is missing -- we use what we already have
                    else:
                        target_args.append(v)
                        had_keyword = True

                # if has to be in keyword arguments.
                else:
                    # was it given
                    if n in kwargs:
                        target_args.append(kwargs.pop(n))

                    # else it is missing -- we use what we already have
                    else:
                        target_args.append(v)
            elif t == Signature.VARARG:

                # if we have no varargs, use the old ones
                if len(args) == 0:
                    target_args.extend(list(v))

                # else use the new ones.
                else:
                    target_args.extend(args)
                    args = []
            elif t == Signature.KEYWORD_ONLY:
                # is it given? if so, use them
                if n in kwargs:
                    target_kwargs[n] = kwargs.pop(n)

                # else use the new ones.
                else:
                    target_kwargs[n] = v
            elif t == Signature.KEYWORD_VARARG:
                # copy over existing kwargs
                for k in v:
                    target_kwargs[k] = v[k]

                # and add all the new ones passed.
                for k in kwargs:
                    if k in passed_args:
                        raise exceptions.DoubleArgumentValue(k)

                    target_kwargs[k] = kwargs[k]

                # and we used all of them
                kwargs = {}

            # we passed this argument.
            passed_args.append(n)

        # check that we didn't pass too many arguments.
        if len(args) > 0:
            raise exceptions.TooManyArguments()

        # check that we didn't pass too many keyword arguments.
        if len(kwargs) > 0:
            for k in kwargs:
                if k in passed_args:
                    raise exceptions.DoubleArgumentValue(k)
            raise exceptions.TooManyKeyWordArguments()

        # and return a new signature
        return AppliedSignature(self.signature, target_args, target_kwargs)

    def __getitem__(self, item):
        """ Gets the value of the argument with a given name.

        :param item: Name of item to get.
        :type item: str
        """

        return self.__values[item]

    def arguments(self):
        """  Returns a list of normalised arguments to this function.

        :rtype: dict
        """

        return dict(self.__values)

    def __iter__(self):
        """ Iterates over the arguments in this AppliedSignature.
        Each element is a triple (name, tp, v) where
            - name is a string giving the name of the argument,
            - tp is the type of the argument and is one of Signature.ARGUMENT,
                Signature.ARGUMENT_WITH_DEFAULT, Signature.VARARG,
                Signature.KEYWORD_VARARG or Signature.KEYWORD_ONLY
            - v is the value of the argument
        """

        for (n, t, d) in self.signature:
            yield (n, t, self[n])

    def __str__(self):
        """ Turns this AppliedSignature object into a string representation.

        :rtype: str
        """

        arg_list = []

        for (n, t, v) in self:
            if t == Signature.ARGUMENT:
                arg_list.append(repr(v))
            elif t == Signature.ARGUMENT_WITH_DEFAULT or \
                            t == Signature.KEYWORD_ONLY:
                arg_list.append('%s=%r' % (n, v))
            elif t == Signature.VARARG:
                arg_list.append('*%s=%r' % (n, v))
            elif t == Signature.KEYWORD_VARARG:
                arg_list.append('**%s=%r' % (n, v))
        return ', '.join(arg_list)

    def __eq__(self, other):
        """ Checks if this AppliedSignature is equal to another
        AppliedSignature.

        :param other: AppliedSignature to compare with.
        :type other: AppliedSignature

        :rtype bool:
        """

        if not isinstance(other, AppliedSignature):
            return False

        return (
            self.signature == other.signature and
            self.arguments() == other.arguments()
        )

    @property
    def signature(self):
        """ The signature that is being applied.

        :rtype: Signature
        """

        return self.__sig
