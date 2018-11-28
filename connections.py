import requests
import functools

from exceptions import GetError

def connection(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            r = func(*args, **kwargs)
        except Exception as e:
            error = f'Exception occurs in function: {func.__name__}. Exception: {e}.'
            raise GetError(error)
        return r
    return wrapper

@connection
def get(*args, **kwargs):
    r = requests.get(*args, **kwargs)
    return r

@connection
def post(*args, **kwargs):
    r = requests.post(*args, **kwargs)
    return r
