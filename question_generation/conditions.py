# my own try & mixup of internet parts on pre- and post-conditions

# Original Code from:
# https://stackoverflow.com/questions/12151182/python-precondition-postcondition-for-member-function-how

import functools


def condition(pre_condition=None, post_condition=None):
    """
    Usage:

    @pre_condition(lambda arg: arg > 0)
    def function(arg): # ordinary function
        pass

    class C(object):
        @post_condition(lambda ret: ret > 0)
        def method_fail(self):
            return 0
        @post_condition(lambda ret: ret > 0)
        def method_success(self):
            return 1

    """

    def decorator(func):
        @functools.wraps(func)  # presever name, docstring, etc
        def wrapper(*args, **kwargs):  # NOTE: no self
            if pre_condition is not None:
                assert pre_condition(*args, **kwargs), "Pre-Condition was not met!"
            retval = func(*args, **kwargs)  # call original function or method
            if post_condition is not None:
                assert post_condition(retval), "Post-Condition was not met!"
            return retval

        return wrapper

    return decorator


def pre_condition(check):
    return condition(pre_condition=check)


def post_condition(check):
    return condition(post_condition=check)
