""" database.py
All of the details about setting up the database. """
import sqlite3
import os


schema = """
CREATE TABLE files (
    id integer PRIMARY KEY,
    directory text NOT NULL,
    name text NOT NULL,
    size integer,
    mod_time timestamp,
    is_dir boolean,
    CONSTRAINT path UNIQUE (directory, name)
);

CREATE TABLE tags (
    id integer PRIMARY KEY,
    key text DEFAULT '' NOT NULL,
    value text NOT NULL,
    CONSTRAINT tag_pk UNIQUE (key, value)
);

CREATE TABLE filetag_junction (
    file_id int, tag_id int,
    CONSTRAINT file_tag_pk PRIMARY KEY (file_id, tag_id),
    CONSTRAINT FK_files
    FOREIGN KEY (file_id) REFERENCES files (id),
    CONSTRAINT FK_tags
    FOREIGN KEY (tag_id) REFERENCES tags (id)
);"""


def find_database_filepath(db_name):
    """ Returns a filepath that points to the database.
    Returns None if not found. """
    # db = os.path.abspath(db_name)
    db = db_name
    if os.path.exists(db):
        return os.path.abspath(db)
    cur = os.path.abspath(os.path.curdir)
    cur, child = os.path.dirname(cur), cur  # go up the hierarchy
    while cur != child:  # because the parent dir of '/' is '/'
        db = os.path.join(cur, db_name)
        if os.path.exists(db):
            return os.path.abspath(db)
        cur, child = os.path.dirname(cur), cur  # go up the hierarchy
    return None


def _initialize_tables(c, destructive=True):
    """ Creates a new database, wiping out the previous one if needed. 
    c :: Cursor. """
    if destructive:
        c.executescript(';\n'.join(
                "DROP TABLE IF EXISTS %s" % table for table in
                ('files', 'tags', 'filetag_junction'))
                )
    #with open(schema, 'r') as sch:
    c.executescript(schema)


def initialize_connection(db_loc, new_db=False):
    conn = sqlite3.connect(db_loc,
            detect_types=sqlite3.PARSE_DECLTYPES)
    sqlite3.register_adapter(bool, int)
    sqlite3.register_converter("boolean", lambda v: bool(int(v)))
    if new_db:
        _initialize_tables(conn)
    return conn
