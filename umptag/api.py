import sqlite3
import functools
import os.path
import sys
from typing import List
from . import tags, fs, filetags
from . import database as db


DEFAULT_DB_NAME = db.DEFAULT_DB_NAME


class TagQuery:
    def __init__(self, conn=None, key='', value=None):
        if value is None and key != '':
            key, value = '', key
        self.key, self.value = key, value
        if conn is not None:
            self.bind(conn)
        else:
            self._conn = None

    @property
    def conn(self):
        if self._conn is not None:
            return self._conn
        else:
            raise AttributeError(
                    "No connection specified. "
                    "Call {}.bind(conn) first.".format(self.__name__))

    @property
    def files(self):
        return filetags.files_of_tag(self.conn, self.key, self.value)

    def bind(self, c):
        # check if c is a conn
        self._conn = c
        return

    def __add__(self, query):
        """ Uses the connection of the first non-None TagQuery. """


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
    for (d, n) in TagQuery(conn, secondary_key, secondary_value).files:
    # for (d, n) in filetags.files_of_tag(conn, secondary_key, secondary_value):
        filetags.tag_file(conn, d, n, primary_key, primary_value)
        remove_tag(conn, d, n, secondary_key, secondary_value)


def show_tags(conn, directory, name) -> List[str]:
    """ Lists the tags applied to file. """
    raise NotImplementedError


def show_files(conn, *args, **kwargs) -> List[str]:
    """ Lists the targets with all of the applied tags. """
    raise NotImplementedError


# God, this is just... not good, right?
def parse_tag_query(query_str):
    """ Given a string that has logical predicates, returns something to query.
    Supports `and`, `or`, parentheses, and negation. """
    """ Not doing parens or OR for now, though. """
    # So, we want to use AND, OR, and NOT sql predicates.
    # To do this, we need to generate conditions from the given tags.
    # SELECT foo, bar FROM files WHERE <map string to a chain of conditions>
    reg_str = "[& |]?(^[& |]+)[& |]?"
    # queries = re.findall(reg_str, query_str)
    queries = query_str.split()
    for index, query in enumerate(queries):
        if '=' in query:
            try:
                k, v = query.split()
            except ValueError:  # Empty value -> Without that key.
                k, v = query.strip('='), None
            queries[index] = (k, v)
        else:
            queries[index] = ('', query)
    conditions = []
    for (k, v) in queries:
        if v is not None and v[0] == '-':
            conditions.append(("(key=? AND NOT value=?)", (k, v)))
        else:
            conditions.append(("(key=? AND value=?)", (k, v)))

def run_tag_query(query_tuple):
    raise NotImplementedError
