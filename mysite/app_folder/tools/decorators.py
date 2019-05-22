from collections.abc import Hashable
from datetime import datetime
from functools import wraps, partial


def log_performance(func):
    from flask import current_app
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        func_name = func.__qualname__
        result = func(*args, **kwargs)
        end_time = datetime.now()
        elapsed = (end_time - start_time).microseconds
        elapsed /= 1e+6
        message = "Function {} took {} seconds".format(func_name, elapsed)
        current_app.logger.info(message)
        return result

    return wrapper


class memoized(object):
    '''Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        if not isinstance(args, Hashable):
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value

    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__

    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return partial(self.__call__, obj)
