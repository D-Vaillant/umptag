import sqlite3
import functools
import os.path
from . import shiny, tags


DEFAULT_DB_NAME = ".umptag.db"


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


def initialize_conn(db_name=DEFAULT_DB_NAME, **kwargs):
    if db_name == ":memory:":
        db_loc = db_name
    else:
        db_loc = os.path.abspath(db_name)
    shiny.initialize_connection(db_loc, True)


def get_conn(db_name=DEFAULT_DB_NAME,
        fail_if_uninitialized=False, **kwargs):
    is_new = False
    if db_name != ":memory:":
        db_loc = find_database_filepath(db_name)
        # We didn't find a database file so we're going to make one.
        if db_loc is None:
            if fail_if_uninitialized:  # Fail loudly.
                raise sqlite3.DatabaseError("No database initialized.")
            db_loc = os.path.abspath(db_name)
            is_new = True
        else:
            assert os.path.exists(db_loc)
    else:
        db_loc = ":memory:"
    return shiny.initialize_connection(db_loc, is_new)


def database_cognant(func, *args):
    # print("No database detected. Run `umptag init` first.")
    def out_func(*args):
        with get_conn(fail_if_uninitialized=True) as conn:
            out = func(conn, *args)
        return out
    return out_func


@database_cognant
def apply_tag(conn, target, *args, **kwargs):
    """ Adds each tag and key=value tag to the given target. """
    for value in args:
        shiny.tag_file(conn, target, value)
        # shiny.relate_tag_and_file(conn, target, '', arg)
    for key, value in kwargs.items():
        shiny.tag_file(conn, target, key, value)
        # shiny.relate_tag_and_file(conn, target, key, value)


@database_cognant
def remove_tag(conn, target, *args, **kwargs):
    """ Removes each tag and key=value tag from the given target. """
    raise NotImplementedError


@database_cognant
def merge_tag(conn, primary, secondary):
    """ Merges the secondary tag into the primary tag. """
    raise NotImplementedError


@database_cognant
def show_tags(conn, target):
    """ Lists the tags applied to target. """
    raise NotImplementedError


@database_cognant
def show_targets(conn, *args, **kwargs):
    """ Lists the targets with all of the applied tags. """
    raise NotImplementedError


def parse_tag_query(query):
    """ Given a string that has logical predicates, gets the tags queried.
    Supports `and`, `or`, parentheses, and negation. """
    raise NotImplementedError
