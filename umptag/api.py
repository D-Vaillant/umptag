import sqlite3
import functools
import os.path
import sys
from . import shiny, tags
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


@database_cognant
def apply_tag(conn, target, key='', value=None):
    # Why did I implement it this way? This seems stupid.
    # I'll just make it how I did add_tag.
    if value is None and key != '':
        key, value = '', key
    shiny.tag_file(conn, target, key, value)
    return

@database_cognant
def remove_tag(conn, target, key='', value=None):
    """ Removes each tag and key=value tag from the given target. """
    if value is None and key != '':
        key, value = '', key
    if (key, value) not in shiny.tags_of_file(conn, target):
        # No need!
        sys.exit(1)
    d, n = os.path.split(target)
    shiny._unrelate_tag_and_file(conn, d, n, key, value)
    if shiny.files_of_tag(conn, key, value) == []:
        tags._delete_tag(conn, key, value)
    if shiny.tags_of_file(conn, target) == []:
        shiny._delete_file(conn, d, n)
    # raise NotImplementedError


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
