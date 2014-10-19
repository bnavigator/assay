"""Monitor a package for changes and run its tests when it changes."""

from __future__ import print_function

import os
import sys
import traceback
from pprint import pprint
from time import time
from .assertion import rerun_failing_assert
from .filesystem import FileWatcher
from .importation import import_module, get_directory_of, improve_order
from .worker import Worker

def f():
    pass

python3 = (sys.version_info.major >= 3)

def main_loop(module_names):
    worker = Worker()
    flush = sys.stdout.flush

    # with worker:
    #     path = worker(get_directory_of, module_name)

    # if path is not None:
    #     raise NotImplementedError('cannot yet introspect full packages')

    # known_modules = set()
    # module_order = []

    # with worker:
    #     paths, events = worker(import_modules, [module_name])

    # # TODO: just return set from worker?

    # for name, names in events:
    #     names = set(names) - known_modules
    #     module_order.extend(names)

    if False:
        # Debugging test of the module orderer: keep running the same
        # set of modules through the partial orderer to see how quickly
        # the order converges on something sensible.
        module_order = list(module_names)
        with worker:
            paths, events = worker(import_modules, module_order)
        pprint(events)
        for i in range(12):
            module_order = improve_order(events)
            with worker:
                paths, events = worker(import_modules, module_order)
            if not i:
                print('--------------------------')
                pprint(events)
        print('--------------------------')
        pprint(events)
        return

    # module_paths = {}

    # with worker:
    #     initial_imports = worker(list_modules)

    # print('Assay up and running with {} modules'.format(len(initial_imports)))

    # import_order = list(module_names)

    main_process_paths = set(imported_paths())
    file_watcher = FileWatcher()

    while True:
        # import_order = improve_order(import_order, dangers)
        # print('Importing {}'.format(module_names))
        with worker:
            # t0 = time()
            # module_paths, events = worker(import_modules, import_order)
            # pprint(events)
            # print('  {} seconds'.format(time() - t0))
            # print()
            worker(run_tests_of, module_names[0])
            paths = worker(imported_paths)
        print()
        print('Watching', len(paths), 'paths', end='...')
        flush()
        file_watcher.add_paths(paths)
        changes = file_watcher.wait()
        paths = [os.path.join(directory, filename)
                 for directory, filename in changes]
        print(paths)
        main_process_changes = main_process_paths.intersection(paths)
        if main_process_changes:
            example_path = main_process_changes.pop()
            print()
            print('Detected edit to {}'.format(example_path))
            print(' Restart '.center(79, '='))
            restart()
        print()
        print('Running tests')

        # with worker:
        #     before = set(worker(list_modules))
        #     worker(import_modules, [module_name])
        #     after = set(worker(list_modules))
        #     print(after - before)
        #     worker(run_tests_of, module_name)
        # print('Loading dependencies')
        # dependencies = after - before - {module_name}
        # dependencies = [d for d in dependencies if not d.startswith('sky')]
        # print(dependencies)
        # with worker:
        #     worker(import_modules, dependencies)
        #     print('Running tests')
        #     worker(run_tests_of, module_name)

def restart():
    executable = sys.executable
    os.execvp(executable, [executable, '-m', 'assay'] + sys.argv[1:])

def speculatively_import_then_loop(import_order, ):
    pass


def list_modules():
    return list(sys.modules)

def import_modules(module_names):
    old = set(sys.modules.keys())
    paths = {}
    events = []
    for module_name in module_names:
        try:
            module = import_module(module_name)
        except ImportError:
            continue  # for modules like "pytz.threading"

        path = getattr(module, '__file__', None)
        if path is not None:
            paths[path] = module_name

        new = set(name for name, module in sys.modules.items()
                  if module is not None)
        events.append((module_name, new - old))
        old = new
    return paths, events

def imported_paths():
    return {module.__file__: name for name, module in sys.modules.items()
            if (module is not None) and hasattr(module, '__file__')}

def run_tests_of(module_name):
    flush = sys.stderr.flush
    if python3:
        write = sys.stderr.buffer.write
    else:
        write = sys.stderr.write

    module = import_module(module_name)
    d = module.__dict__

    good_names = sorted(k for k in d if k.startswith('test_'))
    candidates = [d[k] for k in good_names]
    tests = [t for t in candidates if t.__module__ == module_name]

    reports = []
    for t in tests:
        code = t.__code__ if python3 else t.func_code
        if code.co_argcount:
            print('#######',t)

        try:
            t()
        except AssertionError:
            message = 'rerun'
            character = b'E'
        except Exception as e:
            tb = sys.exc_info()[2]
            message = '{}: {}'.format(e.__class__.__name__, e)
            character = b'E'
        else:
            message = None
            character = b'.'

        write(character)
        flush()

        if message == 'rerun':
            message = rerun_failing_assert(t, code)

        def black(text): # ';47' does bg color
            return '\033[1;30m' + str(text) + '\033[0m'

        def blue(text):
            return '\033[1;35m' + str(text) + '\033[0m'

        def yellow(text):
            return '\033[1;33m' + str(text) + '\033[0m'

        def red(text):
            return '\033[1;31m' + str(text) + '\033[0m'

        if message is not None:
            for tup in traceback.extract_tb(tb):
                filename, line_number, function_name, text = tup
                a = '  {} line {}'.format(filename, line_number)
                b = 'in {}()'.format(function_name)
                f = '{}\n  {}' if (len(a) + len(b) > 78) else '{} {}'
                print(f.format(a, b))
                print('   ', blue(text))
                # print('  {} line {} in {}\n    {}'.format(
                #     , , text))
            print(' ', red(message))
            # reports.append('{}:{}\n  {}()\n  {}'.format(
            #     code.co_filename, code.co_firstlineno, t.__name__))
            print()
    print()
    for report in reports:
        print()
        print(report)
    return
    for tn in test_names:
        test = d[tn]
        print(test.__module__)
    return []
    names = []
    for name, obj in vars(module).items():
        if not name.startswith('test_'):
            continue
        names.append(name)
    return names
