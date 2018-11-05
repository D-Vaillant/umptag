import logging
from typing import Tuple, Union, List
from sqlite3 import (Cursor,  # Used for typechecking
                     OperationalError,
                     IntegrityError,
                     DatabaseError)


def tag_safety(cols: Union[str, List[str]]) -> None:
    """ cols can be '*' (all columns) or a list of strings.
    If '*', we're just querying all columns so that's fine.
    If it's a list of strings, we make sure that those strings are all columns.
        If any of them aren't (e.g. if one of them is an SQL injection) we
        raise an exception.
    """
    table_columns = ['id', 'key', 'value']  # Don't expect this to change fast
    if cols == '*':
        return
    for col in cols:
        if col not in table_columns:
            raise OperationalError("Tried to query an invalid column: '%s'" % col)
    return


def add_tag(c: Cursor, key: str, value: str):
    c.execute("INSERT INTO tags (key, value) VALUES (?,?)", (key, value))


def _get_tag(c, key, value, cols=("key", "value")):
    # Deprecated right now.
    raise NotImplementedError("_get_tag is deprecated. Do not use.")
    return c.execute("SELECT %s FROM tags WHERE key = ? AND value = ?" % (', '.join(cols)),
                     (key, value)).fetchone()


def get_tag(c, key, value):
    """ If the tag exists, we return (key, value); otherwise we return None.
    A weird function but necessary for some error handling. """
    cmd_str = "SELECT key, value FROM tags WHERE key = ? AND value = ? LIMIT 1"
    return c.execute(cmd_str, (key, value)).fetchone()
    # This is an implementation that uses EXISTS instead. Never tested this.
    #   Probably doesn't work because I didn't try testing it!
    """
    cmd_str = "SELECT EXISTS (SELECT 1 FROM tags WHERE key = ? AND value = ? LIMIT 1)",
    exists = c.execute(cmd_str, (key, value)).fetchone()
    return (key, value) if exists else None
    """


def tag_kv_to_id(c, key, value):
    """ Takes a key and a value and returns the ID (if it exists)."""
    out = c.execute("SELECT id FROM tags WHERE key = ? AND value = ?",
                     (key, value)).fetchone()
    return out if out is None else out[0]


def tag_id_to_kv(c, id_):
    """ Takes an i and returns the key-value pair (if it exists)."""
    return c.execute("SELECT key, value from tags WHERE id = ?", (id_,)).fetchone()


def get_or_add_tag(c, key, value):
    """ Returns a (key, value) pair that's in the database.
    Tries to create it and then gets it. Fails if the tag isn't in the
    database even after trying to create it. """
    try:
        add_tag(c, key, value)
    except IntegrityError:
        # Hopefully it's because of duplicates.
        pass
    # Now we try to return our (possibly new) tag. 
    tag = get_tag(c, key, value)
    # Possibly: Have it return None, foist the error checking to the caller.
    if tag is None:
        # It was not because of duplicates.
        raise OperationalError("Tried to add an invalid tag: "
                               "(key='%s', value='%s')" % (key, value))
    return tag
