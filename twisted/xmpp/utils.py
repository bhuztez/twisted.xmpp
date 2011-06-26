import sys
import traceback

from functools import wraps
from inspect import getargspec, currentframe


class NoMatchingClause(Exception): pass


def get_pattern_wrapper(func):
    fn_args, fn_varargs, fn_keywords, fn_defaults = getargspec(func)
    fn_defaults = fn_defaults or ()
    pattern_args = len(fn_args) - len(fn_defaults)
    pattern_keywords = dict(zip(fn_args[-len(fn_defaults):], fn_defaults))

    @wraps(func)
    def wrapper(*args, **kwargs):
        count = 0
        if fn_defaults:
            for i, arg in enumerate(args[pattern_args:]):
                if fn_defaults[i] != arg:
                    raise TypeError
                count += 1

        for key, value in pattern_keywords.items():
            if key in kwargs:
                if value != kwargs[key]:
                    raise TypeError
                count += 1

        if count < len(fn_defaults):
            raise TypeError

        return func(*args, **kwargs)

    return wrapper




class PatternDispatcher(list):

    def __init__(self, name):
        self.__name__ = name


    def __call__(self, *args, **kwargs):
        for func in self:
            try:
                return func(*args, **kwargs)
            except TypeError:
                exc_type, value, tb = sys.exc_info()
                if tb.tb_next.tb_next:
                    raise

        # raise TypeError('%s(): no matching pattern'%(self.__name__))
        raise NoMatchingClause


    def __get__(self, instance, owner):
        if instance is None:
            return self
        return lambda *args, **kwargs: self(instance, *args, **kwargs)


    def match(self, func):
        self.append(get_pattern_wrapper(func))
        return self



def match(func):
    frame = currentframe()
    try:
        dispatcher = frame.f_back.f_locals.get(
            func.__name__,
            PatternDispatcher(func.__name__))
    finally:
        del frame

    assert isinstance(dispatcher, PatternDispatcher)
    dispatcher.append(get_pattern_wrapper(func))
    return dispatcher



class MatchBase(object):

    def __or__(self, other):
        return MatchOr((self, other))

    def __and__(self, other):
        return MatchAnd((self, other))


class MatchString(str, MatchBase):
    pass


class MatchAnd(object):

    def __init__(self, matchers):
        self.matchers = matchers

    def __eq__(self, other):
        return all( m==other for m in self.matchers)


    def __ne__(self, other):
        return not self.__eq__(other)



class MatchOr(object):

    def __init__(self, matchers):
        self.matchers = matchers

    def __eq__(self, other):
        return any( m==other for m in self.matchers)

    def __ne__(self, other):
        return not self.__eq__(other)



class MatchInstance(MatchBase):

    def __init__(self, klass=None, **kwargs):
        self.klass = klass
        self.kwargs = kwargs

    def __eq__(self, other):
        if self.klass and not isinstance(other, self.klass):
            return False
        return all(hasattr(other, k) and v == getattr(other, k) for k,v in self.kwargs.items())

    def __ne__(self, other):
        return not self.__eq__(other)



class MatchDict(MatchBase):

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __eq__(self, other):
        return all(k in other and v == other[k] for k,v in self.kwargs.items())

    def __ne__(self, other):
        return not self.__eq__(other)



