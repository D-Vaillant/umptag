import os, os.path
import unittest
from random import randint, choice
from . import DBTester
from .utilities import make_random_word, get_random_hierarchy
from .. import shiny, tags, api, files

class FilesystemTester(DBTester):
    def test_collect_files_flat(self):
        hier = get_random_hierarchy(structure=[(lambda: randint(2, 6), 0)])
        # Make a flat file hierarchy.
        fs_files = sorted(hier[0]+hier[1])  # Store those in here.
        fetched_files = sorted(files.collect_files())
        self.assertEqual(fs_files, fetched_files)

    def test_collect_files_nested(self):
        # Make a non-flat hierarchy.
        struct = ((lambda: randint(0, 5), lambda: randint(2, 3)),
                  (lambda: randint(1, 3), lambda: randint(1, 3)),
                  (lambda: randint(1, 5), 0))
        hier = get_random_hierarchy(structure=struct)
        fs_files = sorted(hier[0]+hier[1])  # Store those in here.
        fetched_files = sorted(files.collect_files())
        self.assertEqual(fs_files, fetched_files)


class APITester(DBTester):
    def test_find_database(self):
        struct = [(2, randint(2, 4)),
                  (lambda: randint(2, 3), 3),
                  (4, lambda: randint(1, 3))]
        hier = get_random_hierarchy(struct)
        db_loc = '.umptag.db'
        self.fs.create_file(db_loc)
        # Randomly enter a child directory.
        while True:
            dirs = [d for d in os.listdir(os.curdir) if os.path.isdir(d)]
            if dirs == []:
                break
            current_dir = choice(dirs)
            os.chdir(current_dir)
        self.assertEquals(db_loc, api.find_database())

    def test_find_database_none(self):
        # Make hierarchy with two dirs.
        # Put the database file in one.
        # Enter the other directory.
        hier = get_random_hierarchy(
        self.assertIs(api.find_database(), None)


