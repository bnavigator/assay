"""Routines that understand Python importation."""

import sys
from importlib import import_module

def get_directory_of(name):
    """Return the base directory of a package, or None for a plain module."""
    module = import_module(name)
    return getattr(module, '__path__', None)

def import_modules(module_names):
    old = set(name for name, m in sys.modules.items() if m is not None)
    import_events = []
    for module_name in module_names:
        try:
            import_module(module_name)
        except ImportError:
            continue  # for modules like "pytz.threading"
        new = set(name for name, m in sys.modules.items() if m is not None)
        import_events.append((module_name, new - old))
        old = new
    return import_events

def list_module_paths():
    return [(name, module.__file__) for name, module in sys.modules.items()
            if (module is not None) and hasattr(module, '__file__')]

def improve_order(import_events):
    """Given an `import_events` list, return a new module import order.

    The new import order learns from the `import_events` of the last
    slate of imports, a sequence of tuples that reports what really
    happened as each module was imported.  The first element of each
    tuple should be the module that was asked for, and the second
    element be the set of modules that were imported as a result::

    [('zlib', {'zlib'}),
     ('zipfile', {'_io', 'binascii', 'grp', 'io', 'pwd', 'shutil', 'zipfile'}),
     ('_io', set()),
     ('binascii', set()),
     ...]

    The return value is a list of module names whose order is based on
    the order of the `import_events`.  The difference is that each
    module that caused several other modules to be imported as a
    side-effect, like `zipfile` shown above, is moved after all of those
    other modules in the new ordering.  New modules, that were not part
    of the previous ordering but are present in one of the side-effect
    sets, will be inserted into the import order just before the module
    that imports them.

    """
    imported_by = {b: a for a, bset in import_events for b in bset if a != b}
    already_appended = set()
    new_order = []

    def append(name):
        if name not in already_appended:
            already_appended.add(name)
            new_order.append(name)

    for module_name, names_imported in reversed(import_events):
        importer_name = imported_by.get(module_name)
        if importer_name is not None:
            append(importer_name)
        append(module_name)
        for name in sorted(names_imported, reverse=True):
            append(name)

    new_order.reverse()
    return new_order
