from typing import Union
from datetime import datetime
from . import tags
import sqlite3
import logging
import os, os.path

# Schema
## TODO: Set it up so I can read this from a file.

# Some safety stuff we're not really using right now.
""" A preliminary implementation.
Basically: we'll put all of our Cursor-aware methods into classes,
decorated as such. We subclass those classes when we get our Connection
and run `make_decorator` (name pending) to get the decorator that we use on
our new subclasses.""" 
def db_wrap_decorator(func_dec):
    def class_decorator(cls):
        for attr_name in dir(cls):
            if attr_name.startswith('__'):  # Skip magic methods
                continue
            attr_value = getattr(cls, attr_name)
            if hasattr(attr_value, '__call__'):  # Check if attr is function
                setattr(cls, attr_name, func_dec(attr_value))
        return cls
    return class_decorator

def make_decorator(conn):
    @db_wrap_decorator
    def func_dec(func):
        def out_func(*args, **kwargs):
            return func(conn, *args, **kwargs)
        out_func.__name__ = func.__name__
        return out_func
    return func_dec

# func_dec = make_decorator(conn)

""" Alternatively, we can make a class that imports a lot of these things
and have it implement wrappers around them that automatically plug in the
Connection (declared as part of the instantiation.)
So for ConnectionTag, we have self.conn and then:
    def add_tag(self, *arg, **kw):
        tags.add_tag(self.conn, *arg, **kw)
Maybe it would be better to have a Tag class and a ConnectedTag class.
Or a Connected class which includes all of our public methods we can use.
"""

my_tables = ['files', 'tags']

def _column_safety(c, table, cols='*'):
    if table not in my_tables:
        raise sqlite3.IntegrityError
    table_columns = [_[1] for _ in c.execute(f"PRAGMA table_info({table})")]
    if cols == '*' or all(col in table_columns for col in cols):
        return
    else:
        raise sqlite3.OperationalError

def file_safety(cols):
    # I coded a way to dynamically do this above, but it seems silly to query
    # the database each time if my columns aren't going to change that much.
    table_columns = ['id', 'directory', 'name', 'size', 'mod_time', 'is_dir']
    if cols == '*' or all(col in table_columns for col in cols):
        return
    else:
        raise sqlite3.OperationalError

def fs(func, *args, **kwargs):
    def new_func(*args, **kwargs):
        try:
            file_safety(kwargs['cols'])
        except KeyError:  # We're using the default argument, which is Safe.
            pass
        return func(*args, **kwargs)
    return new_func



# File functions.
# @fs
def _get_file(c, directory, name, cols=('directory', 'name')) -> Union[tuple, None]:
    """ All values: ("directory", "name", "size", "mod_time", "is_dir")
    `cols` is UNSAFE. """
    # WARNING: Yeah, I'm using the string input thing.
    #   I wish I could have figured out a better way.
    return c.execute(f"""SELECT {', '.join(cols)} FROM files WHERE
            directory = ? AND name = ? LIMIT 1""", (directory, name)).fetchone()

def get_file(c, directory, name):
    # TODO Take a look at what exactly I'm intending here.
    """ Returns (path,). Weird. """
    return _get_file(c, directory, name, cols=('directory', 'name'))

def get_file_id(c, directory, name) -> Union[int, None]:
    """ Returns the id of the file corresponding to the path. """
    try:
        return _get_file(c, directory, name, cols=('id',))[0]
    except IndexError:
        return None

def _get_file_from_id(c, id_, cols=('directory', 'name')):
    return c.execute(f"""SELECT {', '.join(cols)} FROM files WHERE
            id = ?""", (id_,)).fetchone()

def add_file(c, directory, name):
    """ Adds a file. Raises an IntegrityError if it already exists.
    c :: Cursor. """
    path = os.path.join(directory, name)
    size = round(os.stat(path).st_size, 6)
    mod_time = datetime.fromtimestamp(os.stat(path).st_mtime)
    is_dir = os.path.isdir(path)
    c.execute("""INSERT INTO files (directory, name, size, mod_time, is_dir)
                 VALUES (?,?,?,?,?)""",
              (directory, name, size, mod_time, is_dir))
    return

def get_or_add_file(c, directory, name, **kw) -> Union[tuple, None]:
    try:
        add_file(c, directory, name)
    except sqlite3.IntegrityError:
        pass
    return get_file(c, directory, name)
    #return c.execute("SELECT directory, name FROM files WHERE directory = ? AND name = ? LIMIT 1").fetchone()

# Tag functions.
# filetag_junction functions.
def relate_tag_and_file(c, path, key, value):
    c.execute("""INSERT INTO filetag_junction (file_id, tag_id) SELECT
            (SELECT id FROM files WHERE directory = ? AND name = ?) AS file_id,
            (SELECT id FROM tags WHERE key = ? AND value = ?) AS tag_id""",
            (*os.path.split(path), key, value))

def tags_of_file(c, path, cols=('key', 'value')):
    res = c.execute(f"""SELECT {', '.join(cols)} FROM filetag_junction J
            INNER JOIN tags ON tags.id = J.tag_id
            INNER JOIN files ON files.id = J.file_id
            WHERE files.directory = ? AND files.name = ?""",
            os.path.split(path))
    # res = [(r[1] if r[0] == '' else r) for r in res.fetchall()]
    return res.fetchall()

def files_of_tag(c, key='', value=None, cols=('directory', 'name')):
    if value is None and key != '':
        key, value = '', key
    res = c.execute(f"""SELECT {', '.join(cols)} FROM filetag_junction J
            INNER JOIN files on files.id = J.file_id
            INNER JOIN tags ON tags.id = J.tag_id
            WHERE tags.key = ? AND tags.value = ?""",
            (key, value))
    return res.fetchall()

# Actual usage!
def tag_file(c, path, key="", value=None):
    d, n = os.path.split(path)
    if value is None and key != '':
        key, value = '', key
    filepath = os.path.join(*get_or_add_file(c, d, n))
    tags.get_or_add_tag(c, key, value)
    try:
        relate_tag_and_file(c, filepath, key, value)
    except sqlite3.IntegrityError:
        logging.info("Tried to add duplicate tag.")

"""SELECT {', '.join(('files.'+col for col in cols)} from files INNER JOIN filetag_junction ON file.id = filetag_junction.file_id WHERE filetag_junction.tag_id = N"""
"""SELECT files.id, files.filepath from (INNER JOIN on tags.id = junction.tag_id, INNER JOIN filesfONiles"""
"""SELECT {', '.join(('files.'+col for col in cols)} from files INNER JOIN filetag_junction ON file.id = filetag_junction.file_id WHERE filetag_junction.tag_id = N"""
