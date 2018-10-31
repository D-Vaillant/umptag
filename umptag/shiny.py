from datetime import datetime
import sqlite3
import logging
import os, os.path


def initialize_tables(c):
    """ Creates our tables.
    c :: Cursor. """
    c.execute("""CREATE TABLE files
                  (id integer primary key,
                   directory text NOT NULL,
                   name text NOT NULL,
                   size integer,
                   mod_time timestamp,
                   is_dir boolean,
                   CONSTRAINT path UNIQUE (directory, name))""")

    c.execute("""CREATE TABLE tags
                  (id integer primary key,
                   key text DEFAULT '',
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

def _column_safety(c, table, cols='*'):
    if table not in ['files', 'tags']:
        raise sqlite3.IntegrityError
    table_columns = [_[1] for _ in c.execute(f"PRAGMA table_info({table})")]
    if cols == '*' or all(col in table_columns for col in cols):
        return
    else:
        raise sqlite3.IntegrityError

# Mark these as internal when I get to that point.
# File functions.
def get_file(c, path, cols=('directory', 'name')):
    """ All values: ("directory", "name", "size", "mod_time", "is_dir")
    `cols` is UNSAFE. """
    # WARNING: Yeah, I'm using the string input thing.
    #   I wish I could have figured out a better way.
    return c.execute(f"""SELECT {', '.join(cols)} FROM files WHERE
            directory = ? AND name = ?""", os.path.split(path)).fetchone()

def get_file_id(c, path):
    """ Shortcut method. """
    return get_file(c, path, cols=('id',))[0]

def get_file_from_id(c, id, cols=('directory', 'name')):
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

def get_or_add_file(c, path, **kw):
    try:
        add_file(c, path)
    except sqlite3.IntegrityError:
        pass
    return get_file(c, path)


# Tag functions.
def add_tag(c, key, value):
    if key is None:
        key = ''
    c.execute("INSERT INTO tags (key, value) VALUES (?,?)", (key, value))

def get_tag(c, key, value, cols=("key", "value")):
    # In the backend we treat None as '' for key.
    # Possibly doable with pure SQL but right now? Eh.
    if key is None:
        key = ''
    return c.execute(f"SELECT {', '.join(cols)} FROM tags WHERE key = ? AND value = ?",
                     (key, value)).fetchone()

def get_tag_id(c, key, value):
    return get_tag(c, key, value, cols=("id",))[0]

def get_tag_from_id(c, id, cols=('key', 'value')):
    return c.execute(f"SELECT {', '.join(cols)} FROM tags WHERE id = ?", (id,)).fetchone()

def get_or_add_tag(c, key, value, **kw):
    try:
        add_tag(c, key, value)
    except sqlite3.IntegrityError:
        pass
    return get_tag(c, key, value, **kw)


# filetag_junction functions.
def relate_tag_and_file(c, path, key, value):
    c.execute("""INSERT INTO filetag_junction (file_id, tag_id) SELECT
            (SELECT id FROM files WHERE directory = ? AND name = ?) AS file_id,
            (SELECT id FROM tags WHERE key = ? AND value = ?) AS tag_id""",
            (*os.path.split(path), key, value))

def tags_of_file(c, path, cols=('key', 'value')):
#file_id = get_file(c, path, cols=('id,')).fetchone()
    res = c.execute(f"""SELECT {', '.join(cols)} FROM filetag_junction J
            INNER JOIN tags ON tags.id = J.tag_id
            INNER JOIN files ON files.id = J.file_id
            WHERE files.directory = ? AND files.name = ?""",
            os.path.split(path))
    return res.fetchall()
# return [get_tag_from_id(c, tag_id, **kwargs) for tag_id in tag_ids]

def files_of_tag(c, key, value, cols=('directory', 'name')):
    res = c.execute(f"""SELECT {', '.join(cols)} FROM filetag_junction J
            INNER JOIN files on files.id = J.file_id
            INNER JOIN tags ON tags.id = J.tag_id
            WHERE tags.key = ? AND tags.value = ?""",
            (key, value))
    return res.fetchall()

# Actual usage!
def tag_file(c, path, key="", value=""):
    filepath = os.path.join(get_or_add_file(c, path))
    tag = get_or_add_tag(c, key, value)
    relate_tag_and_file(filepath, *tag)

"""SELECT {', '.join(('files.'+col for col in cols)} from files INNER JOIN filetag_junction ON file.id = filetag_junction.file_id WHERE filetag_junction.tag_id = N"""
"""SELECT files.id, files.filepath from (INNER JOIN on tags.id = junction.tag_id, INNER JOIN filesfONiles"""
"""SELECT {', '.join(('files.'+col for col in cols)} from files INNER JOIN filetag_junction ON file.id = filetag_junction.file_id WHERE filetag_junction.tag_id = N"""
