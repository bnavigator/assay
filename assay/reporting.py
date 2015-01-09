"""Display test results and respond to user keystrokes."""

from __future__ import print_function

import os
import sys
from time import time

stdout_fd = sys.stdout.fileno()
stdout_banner = ' stdout '.center(72, '-')
stderr_banner = ' stderr '.center(72, '-')
plain_banner = '-' * 72
help_hint = 'Press ? for help'
help_hint_length = len(help_hint)
help_message = """\
 [j] Next exception
 [k] Previous exception
 [r] Restart Assay
 [q] Quit Assay
 [?] Help (this summary)
"""  # Future: [m] Pipe all exceptions to more(1) or else your custom $PAGER

def write(string):
    """Send `string` immediately to standard output, without buffering."""
    os.write(stdout_fd, string.encode('ascii'))

class Reporter(object):
    def __init__(self):
        self.letters = []
        self.exceptions = []
        self.period = 78 - help_hint_length
        self.offset = 0
        self.t0 = time()

    def report_result(self, result):
        is_success = (result == '.')
        letter = '.' if is_success else result[0]
        self.letters.append(letter)
        if not self.exceptions:
            if is_success:
                write('.')
                return
            pretty_print_exception(*result)
            self.offset = (len(self.letters) - 1) % self.period
            write(' ' * (79 - help_hint_length) + help_hint + '\r')
        if not is_success:
            self.exceptions.append(result)
        if len(self.letters) % self.period == self.offset:
            write('\r')
        write(letter)
        #write(''.join(self.letters[-72:]) + '\r')

    def summarize(self):
        dt = time() - self.t0
        failures = len(self.exceptions)
        total = len(self.letters)
        if failures:
            tally = red('\r{0} of {1} tests failed'.format(failures, total))
        else:
            tally = green('\nAll {0} tests passed'.format(total))
        write('{0} in {1:.2f} seconds \b'.format(tally, dt))

    def show_help(self):
        write(help_message)

# def reporter_coroutine():
#     successes = failures = 0
#     t0 = time()
#     for item in (yield):
#         if item == '.':
#             write('.')
#             successes += 1
#         elif isinstance(item, tuple):
#             pretty_print_exception(*item)
#             failures += 1
#     dt = time() - t0
#     if failures:
#         tally = red('{0} of {1} tests failed'.format(
#             failures, successes + failures))
#     else:
#         tally = green('All {0} tests passed'.format(successes))
#     write('\n{0} in {1:.2f} seconds\n'.format(tally, dt))

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
