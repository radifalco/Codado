# coding=utf-8
"""
Missing batteries from Python
"""
import random
import inspect
import os
import re
import types

import attr

import ftfy


EMOJI = u'👻👾🤖😼💫👒🎩🐶🦎🐚🌸🌲🍋🥝🥑🥐🍿🥄⛺🚂🚲🌈🏆🎵💡✏🖍📌🛡♻'


@attr.s
class Documentation(object):
    """
    A docstring parser
    """
    raw = attr.ib()
    decode = attr.ib(default=False)

    @property
    def first(self):
        return self.raw.split('\n')[0]

    @property
    def full(self):
        """
        The full docstring, line-folded
        """
        # conveniently, all these calls return unicode if they're passed in unicode, so we
        # won't mangle unicode docstrings at this point.
        out = re.sub(r'\n\n', '\v', self.raw)
        return out.replace('\n', ' ').replace('\v', '\n\n')

    @classmethod
    def fromObject(cls, obj, decode=None):
        """
        Construct a `Documentation` from any object with a docstring

        With `decode=True`, decode docstrings as utf-8, then run them through ftfy, and return unicode.
        """
        if obj.__doc__ is None:
            return cls(u'' if decode else '')
        r = cls.fromString(obj.__doc__, decode=decode)
        return r

    @classmethod
    def fromString(cls, s, decode=None):
        out = inspect.cleandoc(s)
        if not decode or isinstance(out, unicode):
            return cls(out)
        else:
            return cls(ftfy.fix_encoding(out.decode('utf-8')))


def doc(obj):
    """
    The most common case, just give me the first line
    """
    return Documentation.fromObject(obj).first


def eachMethod(decorator, methodFilter=lambda fName: True):
    """
    Class decorator that wraps every single method in its own method decorator

    methodFilter: a function which accepts a function name and should return
    True if the method is one which we want to decorate, False if we want to
    leave this method alone.

    methodFilter can also be simply a string prefix. If it is a string, it is
    assumed to be the prefix we're looking for.
    """
    if isinstance(methodFilter, basestring):
        # Is it a string? If it is, change it into a function that takes a string.
        prefix = methodFilter
        methodFilter = lambda fName: fName.startswith(prefix)

    def innerDeco(cls):
        for fName, fn in inspect.getmembers(cls):
            if type(fn) is types.MethodType and methodFilter(fName):
                if fn.im_self is None:
                    # this is an unbound instance method
                    setattr(cls, fName, decorator(fn))
                else:
                    assert fn.im_class is type, "This should be a classmethod but it doesn't look like one: %r" % fName
                    setattr(cls, fName, classmethod(decorator(fn)))

        return cls
    return innerDeco


class enum(dict):
    """
    Create a simple attribute list from keys
    """
    @classmethod
    def fromkeys(cls, keys):
        ret = cls()
        dd = []
        for k in keys:
            dd.append((k, k))
        ret.update(dict(dd))
        return ret

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(attr)


def _sibpath(path, sibling):
    """
    Return the path to a sibling of a file in the filesystem.

    This is useful in conjunction with the special C{__file__} attribute
    that Python provides for modules, so modules can load associated
    resource files.

    (Stolen from twisted.python.util)
    """
    return os.path.join(os.path.dirname(os.path.abspath(path)), sibling)


class fromdir(object):
    """
    Swiss army knife for working with directory paths

    Returns a callable instance. Calls to the instance return paths from a
    preset directory.

    >>> fromcodado = fromdir('codado')
    >>> fromcodado('py.py')
    '/home/cory/src/Codado/codado/py.py'


    Also acts as a contextmanager that chdirs to the argument and returns
    self, the callable instance.

    >>> with fromdir('codado') as fromcodado:
    ...     print os.listdir('.')
    ...
    ['__init__.py', 'py.py', ..., 'py.pyc']


    When __init__ is called with multiple paths, they are joined.

    Also does ~homedir expansion, and accepts multiple path args to join.

    >>> print fromcodado('test', 'test_py.py')
    /home/cory/src/Codado/codado/test/test_py.py
    >>> print fromdir('~')('.bash_profile')
    /home/cory/.bash_profile


    As a final trick, if the argument is a file that exists, act like sibpath,
    and return paths relative to the dir that contains that file.

    (Only the argument is tested for existence and type.  In all other cases,
    this does only string manipulations and does not examine the filesystem.)

    >>> __file__ = '/home/cory/src/Codado/codado/__init__.py'
    >>> print fromdir(__file__)('tx.py')
    /home/cory/src/Codado/codado/tx.py
    >>> print fromdir(__file__, 'test')('test_tx.py')
    /home/cory/src/Codado/codado/test/test_tx.py


    Note the weird case that more than one argument is given, and more than
    one expands to a file; they are effectively discarded, and only the
    containing directory is used.

    >>> print fromdir(__file__, 'tx.py')('py.py')
    /home/cory/src/Codado/codado/py.py
    """
    def __init__(self, *paths):
        paths = list(paths)
        self.path = ''
        for cur in paths:
            cur = os.path.expanduser(cur)
            self.path = os.path.abspath(os.path.join(self.path, cur))

            if os.path.isfile(self.path):
                self.path = _sibpath(self.path, '')

    def __call__(self, *args):
        a = (self.path,) + args
        return os.path.join(*a)

    def __enter__(self):
        self._origDir = os.getcwd()
        os.chdir(self.path)
        return self

    def __exit__(self, type, value, tb):
        os.chdir(self._origDir)


def remoji():
    """
    Return a random, neutral emoji

    This list has been chosen to consist of emoji that have positive or neutral
    connotations, and which do not reflect any sort of identity symbols (e.g. no
    pictures of human beings). I have also tried to avoid symbols that have
    acquired punny or tasteless meanings, such as the eggplant emoji.

    I recognize that this list currently reflects my western bias. I am not confident
    that I can choose positive/neutral symbols from among the symbols that originate
    in non-western culture. Suggestions and updates to this list 100% welcome.
    """
    return random.choice(EMOJI)
