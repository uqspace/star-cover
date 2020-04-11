import numpy as np


def vectorize(*args, **kwargs):
    def decorator(pyfunc):
        return np.vectorize(pyfunc, *args, **kwargs)
    return decorator
