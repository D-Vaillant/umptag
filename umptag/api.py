import sqlite3
import functools
import os.path
import sys
from . import tags, fs, filetags
from . import database as db


DEFAULT_DB_NAME = ".umptag.db"


def initialize_conn(db_name=DEFAULT_DB_NAME, **kwargs):
    if db_name == ":memory:":
        db_loc = db_name
    else:
        db_loc = os.path.abspath(db_name)
    db.initialize_connection(db_loc, True)


def get_conn(db_name=DEFAULT_DB_NAME,
        fail_if_uninitialized=False, **kwargs):
    is_new = False
    if db_name != ":memory:":
        db_loc = db.find_database_filepath(db_name)
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
    return db.initialize_connection(db_loc, is_new)


def database_cognant(func, *args):
    """ Use with a function that takes an sqlite connection
    as the first argument. """
    # print("No database detected. Run `umptag init` first.")
    def out_func(*args, **kwargs):
        with get_conn(fail_if_uninitialized=True) as conn:
            out = func(conn, *args, **kwargs)
        return out
    return out_func


def apply_tag(conn, directory, name, key='', value=None):
    if value is None and key != '':
        key, value = '', key
    return filetags.tag_file(conn, directory, name, key, value)


def remove_tag(conn, directory, name, key='', value=None):
    """ Removes the tag or key=value tag from the given target. """
    if value is None and key != '':
        key, value = '', key
    return filetags.untag_file(conn, directory, name, key, value)


def remove_tags(conn, directory, name, *args, **kwargs):
    """ Removes multiple tags from a given file. """
    results = []
    for arg in args:
        results.append(remove_tag(conn, directory, name, arg))
    for (k, v) in kwargs.items():
        results.append(remove_tag(conn, directory, name, k, v))
    return 1 if any(results) else 0  # Exit message 1 if any fail.


def merge_tag(conn, primary_key='', primary_value=None,
                    secondary_key='', secondary_value=None):
    """ Merges the secondary tag into the primary tag. """
    if primary_key == secondary_key and primary_value == secondary_value:
        print("Can't merge a key with itself.")
        return 1
    if primary_value is None and primary_key != '':
        primary_key, primary_value = '', primary_key
    if secondary_value is None and secondary_key != '':
        secondary_key, secondary_value = '', secondary_key
    for (d, n) in filetags.files_of_tag(conn, secondary_key, secondary_value):
        filetags.tag_file(conn, d, n, primary_key, primary_value)
        remove_tag(conn, d, n, secondary_key, secondary_value)


def show_tags(conn, directory, name):
    """ Lists the tags applied to target. """
    raise NotImplementedError


def show_targets(conn, *args, **kwargs):
    """ Lists the targets with all of the applied tags. """
    raise NotImplementedError


def parse_tag_query(query):
    """ Given a string that has logical predicates, gets the tags queried.
    Supports `and`, `or`, parentheses, and negation. """
    raise NotImplementedError
