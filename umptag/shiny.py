from datetime import datetime
import tags
import sqlite3
import logging
import os, os.path


def initialize_tables(c):
    """ Creates our tables.
    c :: Cursor. """
    c.execute("""CREATE TABLE files
                  (id integer PRIMARY KEY,
                   directory text NOT NULL,
                   name text NOT NULL,
                   size integer,
                   mod_time timestamp,
                   is_dir boolean,
                   CONSTRAINT path UNIQUE (directory, name))""")

    c.execute("""CREATE TABLE tags
                  (id integer PRIMARY KEY,
                   key text DEFAULT '' NOT NULL,
                   value text NOT NULL,
                   CONSTRAINT tag_pk UNIQUE (key, value))""")

    c.execute("""CREATE TABLE filetag_junction
                  (file_id int, tag_id int,
                   CONSTRAINT file_tag_pk PRIMARY KEY (file_id, tag_id),
                   CONSTRAINT FK_files
                        FOREIGN KEY (file_id) REFERENCES files (id),
                   CONSTRAINT FK_tags
                        FOREIGN KEY (tag_id) REFERENCES tags (id)
                  )""")

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
@fs
def _get_file(c, path, cols=('directory', 'name')):
    """ All values: ("directory", "name", "size", "mod_time", "is_dir")
    `cols` is UNSAFE. """
    # WARNING: Yeah, I'm using the string input thing.
    #   I wish I could have figured out a better way.
    return c.execute(f"""SELECT {', '.join(cols)} FROM files WHERE
            directory = ? AND name = ?""", os.path.split(path)).fetchone()

def get_file(c, path):
    return _get_file(c, path)

def get_file_id(c, path):
    """ Shortcut method. """
    return _get_file(c, path, cols=('id',))[0]

def _get_file_from_id(c, id, cols=('directory', 'name')):
    return c.execute(f"""SELECT {', '.join(cols)} FROM files WHERE
            id = ?""", (id,)).fetchone()

def add_file(c, path):
    """ Adds a file. Raises an exception if it already exists.
    c :: Cursor. """
    directory, name = os.path.split(path)
    size = round(os.stat(path).st_size, 6)
    mod_time = datetime.fromtimestamp(os.stat(path).st_mtime)
    is_dir = os.path.isdir(path)
    c.execute("""INSERT INTO files (directory, name, size, mod_time, is_dir)
                 VALUES (?,?,?,?,?)""",
              (directory, name, size, mod_time, is_dir))
    return

def _get_or_add_file(c, path, **kw):
    try:
        add_file(c, path)
    except sqlite3.IntegrityError:
        pass
    return _get_file(c, path)

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
    return res.fetchall()

def files_of_tag(c, key, value, cols=('directory', 'name')):
    res = c.execute(f"""SELECT {', '.join(cols)} FROM filetag_junction J
            INNER JOIN files on files.id = J.file_id
            INNER JOIN tags ON tags.id = J.tag_id
            WHERE tags.key = ? AND tags.value = ?""",
            (key, value))
    return res.fetchall()

# Actual usage!
def tag_file(c, path, key="", value=""):
    filepath = os.path.join(_get_or_add_file(c, path))
    tags.add_tag(c, key, value)
    try:
        relate_tag_and_file(filepath, key, value)
    except sqlite3.IntegrityError:
        logging.info("Tried to add duplicate tag.")

"""SELECT {', '.join(('files.'+col for col in cols)} from files INNER JOIN filetag_junction ON file.id = filetag_junction.file_id WHERE filetag_junction.tag_id = N"""
"""SELECT files.id, files.filepath from (INNER JOIN on tags.id = junction.tag_id, INNER JOIN filesfONiles"""
"""SELECT {', '.join(('files.'+col for col in cols)} from files INNER JOIN filetag_junction ON file.id = filetag_junction.file_id WHERE filetag_junction.tag_id = N"""
