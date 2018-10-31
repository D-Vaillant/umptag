import shiny
import sqlite3
import unittest
import string
import os
from test import DBTester
from random import randint, choice

chars = string.ascii_letters + string.digits

def make_random_word():
    return ''.join([choice(chars) for _ in range(randint(4, 8))])

def get_random_hierarchy(structure=((2, 2), (randint(1, 4), 1), (3, 0))):
        all_files = []
        all_dirs = []
        dir_hier = []
        for (file_count, dir_count) in structure:
            if dir_hier == []:
                all_files += [make_random_word() for f in range(file_count)]
                first_dir_level = [make_random_word() for f in range(dir_count)]
                dir_hier.append(first_dir_level)
                all_dirs += first_dir_level
            else:
                for file in range(file_count):
                    parent_dir = os.path.join(*(choice(dir_grp) for dir_grp in dir_hier))
                    all_files.append(os.path.join(parent_dir, make_random_word()))
                next_dir_level = [make_random_word() for _ in range(dir_count)]
                # for dir in range(dir_count):
                    # dir_name = make_random_word()
                    # next_dir_level += make_random_word()
                    # next_dirs.append(os.path.join(parent_dir, make_random_word(), ''))
                for dir in next_dir_level:
                    parent_dir = os.path.join(*[choice(dir_grp) for dir_grp in dir_hier])
                    all_dirs.append(os.path.join(parent_dir, dir, ''))
                dir_hier.append(next_dir_level)
        return (all_files, all_dirs)


class DBIntegrity(DBTester):
    def test_file_pragma(self):
        with self.conn as c:
            shiny._column_safety(c, 'files', cols='*')
            shiny._column_safety(c, 'files', cols=('name', 'size', 'is_dir'))
            shiny._column_safety(c, 'files', cols=('directory', 'mod_time', 'is_dir', 'is_dir', 'size'))
            with self.assertRaises(sqlite3.OperationalError):
                shiny._column_safety(c, 'files', cols=('name', 'directory', 'isdir', 'size'))
            with self.assertRaises(sqlite3.OperationalError):
                shiny._column_safety(c, 'files', cols=('dog', 'name', 'is_dir'))

    def test_tag_pragma(self):
        with self.conn as c:
            shiny._column_safety(c, 'tags', cols='*')
            shiny._column_safety(c, 'tags', cols=('key', 'value'))
            shiny._column_safety(c, 'tags', cols=('value', 'id', 'id'))
            with self.assertRaises(sqlite3.OperationalError):
                shiny._column_safety(c, 'tags', cols=('valkey',))
            with self.assertRaises(sqlite3.OperationalError):
                shiny._column_safety(c, 'tags', cols=('value', 'id', 'ke'))


class JunctionTester(DBTester):
    def setUp(self):
        super().setUp()

        # self.fake_filepaths = ("test/file.txt",)
        # self.fake_dirpaths = ("dog", "cat")
        self.fake_filepaths, self.fake_dirpaths = get_random_hierarchy()
        self.pairs = [("lala", "woof"),
                 ("", "wag"),
                 ("ferocious", "hi")]

        self.fake_dirs = [self.fs.create_dir(fp) for fp in self.fake_dirpaths]
        self.fake_files = [self.fs.create_file(fp) for fp in self.fake_filepaths]
        self.fake_filepath, self.fake_file = self.fake_filepaths[0], self.fake_files[0]
        """
        for filepath in self.fake_filepaths:
            self.fake_file = self.fs.create_file(self.fake_filepath)
        for dirpath in self.fake_dirpaths: 
        self.fake_dir = self.fs.create_dir(self.fake_dirpath)
        """


class TestFiletagJunctionFunctions(JunctionTester):
    def test_relate_tag_and_file(self):
        with self.conn as c:
            # First, we add the file to our database.
            shiny.add_file(c, self.fake_filepath)
            for pair in self.pairs:  # For each tag, we go through.
                with self.subTest(pair=pair):
                    shiny.add_tag(c, *pair)  # Adding the tag.
                    # Setting up the relation. 
                    shiny.relate_tag_and_file(c, self.fake_filepath, *pair)
                    # We check that it works by getting the ids directly.
                    file_id = shiny.get_file_id(c, self.fake_filepath)
                    tag_id = shiny.get_tag_id(c, *pair)
                    # Finally, we check if only one row was created in the junction table.
                    res = c.execute("""SELECT * FROM filetag_junction WHERE
                            file_id = ? AND tag_id = ?""", (file_id, tag_id)).fetchall()
                    self.assertEqual(len(res), 1)

    def test_tags_of_file(self):
        with self.conn as c:
            seen = []  # We keep track of each tag that we've added.
            shiny.add_file(c, self.fake_filepath)
            for pair in self.pairs:
                with self.subTest(pair=pair):
                    shiny.add_tag(c, *pair)
                    seen.append(pair)  # Keeping track...
                    shiny.relate_tag_and_file(c, self.fake_filepath, *pair)  # Relating...
                    # Here we get all of the tags in the standard format.
                    tags = shiny.tags_of_file(c, self.fake_filepath, cols=('key', 'value'))
                    self.assertEqual(seen, tags)

    def test_files_of_tag(self):
        with self.conn as c:
            seen = []
            tag = self.pairs[0]
            shiny.add_tag(c, *tag)
            for fp in self.fake_filepaths:
                with self.subTest(fp=fp):
                    shiny.add_file(c, fp)
                    seen.append(os.path.split(fp))
                    shiny.relate_tag_and_file(c, fp, *tag)
                    files = shiny.files_of_tag(c, *tag, cols=('directory', 'name'))
                    self.assertEqual(sorted(seen), sorted(files))

