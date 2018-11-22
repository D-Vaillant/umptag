import logging
from typing import Tuple, Union, List
from sqlite3 import (Cursor,  # Used for typechecking
                     OperationalError,
                     IntegrityError,
                     DatabaseError)


# def tag_safety(cols: Union[str, List[str]]) -> None:
#     """ cols can be '*' (all columns) or a list of strings.
#     If '*', we're just querying all columns so that's fine.
#     If it's a list of strings, we make sure that those strings are all columns.
#         If any of them aren't (e.g. if one of them is an SQL injection) we
#         raise an exception.
#     """
#     table_columns = ['id', 'key', 'value']  # Don't expect this to change fast
#     if cols == '*':
#         return
#     for col in cols:
#         if col not in table_columns:
#             raise OperationalError("Tried to query an invalid column: '%s'" % col)
#     return


# Just the tag stuff.
def _add_tag(c: Cursor, key: str, value: str):
    c.execute("INSERT INTO tags (key, value) VALUES (?,?)", (key, value))


def _exists_tag(c: Cursor, key: str, value: str) -> bool:
    """ Returns True if the (key, value) pair is in the database. """
    cmd_str = "SELECT key, value FROM tags WHERE key = ? AND value = ? LIMIT 1"
    return c.execute(cmd_str, (key, value)).fetchone() is not None
    """
    cmd_str = "SELECT EXISTS (SELECT 1 FROM tags WHERE key = ? AND value = ? LIMIT 1)",
    exists = c.execute(cmd_str, (key, value)).fetchone()
    return (key, value) if exists else None
    """

def _delete_tag(c: Cursor, key: str, value: str) -> bool:
    cmd_str = "DELETE FROM tags WHERE key = ? AND value = ?"
    c.execute(cmd_str, (key, value))

def get_or_add_tag(c, key, value):
    """ If the key,value pair isn't in the database, adds it.
    Returns (key, value). """
    if not _exists_tag(c, key, value):
        _add_tag(c, key, value)
    return (key, value)
