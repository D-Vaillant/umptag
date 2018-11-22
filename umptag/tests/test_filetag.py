import logging
import os
import os.path
from sqlite3 import IntegrityError, OperationalError
from unittest import skip
from . import DBTester
from .utilities import make_random_word, get_random_hierarchy
from .. import shiny, tags
# import shiny, tags


class DBIntegrity(DBTester):
    def test_file_pragma(self):
        with self.conn as c:
            shiny._column_safety(c, 'files', cols='*')
            shiny._column_safety(c, 'files', cols=('name', 'size', 'is_dir'))
            shiny._column_safety(c, 'files', cols=('directory', 'mod_time', 'is_dir', 'is_dir', 'size'))
            with self.assertRaises(OperationalError):
                shiny._column_safety(c, 'files', cols=('name', 'directory', 'isdir', 'size'))
            with self.assertRaises(OperationalError):
                shiny._column_safety(c, 'files', cols=('dog', 'name', 'is_dir'))

    def test_tag_pragma(self):
        with self.conn as c:
            shiny._column_safety(c, 'tags', cols='*')
            shiny._column_safety(c, 'tags', cols=('key', 'value'))
            shiny._column_safety(c, 'tags', cols=('value', 'id', 'id'))
            with self.assertRaises(OperationalError):
                shiny._column_safety(c, 'tags', cols=('valkey',))
            with self.assertRaises(OperationalError):
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
        # First, we add the file to our database.
        for fp in self.fake_filepaths:
            logging.debug("Adding %s to the database.", fp)
            with self.conn as c:
                d, n = os.path.split(fp)
                shiny._add_file(c, d, n)
                for pair in self.pairs:  # For each tag, we go through.
                    # with self.subTest(pair=pair):
                    logging.debug("Using pair <%s=%s>.", (*pair))
                    tags.get_or_add_tag(c, *pair)  # Adding the tag.
                    # We check that it works by getting the ids directly.
                    file_id = shiny._get_file_id(c, d, n)
                    tag_id = c.execute("SELECT id FROM tags WHERE key=? AND value=?", pair).fetchone()[0]
                    # tag_id = tags.tag_kv_to_id(c, *pair)
                    logging.debug("Checking if the database has the pair "
                                  "(file_id=%d, tag_id=%d)." % (file_id, tag_id))
                    # Setting up the relation. 
                    shiny._relate_tag_and_file(c, d, n, *pair)
                    # Finally, we check if only one row was created in the junction table.
                    res = c.execute("""SELECT * FROM filetag_junction WHERE
                            file_id = ? AND tag_id = ?""", (file_id, tag_id)).fetchall()
                    logging.debug("What we got from the database: {}.".format(res))
                    self.assertEqual(len(res), 1)
                    # Now check it gets deleted properly.
                    shiny._unrelate_tag_and_file(c, d, n, *pair)
                    res = c.execute("""SELECT * FROM filetag_junction WHERE
                            file_id = ? AND tag_id = ?""", (file_id, tag_id)).fetchall()
                    self.assertEqual(len(res), 0)

    def test_tags_of_file(self):
        with self.conn as c:
            for fp in self.fake_filepaths:
                seen = []  # We keep track of each tag that we've added.
                logging.debug("Our fake_filepath is %s.", fp)
                shiny._add_file(c, *os.path.split(fp))
                for pair in self.pairs:
                    with self.subTest(fp=fp, pair=pair):
                        tags.get_or_add_tag(c, *pair)
                        seen.append(pair)  # Keeping track...
                        logging.debug("Tags we've seen: {}.".format(', '.join('='.join(_) for _ in seen)))
                        shiny._relate_tag_and_file(c, *os.path.split(fp), *pair)  # Relating...
                        # Here we get all of the tags in the standard format.
                        filetags = shiny.tags_of_file(c, fp, cols=('key', 'value'))
                        logging.debug("Tags we got back: {}.".format(', '.join('='.join(_) for _ in filetags)))
                        self.assertEqual(seen, filetags)

    def test_files_of_tag(self):
        with self.conn as c:
            seen = []
            tag = self.pairs[0]
            tags._add_tag(c, *tag)
            for fp in self.fake_filepaths:
                logging.debug("Our fake_filepath is %s.", fp)
                with self.subTest(fp=fp):
                    d, n = os.path.split(fp)
                    shiny._add_file(c, d, n)
                    seen.append(os.path.split(fp))
                    logging.debug("Files we've seen: {}.".format(', '.join('='.join(_) for _ in seen)))
                    shiny._relate_tag_and_file(c, d, n, *tag)
                    tagfiles = shiny.files_of_tag(c, *tag, cols=('directory', 'name'))
                    logging.debug("Files we got back: {}.".format(', '.join('='.join(_) for _ in tagfiles)))
                    self.assertEqual(sorted(seen), sorted(tagfiles))

