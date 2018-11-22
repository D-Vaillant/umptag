import logging
import os, os.path
from shutil import rmtree
import unittest
import sqlite3
from random import randint, choice
from pyfakefs.fake_filesystem_unittest import TestCase, Patcher
from . import DBTester
from .utilities import make_random_word, get_random_hierarchy
from .. import shiny, tags, api, files, database
from pathlib import Path


"""
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
"""

class RealFS_DBTester(unittest.TestCase):
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

    def tearDown(self):
        os.chdir(self.start)
        rmtree(self.tmpdir)


class FindDatabaseTester(DBTester):
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
        self.assertEquals(db_file.path, database.find_database_filepath(api.DEFAULT_DB_NAME))

    def test_find_database_none(self):
        left, right = make_random_word(), make_random_word()
        self.fs.create_dir(left)
        self.fs.create_file(left+os.sep+api.DEFAULT_DB_NAME)
        self.fs.create_dir(right)
        os.chdir(right)
        self.assertIs(database.find_database_filepath(api.DEFAULT_DB_NAME), None)


class FetchConnectionTester(RealFS_DBTester):
    def test_new_tables(self):
        pass

    def test_init_connection(self):
        database.initialize_connection(':memory:', new_db=True)
        database.initialize_connection('.umptag.db', new_db=True)
        # Test some properties of the connection.

    def test_get_conn(self):
        # c = api.get_conn(in_memory=True)
        # print(os.getcwd())
        c_1 = api.get_conn()
        c_2 = api.get_conn(api.DEFAULT_DB_NAME)
        c_3 = api.get_conn(':memory:')
        # Test some properties of the connection.

    def test_get_conn_failure(self):
        with self.assertRaises(sqlite3.DatabaseError):
            api.get_conn(fail_if_uninitialized=True)

    def test_get_conn_altname(self):
        c = api.get_conn('foobar')

    def test_database_cognancy(self):
        # Setup the database.
        with api.get_conn() as c:
            c.execute("CREATE TABLE foo ("
                    "id integer PRIMARY KEY,"
                    "second_id integer,"
                    "bar TEXT)")
        # Set up the function to wrap.
        def test_me(conn):
            conn.execute("INSERT INTO foo (id, second_id, bar) VALUES (1, ?, ?)", (5, "moo"))
        api.database_cognant(test_me)()  # Run the wrapped function.
        with self.subTest():
            outcoming = api.get_conn().execute("SELECT * FROM foo WHERE bar = ?", ("moo",))
            self.assertIsNotNone(outcoming.fetchone())
        with self.subTest():
            outcoming = api.get_conn().execute("SELECT * FROM foo WHERE bar = ?", ("geez",))
            self.assertIsNone(outcoming.fetchone())


class TagChangeTester(RealFS_DBTester):
    """ Tests `apply_tag` and `remove_tag`. """
    def setUp(self):
        """ What we have available:
        self.filepaths: A list of the files. May or may not be top-level.
        self.dirpaths: A list of the directories. All top-level.
        """
        super().setUp()
        self.filepaths = [make_random_word() for _ in range(randint(3, 6))]
        for fp in self.filepaths:
            # I just used pathlib here. Dang. Oh well.
            Path(fp).touch()
            # self.fs.create_file(fp)
        self.dirpaths = [make_random_word() for _ in range(randint(2, 4))]
        for dp in self.dirpaths:
            Path(dp).mkdir(exist_ok=False)
            # self.fs.create_dir(dp)
            for _ in range(randint(0, 2)):
                stem = make_random_word()
                p = Path(dp, stem)
                p.touch()
                self.filepaths.append(str(p))
                # Path(dp, stem).touch()
                # self.fs.create_file(dp+os.sep+stem)
                # self.dirpaths[dp].append(stem)
        api.initialize_conn()
        return

    def test_simple_apply_tag(self):
        fp = choice(self.filepaths)
        tg = make_random_word()
        api.apply_tag(fp, tg)  # TESTED FUNCTION
        with self.subTest(fp=fp, tg=tg):
            with api.get_conn() as c:
                out = shiny.tags_of_file(c, fp)
            self.assertEqual(out[0], ('', tg))
        with self.subTest(fp=fp, tg=tg):
            with api.get_conn() as c:
                out = shiny.files_of_tag(c, tg)
            self.assertEqual(os.path.join(*out[0]), fp)
        return  # Because otherwise we'll get LOST

    def test_apply_keyless_tag_to_files(self):
        DEBUG = True
        # Choose some random files to tag.
        gen_tags = {}
        len_fp = len(self.filepaths)
        # We create a random number of tags and then apply it to a random
        # number of files. We note which files that the tag was applied to.
        for namelen in range(3, randint(4, 10)):  # Avoid duplicates by various lengths.
            random_tag = make_random_word(a=namelen, b=namelen)
            gen_tags[random_tag] = []
            # Avoid duplicates by using a set.
            chosen = set(choice(self.filepaths) for _ in range(randint(1, len_fp-2)))
            for chose in chosen:
                api.apply_tag(chose, random_tag)  # TESTED FUNCTION
                gen_tags[random_tag].append(chose)
        # Now we check each tag to make sure that the appropriate files were tagged.
        for random_tag, tagged_files in gen_tags.items():
            with self.subTest(random_tag=random_tag, tagged_files=tagged_files):
                tagged_files = set(tagged_files)  # In lieu of sorting.
                with api.get_conn() as c:
                    fetched_files = shiny.files_of_tag(c, '', random_tag)
                    fetched_files = set(str(Path(*ff)) for ff in fetched_files)
                if DEBUG:
                    logging.info("Random tag was %s.", random_tag)
                    logging.info("Tagged files were: %s", ', '.join(tagged_files))
                    logging.info("Fetched files were: %s", ', '.join(fetched_files))
                self.assertEqual(tagged_files, fetched_files)
        return

    def test_apply_keyed_tag_to_files(self):
        """ Same as the above test, except we're using key,value tags. """
        DEBUG = True
        # Choose some random files to tag.
        gen_tags = {}
        len_fp = len(self.filepaths)
        # We create a random number of tags and then apply it to a random
        # number of files. We note which files that the tag was applied to.
        for namelen in range(3, randint(4, 10)):  # Avoid duplicates by various lengths.
            random_key = make_random_word(a=namelen, b=namelen)
            random_tag = make_random_word(a=namelen, b=namelen)
            gen_tags[(random_key, random_tag)] = []
            # Avoid duplicates by using a set. Choose between 1 and almost-all of the files.
            chosen = set(choice(self.filepaths) for _ in range(randint(1, len_fp-2)))
            for chose in chosen:
                api.apply_tag(chose, random_key, random_tag)  # TESTED FUNCTION
                gen_tags[(random_key, random_tag)].append(chose)
        # Now we check each tag to make sure that the appropriate files were tagged.
        for (rk, rt), tagged_files in gen_tags.items():
            with self.subTest(key=rk, tag=rt, tagged_files=tagged_files):
                tagged_files = set(tagged_files)  # In lieu of sorting.
                with api.get_conn() as c:
                    fetched_files = shiny.files_of_tag(c, rk, rt)
                    fetched_files = set(str(Path(*ff)) for ff in fetched_files)
                if DEBUG:
                    logging.info("Random key+tag were %s=%s.", rk, rt)
                    logging.info("Tagged files were: %s", ', '.join(tagged_files))
                    logging.info("Fetched files were: %s", ', '.join(fetched_files))
                self.assertEqual(tagged_files, fetched_files)
        return

