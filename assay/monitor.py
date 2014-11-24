"""Monitor a package for changes and run its tests when it changes."""

from __future__ import print_function

import os
import sys
from time import time
from . import unix
from .discovery import interpret_argument, search_argument
from .filesystem import Filesystem
from .importation import import_module, improve_order, list_module_paths
from .runner import capture_stdout_stderr, run_tests_of
from .worker import Worker

class Restart(BaseException):
    """Tell ``main()`` that we need to restart."""

python3 = sys.version_info >= (3,)
stdin_fd = sys.stdin.fileno()
stdout_fd = sys.stdout.fileno()
ctrl_d = b'\x04'

def read_keystrokes():
    """Read user keystrokes from standard input."""
    keystrokes = os.read(stdin_fd, 1024)
    if python3:
        keystrokes = [keystrokes[i:i+1] for i in range(len(keystrokes))]
    return keystrokes

def write(string):
    """Send `string` immediately to standard output, without buffering."""
    os.write(stdout_fd, string.encode('ascii'))

def main_loop(arguments, is_batch):
    """Run and report on tests while also letting the user type commands."""

    main_process_paths = set(path for name, path in list_module_paths())

    file_watcher = Filesystem()
    file_watcher.add_paths(main_process_paths)

    poller = unix.EPoll()
    poller.register(file_watcher)
    if not is_batch:
        poller.register(sys.stdin)

    runner = None  # so our 'finally' clause does not explode
    workers = []
    try:
        for i in range(unix.cpu_count()):
            worker = Worker()
            workers.append(worker)
            poller.register(worker)

        paths_under_test = set()
        runner = run_all_tests(arguments, workers, paths_under_test, is_batch)
        next(runner)

        for source, flags in poller.events():

            if isinstance(source, Worker):
                try:
                    runner.send(source)
                except StopIteration:
                    file_watcher.add_paths(paths_under_test)
                    write('Watching {0} paths...'.format(len(paths_under_test)))

            elif source is sys.stdin:
                for keystroke in read_keystrokes():
                    print('got {0}'.format(keystroke))
                    if keystroke == b'q' or keystroke == ctrl_d:
                        sys.exit(0)
                    elif keystroke == b'r':
                        raise Restart()

            elif source is file_watcher:
                changes = file_watcher.read()
                paths = [os.path.join(directory, filename)
                         for directory, filename in changes]
                main_process_changes = main_process_paths.intersection(paths)
                if main_process_changes:
                    example_path = main_process_changes.pop()
                    write('\nAssay has been modified: {0}'.format(example_path))
                    raise Restart()
                runner.close()
                write(repr(paths))

                if paths:
                    write('\n\nFile modified: {0}\n\n'.format(paths[0]))

                paths_under_test = set()
                runner = run_all_tests(arguments, workers, paths_under_test,
                                       is_batch)
                next(runner)

            # import_order = improve_order(import_order, dangers)
            # module_paths, events = worker(import_modules, import_order)
    finally:
        if runner is not None:
            runner.close()
        for worker in workers:
            worker.close()

def run_all_tests(arguments, workers, paths_under_test, is_batch):
    worker = workers[0]
    running_workers = set()
    names = []
    t0 = time()
    successes = failures = 0

    for argument in arguments:
        import_path, import_name = interpret_argument(worker, argument)
        more_names = search_argument(import_path, import_name)
        names.extend(more_names)

    def give_work_to(worker):
        if names:
            name = names.pop()
            worker.start(capture_stdout_stderr, run_tests_of, name)
        else:
            running_workers.remove(worker)
            paths = [path for name, path in worker.call(list_module_paths)]
            paths_under_test.update(paths)

    for worker in workers:
        worker.push()

    try:
        for worker in workers:
            running_workers.add(worker)
            give_work_to(worker)

        while running_workers:
            worker = yield
            result = worker.next()
            if result is StopIteration:
                give_work_to(worker)
            elif result == '.':
                write('.')
                successes += 1
            else:
                pretty_print_exception(*result)
                failures += 1

    finally:
        for worker in workers:
            worker.pop()

    dt = time() - t0
    if failures:
        tally = red('{0} of {1} tests failed'.format(
            failures, successes + failures))
    else:
        tally = green('All {0} tests passed'.format(successes))
    write('\n{0} in {1:.2f} seconds\n'.format(tally, dt))

    if is_batch:
        exit(1 if failures else 0)

def install_import_path(path):
    sys.modules.insert(0, path)

stdout_banner = ' stdout '.center(72, '-')
stderr_banner = ' stderr '.center(72, '-')
plain_banner = '-' * 72

def pretty_print_exception(character, name, message, frames, out='', err=''):
    print()
    out = out.rstrip()
    err = err.rstrip()
    if out:
        print(stdout_banner)
        print(green(out))
    if err:
        print(stderr_banner)
        print(yellow(err))
    if out or err:
        print(plain_banner)
    for tup in frames:
        filename, line_number, function_name, text = tup
        a = '  {0} line {1} in'.format(filename, line_number)
        b = '{0}'.format(function_name)
        f = '{0}\n  {1}' if (len(a) + len(b) > 78) else '{0} {1}'
        print(f.format(a, b))
        print(blue('    ' + text.replace('\n', '\n    ')))
    line = '{0}: {1}'.format(name, message) if message else name
    print(red(line))
    print()

def black(text): # ';47' does bg color
    return '\033[1;30m' + str(text) + '\033[0m'

def red(text):
    return '\033[1;31m' + str(text) + '\033[0m'

def green(text):
    return '\033[1;32m' + str(text) + '\033[0m'

def yellow(text):
    return '\033[1;33m' + str(text) + '\033[0m'

def blue(text):
    return '\033[1;35m' + str(text) + '\033[0m'
