
from __future__ import print_function

import inspect
import linecache
import sys
import traceback
from .assertion import rerun_failing_assert
from .importation import import_module

class TestFailure(Exception):
    """Test failure encountered during importation or setup."""

_python3 = (sys.version_info.major >= 3)
_no_such_fixture = object()

def run_tests_of(module_name):
    module = import_module(module_name)
    d = module.__dict__

    test_names = sorted(k for k in d if k.startswith('test_'))
    candidates = [d[k] for k in test_names]
    tests = [t for t in candidates if t.__module__ == module_name]

    for test in tests:
        try:
            for result in run_test(module, test):
                yield result
        except TestFailure as e:
            tb = sys.exc_info()[2]
            frames = traceback.extract_tb(tb)
            yield 'F', e.__class__.__name__, str(e), frames

def run_test(module, test):
    code = test.__code__ if _python3 else test.func_code
    if not code.co_argcount:
        yield run_test_with_arguments(module, test, code, ())
        return
    names = inspect.getargs(code).args
    fixtures = []
    for name in names:
        fixture = getattr(module, name, _no_such_fixture)
        if fixture is _no_such_fixture:#
            line = linecache.getline(code.co_filename, code.co_firstlineno)
            line = line.strip()
            yield 'F', 'Failure', 'no such fixture {!r}'.format(name), [
                (code.co_filename, code.co_firstlineno, test.__name__, line)]
            return
        fixtures.append(fixture)
    for result in run_test_with_fixtures(module, test, code, names, fixtures, ()):
        yield result

def run_test_with_fixtures(module, test, code, names, fixtures, args):
    name = names[0]
    fixture = fixtures[0]
    if len(fixtures) == 1:
        for item in iterate_over_fixture(name, fixture):
            yield run_test_with_arguments(module, test, code, args + (item,))
    else:
        remaining_names = names[1:]
        remaining_fixtures = fixtures[1:]
        for item in iterate_over_fixture(name, fixture):
            for result in run_test_with_fixtures(
                    module, test, code, remaining_names,
                    remaining_fixtures, args + (item,)):
                yield result

def iterate_over_fixture(name, fixture):
    if callable(fixture):
        try:
            fixture = fixture()
        except Exception as e:
            raise TestFailure('Exception {} when calling {}()'.format(e, name))
    try:
        i = iter(fixture)
    except Exception as e:
        raise TestFailure('Exception {} calling iter() on {}'.format(e, name))
    while True:
        try:
            item = next(i)
        except Exception as e:
            raise TestFailure('Exception {} iterating over {}'.format(e, name))
        yield item

def run_test_with_arguments(module, test, code, args):
    try:
        test(*args)
    except AssertionError:
        tb = sys.exc_info()[2]
        frames = traceback.extract_tb(tb)
    except Exception as e:
        tb = sys.exc_info()[2]
        frames = traceback.extract_tb(tb)[1:]
        return 'E', e.__class__.__name__, str(e), frames
    else:
        return '.'

    message = rerun_failing_assert(test, code, args)
    return 'E', 'AssertionError', message, frames
