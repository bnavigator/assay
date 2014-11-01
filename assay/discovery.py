"""Test discovery tools."""

import os
import re
import sys
from importlib import import_module
from keyword import iskeyword
from .importation import list_module_paths

def paths_and_modules(worker, names):
    """Return paths and modules for each name on the command line.

    Each name on the Assay command line can specify one of three things:
    a directory that contains .py files, the name of one particular .py
    file, or the name of a package that Python can import.  For every
    name provided in `names` this routine either reports an error to the
    user, or else yields a tuple (path, prefix) that will allow Python
    to import all of the Python files beneath the given name.

    """

def interpret_command_line_name(worker, name):
    """

    ('/os/path/addition', '')  - search the directory itself
    ('/os/path/addition', 'package.package') - search __path__ if present
    ('/os/path/addition', 'package.module') - search __path__ if present
    (None, 'package.package') - search __path__ if present

    """
    if os.path.isdir(name):
        if not is_package(name):
            return search_plain_directory, name
        directory, prefix = os.path.abspath(name), ''
        while is_package:
            parent, subdirectory = os.path.split(directory)
            if not subdirectory:
                print('Error: there should not be an __init__.py file'
                      ' at the root of your filesystem')
                return
            if not is_identifier(subdirectory):
                print('Error - directory contains an __init__.py but its'
                      ' name is not an identifier: {}'
                      .format(parent))
                return
            directory, prefix = parent, subdirectory + '.' + prefix
            is_package = os.path.isfile(os.path.join(directory, '__init__.py'))
        return directory, prefix

    if os.path.isfile(name):
        base, extension = os.path.splitext(name)
        if extension != '.py':
            print('Error - test file lacks .py extension: {}'.format(name))
            return
        parent, module_name = os.path.split(base)
        return (parent or '.'), module_name

    with worker:
        worker(import_modules, [name])
        module_paths = dict(worker(list_module_paths))
    if name in module_paths:
        return None, name

    print('Error - can neither open nor import: {}'.format(name))

def search_plain_directory(directory, listing):
    possible_packages = []
    for filename in listing:
        module_name = module_name_of(filename)
        if module_name is not None:
            yield module_name, directory
        elif is_identifier(filename):
            possible_packages.append(filename)
    for filename in possible_packages:
        subdirectory = os.path.join(directory, filename)
        filenames = os.listdir(subdirectory)
        if '__init__.py' in filenames:
            asdf
        os.walk

def insert_path_and_search_package_or_module(path, name):
    sys.path.insert(0, path)
    return search_package_or_module(name)

def search_package_or_module(name):
    import_module

def is_package(directory):
    return os.path.isfile(os.path.join(directory, '__init__.py'))

def is_identifier(name):
    return re.match('[A-Za-z_][A-Za-z0-9_]*', name) and not iskeyword(name)

def module_name_of(filename):
    if filename.endswith('.py'):
        base = filename[:-3]
        if is_identifier(base):
            return base
    return None