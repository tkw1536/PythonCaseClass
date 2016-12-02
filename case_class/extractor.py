from . import case_class, exceptions, utils, clsutils, signature


class Extractor(case_class.AbstractCaseClass):
    """ A Pattern-Matching object that can be used to extract variables
    from a class. """

    def _extract(self, o, ctx):
        """ Applies this Extractor to an object by extracting a
        context. Raises ExtractorDoesNotMatch if the pattern does not match.

        This function is for internal usage only, use .extract() instead.

        :raises: ExtractorDoesNotMatch


        :param o: Object to apply extractor to.
        :type o: object

        :param ctx: Existing context to use extractor in.
        :type ctx: dict

        :rtype: dict
        """

        raise NotImplementedError

    def extract(self, o):
        """ Applies this Extractor to an object by extracting a
        context. Raises ExtractorDoesNotMatch if the pattern does not match.

        :param o: Object to apply extractor to.
        :type o: object

        :param ctx: Existing context to use extractor in.
        :type ctx: dict

        :rtype: ExtractedContext
        """

        # Extract using the protected method
        ctx = self._extract(o, dict())

        # return an extracted context
        return ExtractedContext(ctx)

    def matches(self, o):
        """ Checks if this Extractor matches an object.

        :param o: Object to apply extractor to.
        :type o: object

        :rtype: bool
        """

        try:
            self.extract(o)
            return True
        except exceptions.ExtractorDoesNotMatch:
            return False

    #
    # MAGIC methods
    #

    def __call__(self, *args, **kwargs):
        """ Creates a new Extractor that extracts this instance to a set of
        arguments.

        :param args: Arguments to extract
        :type args: tuple

        :param kwargs: Keyword arguments to extract
        :type kwargs: dict

        :rtype: A
        """

        return A(self, args, kwargs)

    def __rshift__(self, other):
        """ Creates a new Extractor that stores this Pattern in a variable.

        :param other: Name of variable to store this pattern in.
        :type other: str

        :rtype: And
        """

        return And(self, V(other))

    def __and__(self, other):
        """ Creates a new Extractor that stores this pattern and another
        pattern at the same time.

        :param other: Other Extractor pattern to match.
        :type other: object

        :rtype: And
        """

        # avoid a chained And() instance
        if isinstance(self, And):
            return And(*(self.patterns + (other,)))

        # return itself
        else:
            return And(self, other)

    @staticmethod
    def lift(o):
        """ Lifts an object into an Extractor.

        :param o: Object to turn into Extractor.
        :type o: object

        :rtype: Extractor
        """

        # if it is an extractor, return it.
        if isinstance(o, Extractor):
            return o

        # if it is _, ignore it
        elif o is _:
            return _()

        # If it is a type, we match anything of that type
        elif isinstance(o, type):
            return T(o)

        # in case of a callable, return a condition
        elif callable(o):
            return C(o)

        # else it is a literal
        else:
            return L(o)


class _(Extractor):
    """ An extractor that matches anything. """

    def _extract(self, o, ctx):
        """ Applies this Extractor to an object by extracting a
        context. Raises ExtractorDoesNotMatch if the pattern does not match.

        This function is for internal usage only, use .extract() instead.

        :raises: ExtractorDoesNotMatch


        :param o: Object to apply extractor to.
        :type o: object

        :param ctx: Existing context to use extractor in.
        :type ctx: dict

        :rtype: dict
        """

        return ctx


class V(Extractor):
    """ An extractor that extracts a single variable subject to a condition."""

    def __init__(self, name):
        """ Creates a new V() instance.

        :param name: Name of the extracted variable.
        :type name: str
        """

        self.__name = name

    def _extract(self, o, ctx):
        """ Applies this Extractor to an object by extracting a
        context. Raises ExtractorDoesNotMatch if the pattern does not match.

        This function is for internal usage only, use .extract() instead.

        :raises: ExtractorDoesNotMatch


        :param o: Object to apply extractor to.
        :type o: object

        :param ctx: Existing context to use extractor in.
        :type ctx: dict

        :rtype: dict
        """

        # if we already have a variable with the same name, it should be the
        # same
        if self.__name in ctx and ctx[self.__name] != o:
            raise exceptions.ExtractorDoesNotMatch()

        # and add itself
        ctx[self.__name] = o

        # and return the context
        return ctx


class A(Extractor):
    """ An Extractor that can extract signatures. """

    _patterns = []  #: List[ApplicationExtractor]

    def __init__(self, pattern, args, kwargs):
        """ Creates a new A() instance.

        :param pattern: Pattern that this extractor should match.
        :type pattern: Extractor

        :param args: Arguments that should be extracted.
        :type args: tuple

        :param kwargs: Keyword arguments that should be extracted.
        :type kwargs: dict
        """

        self.__pattern = pattern
        self.__args = tuple(map(Extractor.lift, args))

        self.__kwargs = dict()
        for k in kwargs:
            self.__kwargs[k] = Extractor.lift(kwargs[k])

    def _extract(self, o, ctx):
        """ Applies this Extractor to an object by extracting a
        context. Raises ExtractorDoesNotMatch if the pattern does not match.

        This function is for internal usage only, use .extract() instead.

        :raises: ExtractorDoesNotMatch


        :param o: Object to apply extractor to.
        :type o: object

        :param ctx: Existing context to use extractor in.
        :type ctx: dict

        :rtype: dict
        """

        # extract the context
        extracted_ctx = self.__pattern._extract(o, ctx)

        # find all matching extractors and sort them by priority
        extractors = filter(lambda ae: ae.applicable(o), A._patterns)
        extractors = sorted(extractors, key=lambda ae: ae.priority)
        extractors = list(extractors)

        # if we have none, they do not match
        if len(extractors) == 0:
            raise exceptions.ExtractorDoesNotMatch()

        # get the last element
        application_extractor = extractors[-1]

        # extract the actual applied signature
        actual_signature = application_extractor.extract(o)

        # make a signature that we should have
        try:
            should_signature = actual_signature.signature(*self.__args,
                                                          **self.__kwargs)
        except exceptions.AppliedSignatureException:
            raise exceptions.ExtractorDoesNotMatch()

        # now iterate over the values to extract
        for (name, tp, pattern) in should_signature:

            # extract the actual value
            try:
                value = actual_signature[name]
            except KeyError:
                raise exceptions.ExtractorDoesNotMatch()

            # extract all the items one by one
            extracted_ctx = pattern._extract(value, extracted_ctx)

        # and return the context
        return extracted_ctx


class ApplicationExtractor(case_class.AbstractCaseClass):
    """ Represents an extractor Component that can extract objects from a
    function. """

    def __init__(self, priority=0):
        """ Creates a new ApplicationExtractor() instance.

        :param priority: Priority of this extractor.
        :type priority: int
        """

        self.__priority = priority

    @property
    def priority(self):
        """ Priority of this ApplicationExtractor. """
        return self.__priority

    def applicable(self, o):
        """ Checks if this ApplicationExtractor is applicable to a given
        object.

        :param o: Object to check applicability to
        :type o: object

        :rtype: bool
        """

        raise NotImplementedError

    def extract(self, o):
        """ Applies this ApplicationExtractor to an object and extracts the
        parameters.

        :param o: Object to apply to.
        :type o: object

        :rtype: signature.AppliedSignature
        """

        raise NotImplementedError

    @classmethod
    def register(cls, *args, **kwargs):
        """Function that is called to register this ApplicationExtractor. """

        A._patterns.append(cls(*args, **kwargs))


class C(Extractor):
    """ Extractor that matches a conditional expression. """

    def __init__(self, func):
        """ Creates a new C() instance.

        :param func: Function that takes a context and returns a boolean
        if it matches.
        :type func: callable
        """

        # If we have a lambda, we need to do some dark magic
        # we want to have lambda a,b,c:... automatically extract a,b,c from
        # the context.
        if utils.is_lambda(func):

            # get the signature and the names in the signature
            s = signature.Signature(func)
            s_names = [name for (name, tp, d) in s]

            def lambda_wrapper(ctx):
                args = []

                # args to be passed to the lambda
                for name in s_names:
                    if not name in ctx:
                        return False

                    args.append(ctx[name])

                args = [ctx[name] for name in s_names]

                return func(*args)

            self.__func = lambda_wrapper
        else:
            self.__func = func

    def _extract(self, o, ctx):
        """ Applies this Extractor to an object by extracting a
        context. Raises ExtractorDoesNotMatch if the pattern does not match.

        This function is for internal usage only, use .extract() instead.

        :raises: ExtractorDoesNotMatch


        :param o: Object to apply extractor to.
        :type o: object

        :param ctx: Existing context to use extractor in.
        :type ctx: dict

        :rtype: dict
        """

        if not self.__func(ctx):
            raise exceptions.ExtractorDoesNotMatch()

        # and return the context
        return ctx


class F(Extractor, case_class.AbstractCaseClass):
    """ An extractor that matches anything subject to a condition. """

    def _matches(self, o):
        """ Protected method used to check if this Extractor matches an
        object.

        :param o: Object to apply extractor to.
        :type o: object

        :rtype: bool
        """

        raise NotImplementedError

    def matches(self, o):
        """ Checks if this Extractor matches an object.

        :param o: Object to apply extractor to.
        :type o: object

        :rtype: bool
        """

        return self._matches(o)

    def _extract(self, o, ctx):
        """ Applies this Extractor to an object by extracting a
        context. Raises ExtractorDoesNotMatch if the pattern does not match.

        This function is for internal usage only, use .extract() instead.

        :raises: ExtractorDoesNotMatch


        :param o: Object to apply extractor to.
        :type o: object

        :param ctx: Existing context to use extractor in.
        :type ctx: dict

        :rtype: dict
        """

        if not self._matches(o):
            raise exceptions.ExtractorDoesNotMatch()

        return ctx


class L(F):
    """ An Extractor that matches a literal. """

    def __init__(self, lit):
        """ Creates a new L() instance.

        :param lit: Literal to match
        :type lit: object
        """

        self.__lit = lit

    def _matches(self, o):
        """ Protected method used to check if this Extractor matches an
        object.

        :param o: Object to apply extractor to.
        :type o: object

        :rtype: bool
        """

        return o == self.__lit


class T(F):
    """ An Extractor that matches all objects of a specific type """

    def __init__(self, tp):
        """ Creates a new T() instance.

        :param tp: Type to match
        :type tp: type
        """

        self.__tp = tp

    def _matches(self, o):
        """ Protected method used to check if this Extractor matches an
        object.

        :param o: Object to apply extractor to.
        :type o: object

        :rtype: bool
        """

        return isinstance(o, self.__tp)


class And(Extractor):
    """ An Extractor that applies a set of patterns in order. """

    def __init__(self, *patterns):
        """ Creates a new And() instance.

        :param patterns: List of patterns to And()
        :type patterns: tuple
        """

        self.__patterns = tuple(map(Extractor.lift, patterns))

    @property
    def patterns(self):
        """ Returns the list of patterns used by this And() instance.

        :rtype: tuple
        """
        return self.__patterns

    def _extract(self, o, ctx):
        """ Applies this Extractor to an object by extracting a
        context. Raises ExtractorDoesNotMatch if the pattern does not match.

        This function is for internal usage only, use .extract() instead.

        :raises: ExtractorDoesNotMatch


        :param o: Object to apply extractor to.
        :type o: object

        :param ctx: Existing context to use extractor in.
        :type ctx: dict

        :rtype: dict
        """

        extracted_context = ctx

        for p in self.__patterns:
            extracted_context = p._extract(o, extracted_context)

        return extracted_context


class ExtractedContext(object):
    """ Represents a context that was extracted from an object"""

    def __init__(self, vars):
        """ Creates a new ExtractedContext() object.

        :param vars: Variables to update this extracted context with
        :type vars: dict
        """

        self.__vars = vars

    def __getitem__(self, item):
        """ Returns an item in this ExtractedContext or raises KeyError.

        :raises: KeyError

        :param item: Name of item to get.
        :type item: str

        :rtype: object
        """

        return self.__vars[item]

    def __getattr__(self, item):
        """ Returns an item in this ExtractedContext or raises KeyError.

        :raises: KeyError

        :param item: Name of item to get.
        :type item: str

        :rtype: object
        """

        return self.__vars[item]

    def __str__(self):
        """ Turns this ExtractedContext into a string. """

        return 'ExtractedContext(%s)' % (self.__vars,)


class CaseClassExtractor(ApplicationExtractor):
    def applicable(self, o):
        """ Checks if this ApplicationExtractor is applicable to a given
        object.

        :param o: Object to check applicability to
        :type o: object

        :rtype: bool
        """

        return isinstance(o, case_class.CaseClass)

    def extract(self, o):
        """ Applies this ApplicationExtractor to an object and extracts the
        parameters.

        :param o: Object to apply to.
        :type o: object

        :rtype: signature.AppliedSignature
        """

        return o.case_params.signature


CaseClassExtractor.register()


class PatternMatcher(case_class.CaseClass):
    """ Runs a pattern match scenario """

    def __init__(self, o):
        """ Creates a new PatternMatcher() instance.

        :param o: Object to pattern match on.

        """

        self.__o = o
        self.__context = None

    @property
    def context(self):
        """ Gets the context of this PatternMatcher.

        :rtype: ExtractedContext
        """

        if self.__context is None:
            raise exceptions.ExtractorDoesNotMatch()

        return self.__context

    def __getattr__(self, item):
        """ Returns an item in this ExtractedContext or raises KeyError or
        ExtractorDoesNotMatch.

        :raises: KeyError
        :raises: ExtractorDoesNotMatch

        :param item: Name of item to get.
        :type item: str

        :rtype: object
        """

        return getattr(self.context, item)

    def __getitem__(self, item):
        """ Returns an item in this ExtractedContext or raises KeyError or
        ExtractorDoesNotMatch.

        :raises: KeyError
        :raises: ExtractorDoesNotMatch

        :param item: Name of item to get.
        :type item: str

        :rtype: object
        """

        return self.context[item]

    def __or__(self, extractor):
        """ Applies an extractor to this patternMatch scenario.

        :param extractor: Extractor to apply
        :type extractor: Extractor

        :rtype: bool
        """

        ex = Extractor.lift(extractor)

        try:
            self.__context = ex.extract(self.__o)
            return True
        except exceptions.ExtractorDoesNotMatch:
            self.__context = None
            return False

    def __call__(self, extractor):
        """ Applies an extractor to this patternMatch scenario.

        :param extractor: Extractor to apply
        :type extractor: Extractor

        :rtype: bool
        """

        return self | extractor


__all__ = ["Extractor", "_", "V", "L", "T", "A", "C", "ExtractedContext",
           "PatternMatcher"]
