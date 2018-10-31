import datetime
import sqlite3
import os
import os.path
import unittest
from random import uniform, randrange
from pyfakefs.fake_filesystem_unittest import TestCase
# My modules.
import shiny
from test import DBTester

class FileTester(DBTester):
    def setUp(self):
        super().setUp()


class TestFileFunctions(DBTester):
    def setUp(self):
        super().setUp()
        self.fake_filepath = "test/file.txt"
        self.fake_dirpath = "dog"
        self.fake_file = self.fs.create_file(self.fake_filepath)
        self.fake_dir = self.fs.create_dir(self.fake_dirpath)
    
    # Test `_get_file`.
    def test_getter_variation(self):
        for (fp, file) in ((self.fake_filepath, self.fake_file),
                           (self.fake_dirpath, self.fake_dir)):
            with self.subTest(fp=fp, file=file):
                c = self.conn.cursor()
                # Setting up our attributes
                rand_size = randrange(1500, 30000)
                rand_time = round(uniform(6*(10**8), 9*(10**9)), 4)
                # Setting file attributes
                file.st_size = rand_size
                file.st_mtime = rand_time
                rand_time = datetime.datetime.fromtimestamp(rand_time)
                # And then we add it and do a variety of tests
                shiny.add_file(c, fp)
                # We use this to permute.
                d, n = os.path.split(fp)
                all_cols = {"directory": d, "name": n, "mod_time": rand_time,
                        "size": rand_size, "is_dir": os.path.isdir(fp)}
                vars = [('directory', 'mod_time', 'size'),
                        ('name', 'mod_time', 'size'),
                        ('is_dir', 'size'),
                        ('name',),
                        ('directory', 'size')]
                for var in vars:
                    with self.subTest(var=var):
                        self.assertEqual(
                            tuple(all_cols.get(k) for k in var),
                            shiny._get_file(self.conn.cursor(),
                                            fp, cols=var)
                            )

    def test_get_safety(self):
        with self.assertRaises(sqlite3.OperationalError):
            shiny._get_file(self.conn, 'foo', cols=('ashdoaho', 'name'))

    # Test `_get_file_from_id`.
    def test_get_file_from_id(self):
        pass

    # Test `add_file`.
    def test_add_nonexistent_file(self):
        file_path = "djowiajod.txt"
        # Test adding a non-existent file.
        with self.assertRaises(FileNotFoundError):
            shiny.add_file(self.conn.cursor(), file_path)

    def test_only_one_file_added(self):
        for fp in (self.fake_filepath, self.fake_dirpath):
            c = self.conn.cursor()
            shiny.add_file(c, fp)
            results = c.execute("SELECT * FROM files WHERE directory = ? AND name = ?",
                    os.path.split(fp)).fetchall()
            self.assertGreater(len(results), 0)  # Make sure we get at least one match.
            self.assertEqual(len(results), 1)  # Make sure we get at most one match.

    def test_adding_duplicate_exception(self):
        for fp in (self.fake_filepath, self.fake_dirpath):
            c = self.conn.cursor()
            shiny.add_file(c, fp)
            with self.assertRaises(sqlite3.IntegrityError):
                shiny.add_file(c, fp)

    def test_correct_metadata(self):
        for (fp, file) in ((self.fake_filepath, self.fake_file), (self.fake_dirpath, self.fake_dir)):
            with self.subTest(fp=fp, file=file):
                # Filesize
                rand_size = randrange(1500, 30000)
                file.st_size = rand_size
                # Modified Time
                rand_time = round(uniform(1 * (6**8), 1 * (9**10)), 4)
                file.st_mtime = rand_time
                rand_time = datetime.datetime.fromtimestamp(rand_time)
                shiny.add_file(self.conn.cursor(), fp)
                results = self.conn.cursor().execute(
                        "SELECT mod_time, size, is_dir FROM files WHERE directory = ? AND name = ?",
                        os.path.split(fp)).fetchone()
                self.assertEqual((rand_time, rand_size, os.path.isdir(fp)), results)

    # Test `get_or_add_file`.
    def test_file_getoradd_adding(self):
        for fp in (self.fake_filepath, self.fake_dirpath):
            with self.subTest(fp=fp):
                c = self.conn.cursor()
                got = shiny._get_or_add_file(self.conn.cursor(), fp)
                # Getting the directory and name. Fragile.
                got = got[0:2]
                c = self.conn.cursor()
                query = c.execute(
                    """SELECT directory, name FROM files WHERE
                    directory = ? AND
                    name = ?""", os.path.split(fp)).fetchall()
                self.assertEqual(1, len(query))
                self.assertEqual(got, query.pop())

    def test_file_getoradd_getting(self):
        for fp in (self.fake_filepath, self.fake_dirpath):
            with self.subTest(fp=fp):
                c = self.conn.cursor()
                shiny.add_file(c, fp)
                # Getting the directory and name. Fragile.
                got = shiny._get_or_add_file(c, fp)[0:2]
                self.assertEqual(got, c.execute(
                    """SELECT directory, name FROM files WHERE
                    directory = ? AND
                    name = ?""", os.path.split(fp)).fetchone())
