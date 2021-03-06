import os
import os.path
from datetime import datetime, timedelta
from random import uniform, randrange
from sqlite3 import IntegrityError, OperationalError
# My modules.
from .. import fs
from . import DBTester
from .utilities import make_random_word


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

        self.fake_filepaths = [make_random_word() for _ in range(3)]
        self.fake_files = [self.fs.create_file(fs) for fs in self.fake_filepaths]

    # Test `_get_file`.
    def test_getter_variation(self):
        for (fp, file) in ((self.fake_filepath, self.fake_file),
                           (self.fake_dirpath, self.fake_dir)):
            d, n = os.path.split(fp)
            with self.subTest(fp=fp, file=file):
                c = self.conn.cursor()
                # Setting up our attributes
                rand_size = randrange(1500, 30000)
                rand_time = round(uniform(6*(10**8), 9*(10**9)), 4)
                # Setting file attributes
                file.st_size = rand_size
                file.st_mtime = rand_time
                rand_time = datetime.fromtimestamp(rand_time)
                # And then we add it and do a variety of tests
                fs._add_file(c, d, n)
                # We use this to permute.
                all_cols = {"directory": d, "name": n, "mod_time": rand_time,
                        "size": rand_size, "is_dir": os.path.isdir(fp)}
                vars = [('directory', 'mod_time', 'size'),
                        ('name', 'mod_time', 'size'),
                        ('is_dir', 'size'),
                        ('name',),
                        ('directory', 'size')]
                for var in vars:
                    for col in var:
                        c = self.conn.cursor()
                        with self.subTest(col=col):
                            if col != 'mod_time':
                                self.assertEqual(
                                    all_cols.get(col),
                                    fs._get_file_property(c, d, n, col)
                                    )
                            else:
                                # To account for lag.
                                time_diff = abs(all_cols.get(col) - 
                                                fs._get_file_property(c, d, n, col))
                                self.assertTrue(time_diff <= timedelta(milliseconds=1))

    def test_get_safety(self):
        with self.assertRaises(OperationalError):
            fs._get_file_properties(self.conn, '', 'foo', cols=('ashdoaho', 'name'))

    # Test `_get_file_from_id`.
    def test_get_file_from_id(self):
        pass

    # Test `add_file`.
    def test_add_multiple_files(self):
        added = []
        for fp in self.fake_filepaths:
            d, n = os.path.split(fp)
            added.append((d, n))
            fs._add_file(self.conn, d, n)
            from_db = self.conn.execute("SELECT directory, name FROM files").fetchall()
            self.assertEqual(sorted(added), sorted(from_db))
            all_keys = self.conn.execute("SELECT DISTINCT id FROM files").fetchall()
            self.assertEqual(len(added), len(all_keys))


    def test_add_nonexistent_file(self):
        fp = "djowiajod.txt"
        # Test adding a non-existent file.
        with self.assertRaises(FileNotFoundError):
            fs._add_file(self.conn.cursor(), *os.path.split(fp))

    def test_only_one_file_added(self):
        for fp in (self.fake_filepath, self.fake_dirpath):
            d, n = os.path.split(fp)
            c = self.conn.cursor()
            fs._add_file(c, d, n)
            with self.assertRaises(IntegrityError):
                fs._add_file(c, d, n)

    def test_adding_duplicate_exception(self):
        for fp in (self.fake_filepath, self.fake_dirpath):
            d, n = os.path.split(fp)
            c = self.conn.cursor()
            fs._add_file(c, d, n)
            with self.assertRaises(IntegrityError):
                fs._add_file(c, d, n)

    def test_correct_metadata(self):
        for (fp, file) in ((self.fake_filepath, self.fake_file), (self.fake_dirpath, self.fake_dir)):
            d, n = os.path.split(fp)
            # Filesize
            rand_size = randrange(1500, 30000)
            file.st_size = rand_size
            # Modified Time
            rand_time = round(uniform(1 * (6**8), 1 * (9**10)), 4)
            file.st_mtime = rand_time
            rand_time = datetime.fromtimestamp(rand_time)
            fs._add_file(self.conn.cursor(), d, n)
            results = self.conn.cursor().execute(
                    "SELECT mod_time, size, is_dir FROM files WHERE directory = ? AND name = ?",
                    (d, n)).fetchone()
            self.assertEqual((rand_time, rand_size, os.path.isdir(fp)), results)
            self.assertEqual(rand_size, results[1])
            self.assertEqual(os.path.isdir(fp), results[2])
            time_diff = abs(results[0] - rand_time)
            self.assertTrue(time_diff <= timedelta(milliseconds=1)) 


    # Test `get_or_add_file`.
    def test_file_getoradd_adding(self):
        for fp in (self.fake_filepath, self.fake_dirpath):
            with self.subTest(fp=fp):
                c = self.conn.cursor()
                d, n = os.path.split(fp)
                got = fs.get_or_add_file(self.conn.cursor(), d, n)
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
                d, n = os.path.split(fp)
                c = self.conn.cursor()
                fs._add_file(c, d, n)
                # Getting the directory and name. Fragile.
                got = fs.get_or_add_file(c, d, n)[0:2]
                self.assertEqual(got, c.execute(
                    """SELECT directory, name FROM files WHERE
                    directory = ? AND
                    name = ?""", (d, n)).fetchone())
