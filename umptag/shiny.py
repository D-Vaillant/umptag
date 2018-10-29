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
                   mod_time real,
                   is_dir boolean)""")

    c.execute("""CREATE TABLE tags
                  (id integer primary key,
                   key text DEFAULT '',
                   value text NOT NULL)""")

    c.execute("""CREATE TABLE files_tags_junction
                  (file_id int, tag_id int,
                   CONSTRAINT file_tag_pk PRIMARY KEY (file_id, tag_id),
                   CONSTRAINT FK_files
                        FOREIGN KEY (file_id) REFERENCES files (id),
                   CONSTRAINT FK_tags
                        FOREIGN KEY (tag_id) REFERENCES tags (id)
                  )""")


def get_file(c, path):
    return c.execute("""SELECT directory, name, size, mod_time, is_dir
                     FROM files WHERE directory = ? AND name = ?""",
                     os.path.split(path))


def get_tag(c, key, value):
    # In the backend we treat None as '' for key.
    # Possibly doable with pure SQL but right now? Eh.
    if key is None:
        key = ''
    return c.execute("SELECT key, value FROM tags WHERE key = ? AND value = ?",
                     (key, value))
    

def add_file(c, path):
    """ Adds a file. Avoids duplicates based on the filepath.
    c :: Cursor. """
    if not os.path.exists(path):
        raise FileNotFoundError()
    file = get_file(c, path).fetchone()
    if file is not None:
        # We're trying to add a duplicate!
        logging.warning("Tried to add a duplicate file.")
        pass
        # return file
    directory, name = os.path.split(path)
    size = round(os.stat(path).st_size, 6)
    mod_time = os.stat(path).st_mtime
    is_dir = os.path.isdir(path)
    c.execute("""INSERT INTO files (directory, name, size, mod_time, is_dir)
                 VALUES (?,?,?,?,?)""",
              (directory, name, size, mod_time, is_dir))
    return


def add_tag(c, key, value):
    if key is None:
        key = ''
    c.execute("INSERT INTO tags (key, value) VALUES (?,?)", (key, value))


def tag_file(c, path, key="", value=""):
    tag = get_tag(c, key, value)



