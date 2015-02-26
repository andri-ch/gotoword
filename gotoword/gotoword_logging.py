# -*- coding: utf8 -*-

import logging
import logging.handlers


def set_up_logging(default_level, name=''):
    ### DEBUG -> is the lowest level ###
    #logging.basicConfig(level=default_level)
    # .basicConfig adds a stream handler by default
    msg_format = ("%(asctime)s [  %(levelname)s  ] %(className)s.%(funcName)s "
                  "- %(message)s")
    #msg_format = ("%(asctime)s [  %(levelname)s  ] .%(funcName)s "
    #              "- %(message)s")
    formatter = logging.Formatter(msg_format)

    file_handler = logging.FileHandler(filename="gotoword.log",
                                       mode="w")
    file_handler.setFormatter(formatter)

    IP = 'localhost'
    PORT = logging.handlers.DEFAULT_TCP_LOGGING_PORT
    socket_handler = logging.handlers.SocketHandler(IP, PORT)
    # socket_handler is used to send logs to a socket server in the functional
    # tests file
    sock_msg_format = "%(message)s"
    socket_formatter = logging.Formatter(sock_msg_format)
    socket_handler.setFormatter(socket_formatter)

    # override Logger.makeRecord with a custom one to allow
    # logging facilities used by @log:
    logging.Logger.makeRecord = custom_makeRecord
    #logger = logging.getLogger('app')
    logger = logging.getLogger(name)
    logger.setLevel(default_level)
    logger.addHandler(file_handler)
    logger.addHandler(socket_handler)
    return logger


def custom_makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None):
        """
        A factory method which can be overridden in subclasses to create
        specialized LogRecords.

        For instance, 'funcName' is an attribute of LogRecord, created
        automatically and cannot be overwritten except if you use a
        LoggerAdapter instead of Logger.

        With this method, LogRecord attbutes can now be overwritten by keys
        in 'extra' dict.
        Eg:
        >>> logger.debug('test message', extra={'funcName': 'some_fct'})

        """
        rv = logging.LogRecord(name, level, fn, lno, msg, args, exc_info, func)
        if extra is not None:
            for key in extra:
                #if (key in ["message", "asctime"]) or (key in rv.__dict__):
                #    raise KeyError("Attempt to overwrite %r in LogRecord" % key)
                rv.__dict__[key] = extra[key]
        return rv


#def log(fn):
#    """Adapted the decorator for extracting the name of the function even if
#    the function is decorated.
#    """
#    # uncomment if multiple decorators wrap fn:
#    #decorators = get_decorators(fn)
#    #fn = decorators[0]
#
#    def wrapper(obj, *args, **kwargs):
#        """
#        Because fn is wrapped, the function name when logging, will be
#        'wrapper':
#        >>> fn.__repr__()
#        '<unbound method CheckContextState.wrapper>'
#        """
#        logger.debug('About to run %s with args: %s and kwargs: %s' %
#                     (fn.__name__, args[1:], kwargs),
#                     extra={'className': strip(getattr(obj, '__class__', "")),
#                            'funcName': fn.__name__}
#                     )
#        # getattr() is needed because not all functions decorated by log()
#        # are bounded to a class instance.
#        out = fn(obj, *args, **kwargs)
#        logger.debug('Done running %s; return value: %s' %
#                     (fn.__name__, out),
#                     extra={'className': strip(getattr(obj, '__class__', "")),
#                            'funcName': fn.__name__}
#                     )
#        return out
#    return wrapper


def logger_as_decorator_factory(logger):
    """Factory used to return a decorator that logs function call and
    its return value.
    Useful when every module has its own logger, so this function is imported
    from library and gets a per module logger.
    Args:
    logger - logger used in the decorator to log events.
    Usage:
        from library import logger_as_decorator_factory
        import logging

        logger = logging.getLogger()
        logger.debug("message module main logger")
        log = logger_as_decorator_factory(logger)

        @log
        def function_to_be_logged():
            print("this function's call signature and return value will be "
                  "logged")
    """
    def log(fn):
        """Adapted the decorator for extracting the name of the function even if
        the function is decorated.
        """
        # uncomment if multiple decorators wrap fn:
        #decorators = get_decorators(fn)
        #fn = decorators[0]

        def wrapper(obj, *args, **kwargs):
            """
            Because fn is wrapped, the function name when logging, will be
            'wrapper':
            >>> fn.__repr__()
            '<unbound method CheckContextState.wrapper>'
            """
            logger.debug('About to run %s with args: %s and kwargs: %s' %
                         (fn.__name__, args[1:], kwargs),
                         extra={'className': strip(getattr(obj, '__class__', "")),
                                'funcName': fn.__name__}
                         )
            # getattr() is needed because not all functions decorated by log()
            # are bounded to a class instance.
            out = fn(obj, *args, **kwargs)
            logger.debug('Done running %s; return value: %s' %
                         (fn.__name__, out),
                         extra={'className': strip(getattr(obj, '__class__', "")),
                                'funcName': fn.__name__}
                         )
            return out
        return wrapper
    return log


def get_decorators(function):
    """Get decorators wrapping a function:
    http://schinckel.net/2012/01/20/get-decorators-wrapping-a-function/

    Recursive function that returns a list of functions, last element L[-1]
    is the original function.
    """
    # all python functions have an attr. 'func_closure' which is None or a
    # tuple;
    # If func_closure is None, it means we are not wrapping any other
    # functions -> it's the original function that's being wrapped.
    if not function.func_closure:
        return [function]
    decorators = []
    # Otherwise, we want to collect all of the recursive results for every
    # closure we have.
    for closure in function.func_closure:
        decorators.extend(get_decorators(closure.cell_contents))
    return [function] + decorators


def strip(s):
    """Used to stringify and then strip a class name accessed using
    obj.__class__ so that it is suitable for pretty printing.
    This function will be used like this::

        >>> print("this is class %s " % strip(obj.__class__))
        'this is class module.Class'

    Without this function the output would look like this::

        'this is class <class 'module.Class'>

    This function is needed because::

        >>> obj.__class__
        module.Class
        >>> print(obj.__class__)
        <class 'module.Class'>
        >>> type(s)
        type

    so obj.__class__ is not 'str' but of type 'type' , so we need to call
    repr(s) to get the string notation and get rid of the characters we don't
    want.

    It is used by the logging system.
    """
    return repr(s).lstrip("<class '").rstrip("'>")


#########
## MAIN
#########
# get same logger 'app' created in other modules
logger = logging.getLogger('app')
#logger = set_up_logging(logging.DEBUG)
#logger = set_up_logging(logging.INFO)
