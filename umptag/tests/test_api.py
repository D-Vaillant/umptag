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


class DatabaseLocTester(DBTester):
    def test_find_database(self):
        struct = [(2, randint(2, 4)),
                  (lambda: randint(2, 3), 3),
                  (4, lambda: randint(1, 3))]
        hier = get_random_hierarchy(struct)
        self.make_hierarchy(hier)
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
        left, right = make_random_word(), make_random_word()
        self.fs.mkdir(left)
        self.fs.mkfile(left+os.sep+'.umptag')
        self.fs.mkdir(right)
        os.chdir(right)
        self.assertIs(api.find_database(), None)

class TaggingTester(DBTester):
    def setUp(self):
        super().setUp()
        self.filepaths = [make_random_word() for _ in range(randint(3, 6))]
        for fp in self.filepaths:
            self.fs.mkfile(fp)
        self.dirpaths = {make_random_word():list() for _ in range(randint(2, 4))}
        for dp in self.dirpaths:
            self.fs.mkdir(dp)
            for _ in range(randint(0, 2)):
                stem = make_random_word()
                self.fs.mkfile(dp+os.sep+stem)
                self.dirpaths[dp].append(stem)

    def test_apply_tag(self):
        pass

