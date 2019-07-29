from datetime import datetime
from functools import wraps


def time_this(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        start_time = datetime.now()
        print("Starting {}".format(func.__name__))
        result = func(*args, **kwargs)
        elapsed = datetime.now() - start_time
        print("Finished {} in {}".format(func.__name__, elapsed))
        return result

    return wrapped
