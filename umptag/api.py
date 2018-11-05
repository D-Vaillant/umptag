import shiny, tags

def find_database():
    """ Returns a filepath that points to the database.
    Returns None if not found. """
    raise NotImplementedError


def apply_tag(filepath, *args, **kwargs):
    """ Adds each tag and key=value tag to the given filepath. """
    raise NotImplementedError

def remove_tag(filepath, *args, **kwargs):
    """ Removes each tag and key=value tag from the given filepath. """
    raise NotImplementedError

def merge_tag(primary, secondary):
    """ Merges the secondary tag into the primary tag. """
    raise NotImplementedError


def show_tags(filepath):
    """ Lists the tags applied to filepath. """
    raise NotImplementedError


def show_files(*args, **kwargs):
    """ Lists the files with all of the applied tags. """
    raise NotImplementedError


def parse_tag_query(query):
    """ Given a string that has logical predicates, gets the tags queried.
    Supports `and`, `or`, parentheses, and negation. """
    raise NotImplementedError
