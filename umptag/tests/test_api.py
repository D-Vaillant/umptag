import os, os.path
from shutil import rmtree
import unittest
import sqlite3
from random import randint, choice
from pyfakefs.fake_filesystem_unittest import TestCase, Patcher
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
    def test_find_database_filepath(self):
        struct = [(2, randint(2, 4)),
                  (lambda: randint(2, 3), 3),
                  (4, lambda: randint(1, 3))]
        files, folders = get_random_hierarchy(struct)
        for f in files:
            self.fs.create_file(f)
        for f in folders:
            try:
                self.fs.create_dir(f)
            except FileExistsError:
                pass
        # self.make_hierarchy(hier)
        db_loc = api.DEFAULT_DB_NAME
        db_file = self.fs.create_file(db_loc)
        # Randomly enter a child directory.
        while True:
            dirs = [d for d in os.listdir(os.curdir) if os.path.isdir(d)]
            if dirs == []:
                break
            current_dir = choice(dirs)
            os.chdir(current_dir)
        self.assertEquals(db_file.path, api.find_database_filepath(api.DEFAULT_DB_NAME))

    def test_find_database_none(self):
        left, right = make_random_word(), make_random_word()
        self.fs.create_dir(left)
        self.fs.create_file(left+os.sep+api.DEFAULT_DB_NAME)
        self.fs.create_dir(right)
        os.chdir(right)
        self.assertIs(api.find_database_filepath(api.DEFAULT_DB_NAME), None)


class InitializationTester(unittest.TestCase):
    def setUp(self):
        #self.tmp_directory = os.path.abspath('.ump_tmp')
        self.start = os.getcwd()
        self.tmpdir = '.ump_tmp'
        try:
            os.mkdir(self.tmpdir)
        except FileExistsError:
            # self.tearDown()
            unittest.skip("Folder already existed; tearing down and skipping.")
        os.chdir(self.tmpdir)

    def test_new_tables(self):
        pass

    def test_init_connection(self):
        pass
        shiny.initialize_connection(':memory:', new_db=True)
        shiny.initialize_connection('.umptag.db', new_db=True)
        # Test some properties of the connection.

    def test_get_conn(self):
        # c = api.get_conn(in_memory=True)
        print(os.getcwd())
        c_1 = api.get_conn()
        c_2 = api.get_conn(api.DEFAULT_DB_NAME)
        c_3 = api.get_conn(':memory:')
        # Test some properties of the connection.

    def test_get_conn_failure(self):
        with self.assertRaises(sqlite3.DatabaseError):
            api.get_conn(fail_if_uninitialized=True)

    def test_get_conn_altname(self):
        c = api.get_conn('foobar')

    def tearDown(self):
        os.chdir(self.start)
        rmtree(self.tmpdir)


class TaggingTester(TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self.filepaths = [make_random_word() for _ in range(randint(3, 6))]
        for fp in self.filepaths:
            self.fs.create_file(fp)
        self.dirpaths = {make_random_word():list() for _ in range(randint(2, 4))}
        for dp in self.dirpaths:
            self.fs.create_dir(dp)
            for _ in range(randint(0, 2)):
                stem = make_random_word()
                self.fs.create_file(dp+os.sep+stem)
                self.dirpaths[dp].append(stem)

    def test_apply_tag(self):
        pass


