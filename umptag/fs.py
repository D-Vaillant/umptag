from typing import Union
from datetime import datetime
import os
import sqlite3

def collect_files(root_dir=os.curdir, filter_=lambda x: True):
    # This is probably just going to wrap os.walk.
    os.walk(root_dir)

def _get_file_properties(c, directory, name, cols=('directory', 'name')) -> Union[tuple, None]:
    """ All values: ("directory", "name", "size", "mod_time", "is_dir")
    `cols` is UNSAFE. """
    # WARNING: Yeah, I'm using the string input thing.
    #   I wish I could have figured out a better way.
    return c.execute(f"""SELECT {', '.join(cols)} FROM files WHERE
            directory = ? AND name = ? LIMIT 1""", (directory, name)).fetchone()

def _get_file_from_id(c, id_, cols=('directory', 'name')):
    return c.execute(f"""SELECT {', '.join(cols)} FROM files WHERE
            id = ?""", (id_,)).fetchone()

# Possibly public.
def _get_file(c, directory, name):
    # TODO Take a look at what exactly I'm intending here.
    """ Returns (path,). Weird.
    Can be replaced with a _file_exists thing. """
    return _get_file_properties(c, directory, name, cols=('directory', 'name'))

def _get_file_id(c, directory, name) -> Union[int, None]:
    """ Returns the id of the file corresponding to the path. """
    try:
        return _get_file_properties(c, directory, name, cols=('id',))[0]
    except IndexError:
        return None

def _add_file(c, directory, name):
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

def delete_file(c, directory, name):
    cmd_str = "DELETE FROM files WHERE directory = ? AND name = ?"
    c.execute(cmd_str, (directory, name))

def get_or_add_file(c, directory, name, **kw) -> Union[tuple, None]:
    try:
        _add_file(c, directory, name)
    except sqlite3.IntegrityError:
        pass
    return _get_file(c, directory, name)
    #return c.execute("SELECT directory, name FROM files WHERE directory = ? AND name = ? LIMIT 1").fetchone()

