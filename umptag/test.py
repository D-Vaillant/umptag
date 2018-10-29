import shiny
import sqlite3
import os
import os.path
import unittest
from random import uniform, randrange
from pyfakefs.fake_filesystem_unittest import TestCase


class DBTester(TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self.conn = sqlite3.connect(':memory:', detect_types=sqlite3.PARSE_DECLTYPES)
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter("boolean", lambda v: bool(int(v)))
        shiny.initialize_tables(self.conn.cursor())


class TestFileErrors(DBTester):
    def test_add_nonexistent_file(self):
        self.file_path = "test/file.txt"
        # Test adding a non-existent file.
        with self.assertRaises(FileNotFoundError):
            shiny.add_file(self.conn.cursor(), self.file_path)
            # umptag.add_file


class TestExistingFiles(DBTester):
    def setUp(self):
        super().setUp()
        # Files
        self.fake_filepath = "test/file.txt"
        self.fake_file = self.fs.create_file(self.fake_filepath)
        # Directories
        self.fake_dirpath = "dog"
        self.fake_dir = self.fs.create_dir(self.fake_dirpath)

    def test_only_one_file_added(self):
        for fp in (self.fake_filepath, self.fake_dirpath):
            c = self.conn.cursor()
            shiny.add_file(c, fp)
            results = c.execute("SELECT * FROM files WHERE directory = ? AND name = ?",
                                os.path.split(fp)).fetchall()
            self.assertGreater(len(results), 0)  # Make sure we get at least one match.
            self.assertEqual(len(results), 1)  # Make sure we get at most one match.

        
class TestMetadata(DBTester):
    def setUp(self):
        super().setUp()
        # Files
        self.fake_filepath = "test/file.txt"
        self.fake_file = self.fs.create_file(self.fake_filepath)
        # Directories
        self.fake_dirpath = "dog"
        self.fake_dir = self.fs.create_dir(self.fake_dirpath)

    def test_correct_metadata(self):
        for (fp, file) in ((self.fake_filepath, self.fake_file), (self.fake_dirpath, self.fake_dir)):
            # Filesize
            rand_size = randrange(1500, 30000)
            file.st_size = rand_size
            # Modified Time
            rand_time = round(uniform(10000, 80000), 6)
            file.st_mtime = rand_time
            shiny.add_file(self.conn.cursor(), fp)
            results = self.conn.cursor().execute(
                    "SELECT mod_time, size, is_dir FROM files WHERE directory = ? AND name = ?",
                    os.path.split(fp)).fetchone()
            self.assertEqual((rand_time, rand_size, os.path.isdir(fp)), results)

class TestTagGetting(DBTester):
    def setUp(self):
        super().setUp()
        self.pairs = [('lala', "woof"),
                 ("wag", "wag"),
                 ("ferocious", "hi"),
                 ("hi hi hi", "hello"),
                 ("", "hihaoishio")]

    def test_get_tag(self):
        for pair in self.pairs:
            c = self.conn.cursor()
            c.execute("INSERT INTO tags (key, value) VALUES (?,?)", pair)
            self.assertEqual(pair, shiny.get_tag(c, *pair).fetchone())

    def test_getting_none_key(self):
        pair = ('', "foo")
        self.conn.execute("INSERT INTO tags (key, value) VALUES (?,?)", pair)
        got = shiny.get_tag(self.conn, None, "foo")
        self.assertEqual(('', "foo"), got.fetchone())

class TestTagAdding(DBTester):
    def setUp(self):
        super().setUp()
        self.pairs = [("BORK", "woof"),
                 ("wag", "wag"),
                 ("", "hi"),
                 ("hi hi hi", "hello"),
                 ("broha", "hihaoishio")]

    def test_add_tag(self):
        for pair in self.pairs:
            shiny.add_tag(self.conn.cursor(), *pair)
        for pair in self.pairs:
            result = self.conn.cursor().execute(
                    "SELECT key, value FROM tags WHERE key = ? AND value = ?",
                    pair)

    def test_adding_none_value(self):
        with self.assertRaises(sqlite3.IntegrityError):
            shiny.add_tag(self.conn, key="", value=None)

    def test_adding_none_key(self):
        pair = (None, "foo")
        shiny.add_tag(self.conn, *pair)
        res = self.conn.execute("SELECT key, value FROM tags WHERE key = ? AND value = ?",
                ('' if pair[0] is None else pair[0], pair[1]))




if __name__ == "__main__":
    unittest.main()
