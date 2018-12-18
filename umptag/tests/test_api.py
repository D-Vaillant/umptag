""" test_api.py:
TestCases for umptag.api. """
import logging
import os
import os.path
import sqlite3
import unittest
from pathlib import Path
from random import randint, choice
from . import DBTester, RealFS_DBTester
from .utilities import make_random_word, get_random_hierarchy
from .. import (api,
                fs,
                tags,
                filetags,
                database)


class TagChangeTester(RealFS_DBTester):
    """ Tests `apply_tag` and `remove_tag`. """
    def setUp(self):
        """ What we have available:
        self.filepaths: A list of the files. May or may not be top-level.
        self.dirpaths: A list of the directories. All top-level.
        """
        super().setUp()
        self.db_name = database.DEFAULT_DB_NAME
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
        database.initialize_conn(self.db_name, True)
        return


class Keyless_TagChangeTester(TagChangeTester):
    def setUp(self):
        super().setUp()
        self.DEBUG = False

    def test_simple_apply_tag(self):
        d, n = os.path.split(choice(self.filepaths))
        tg = make_random_word()
        with database.get_conn(self.db_name) as c:
            api.apply_tag(c, d, n, tg)  # TESTED FUNCTION
        with self.subTest(directory=d, name=d, tg=tg):
            with database.get_conn(self.db_name) as c:
                out = filetags.tags_of_file(c, d, n)
            self.assertEqual(out[0], ('', tg))
        with self.subTest(directory=d, name=n, tg=tg):
            with database.get_conn(self.db_name) as c:
                out = filetags.files_of_tag(c, '', tg)
            self.assertEqual(out[0], (d, n))
        return  # Because otherwise we'll get LOST

    def test_apply_keyless_tag_to_files(self):
        DEBUG = False
        len_fp = len(self.filepaths)
        # Avoid duplicates by using different lengths.
        for namelen in range(3, randint(4, 10)): 
            random_tag = make_random_word(a=namelen, b=namelen)
            # Avoid duplicates by using a set.
            files_to_tag = {os.path.split(choice(self.filepaths)) for _ in range(randint(1, len_fp-2))}
            for (d, n) in files_to_tag:
                with database.get_conn(self.db_name) as c:
                    api.apply_tag(c, d, n, random_tag)  # TESTED FUNCTION
                    with self.subTest(directory=d, name=n, tag=random_tag):
                        self.assertIn((d, n), filetags.files_of_tag(c, '', random_tag))
            with self.subTest(tag=random_tag):
                with database.get_conn(self.db_name) as c:
                    tagged_files = set(filetags.files_of_tag(c, '', random_tag))
                if DEBUG:
                    logging.info("Random tag was %s.", random_tag)
                    logging.info("Files to tag were: %s", ', '.join(
                        os.path.join(a, b) for (a, b) in files_to_tag))
                    logging.info("Files actually tagged were: %s", ', '.join(
                        os.path.join(a, b) for (a, b) in tagged_files))
                self.assertEqual(files_to_tag, tagged_files)

    def test_simple_remove_tag(self):
        d, n = os.path.split(choice(self.filepaths))
        tg = make_random_word()
        with database.get_conn(self.db_name) as c:
            api.apply_tag(c, d, n, tg)
            api.remove_tag(c, d, n, tg)
        with self.subTest(directory=d, name=n, tg=tg):
            with database.get_conn(self.db_name) as c:
                out = filetags.tags_of_file(c, d, n)
            self.assertEqual(out, [])
        with self.subTest(directory=d, name=n, tg=tg):
            with database.get_conn(self.db_name) as c:
                out = filetags.files_of_tag(c, '', tg)
            self.assertEqual(out, [])
        return  # Because otherwise we'll get LOST

    def test_remove_keyless_tag_from_files(self):
        DEBUG = False
        # Choose some random files to tag.
        gen_tags = {}
        len_fp = len(self.filepaths)
        # We create a random number of tags and then apply it to a random
        # number of files. We note which files that the tag was applied to.
        for namelen in range(3, randint(4, 10)):  # Avoid duplicates by various lengths.
            random_tag = make_random_word(a=namelen, b=namelen)
            # Avoid duplicates by using a set.
            files_to_tag = set(os.path.split(choice(self.filepaths))
                    for _ in range(randint(1, len_fp-2)))
            for (d, n) in files_to_tag:
                with database.get_conn(self.db_name) as c:
                    api.apply_tag(c, d, n, random_tag)
                    # Make sure we actually tagged it.
                    self.assertIn((d, n), filetags.files_of_tag(c, '', random_tag))
            while files_to_tag:
                rm_d, rm_n = files_to_tag.pop()
                with self.subTest(directory=d, name=n, tag=random_tag):
                    with database.get_conn(self.db_name) as c:
                        api.remove_tag(c, rm_d, rm_n, random_tag)
                        self.assertNotIn(random_tag, filetags.tags_of_file(c, rm_d, rm_n))
                        self.assertNotIn((rm_d, rm_n), filetags.files_of_tag(c, '', random_tag))
            with self.subTest(tag=random_tag):
                self.assertFalse(filetags.files_of_tag(c, '', random_tag))


class Keyed_TagChangeTester(TagChangeTester):
    """ Note: can't this just be folded into the default one?
    I'd have to rewrite some of the logic; maybe using lambdas... """
    def test_apply_keyed_tag_to_files(self):
        DEBUG = False
        # Choose some random files to tag.
        gen_tags = {}
        len_fp = len(self.filepaths)
        # We create a random number of tags and then apply it to a random
        # number of files. We note which files that the tag was applied to.
        for namelen in range(3, randint(4, 10)):  # Avoid duplicates by various lengths.
            random_tag = make_random_word(a=namelen, b=namelen)
            if False:
                random_key = ''
                apply_tag = lambda d, n: api.apply_tag(c, d, n, random_key)
            else:
                random_key = make_random_word(a=namelen, b=namelen)
                apply_tag = lambda d, n: api.apply_tag(c, d, n, random_key, random_tag)
            # Avoid duplicates by using a set. Choose between 1 and almost-all of the files.
            chosen = set(os.path.split(choice(self.filepaths)) for _ in range(randint(1, len_fp-2)))
            for (d, n) in chosen:
                with database.get_conn(self.db_name) as c:
                    # api.apply_tag(c, k, v, random_key, random_tag)  # TESTED FUNCTION
                    apply_tag(d, n)
            with self.subTest(key=random_key, tag=random_tag, tagged_files=chosen):
                with database.get_conn(self.db_name) as c:
                    fetched_files = set(filetags.files_of_tag(c, random_key, random_tag))
                if DEBUG:
                    logging.info("Random key+tag were %s=%s.", random_key, random_tag)
                    logging.info("Tagged files were: %s", ', '.join(chosen))
                    logging.info("Fetched files were: %s", ', '.join(fetched_files))
                self.assertEqual(chosen, fetched_files)

    def test_remove_keyed_tag_from_files(self):
        DEBUG = False
        # Choose some random files to tag.
        gen_tags = {}
        len_fp = len(self.filepaths)
        # We create a random number of tags and then apply it to a random
        # number of files. We note which files that the tag was applied to.
        for has_key in [True, False]:
            for namelen in range(3, randint(4, 10)):  # Avoid duplicates by various lengths.
                random_tag = make_random_word(a=namelen, b=namelen)
                if has_key:
                    random_key = ''
                    apply_tag = lambda d, n: api.apply_tag(
                            c, d, n, random_tag)
                    remove_tag = lambda rm_d, rm_n: api.remove_tag(
                            c, rm_d, rm_n, random_tag)
                else:
                    random_key = make_random_word(a=namelen, b=namelen)
                    apply_tag = lambda d, n: api.apply_tag(
                            c, d, n, random_key, random_tag)
                    remove_tag = lambda rm_d, rm_n: api.remove_tag(
                            c, rm_d, rm_n, random_key, random_tag)
                # Avoid duplicates by using a set.
                files_to_tag = set(os.path.split(choice(self.filepaths))
                        for _ in range(randint(1, len_fp-2)))
                for (d, n) in files_to_tag:
                    with database.get_conn(self.db_name) as c:
                        apply_tag(d, n)
                        # Make sure we actually tagged it.
                        self.assertIn((d, n),
                                filetags.files_of_tag(c, random_key, random_tag))
                while files_to_tag:
                    rm_d, rm_n = files_to_tag.pop()
                    with database.get_conn(self.db_name) as c:
                        remove_tag(rm_d, rm_n)
                        self.assertNotIn(random_tag,
                                filetags.tags_of_file(c, rm_d, rm_n))
                        self.assertNotIn((rm_d, rm_n),
                                filetags.files_of_tag(c,
                                                      random_key,
                                                      random_tag))
                with self.subTest(key=random_key, tag=random_tag):
                    self.assertFalse(filetags.files_of_tag(c,
                                                           random_key,
                                                           random_tag))



class Merge_TagChangeTester(TagChangeTester):
    def test_merge_tag(self):
        parent_tags = [('', make_random_word()), (make_random_word(), make_random_word())]
        for parent_tag in parent_tags:
            """
            child_tags = [('', parent_tag[1]+"_fob"), (parent_tag[0]+"_bar", parent_tag[1]+"_bar"),
                          (parent_tag[0], parent_tag[1]+"_bax"), (parent_tag[0]+"_bai", parent_tag[1])]
            for child_tag in child_tags:
            """
            child_tag = (parent_tag[1], parent_tag[0])
            tagged_files = []
            for _ in range(randint(2, 5)):
                fp = os.path.split(choice(self.filepaths))
                tagged_files.append(fp)
                with database.get_conn(self.db_name) as c:
                    api.apply_tag(c, *fp, *child_tag)
            with database.get_conn(self.db_name) as c:
                api.merge_tag(c, *parent_tag, *child_tag)
                self.assertEqual(set(tagged_files),
                        set(filetags.files_of_tag(c, *parent_tag)))
                self.assertFalse(filetags.files_of_tag(c, *child_tag))
                self.assertFalse(tags._exists_tag(c, *child_tag))


class Error_TagChangeTester(TagChangeTester):
    def test_add_duplicate_tag(self):
        d, n = os.path.split(choice(self.filepaths))
        for tg in ((make_random_word(),), (make_random_word(), make_random_word())):
            with database.get_conn(self.db_name) as c:
                api.apply_tag(c, d, n, *tg)
            with database.get_conn(self.db_name) as c:
                self.assertEqual(1, api.apply_tag(c, d, n, *tg))

    def test_remove_null_tag(self):
        d, n = os.path.split(choice(self.filepaths))
        with database.get_conn(self.db_name) as c:
            self.assertEqual(1, api.remove_tag(c, d, n, make_random_word()))


class Orphan_TagChangeTester(TagChangeTester):
    def test_remove_orphan_file(self):
        conn = database.get_conn(self.db_name)
        fp = choice(self.filepaths)
        for tg in ((make_random_word(),), (make_random_word(), make_random_word())):
            d, n = os.path.split(fp)
            with database.get_conn(self.db_name) as c:
                api.apply_tag(c, d, n, *tg)
            self.assertIsNotNone(conn.execute(
                "SELECT * FROM files WHERE directory=? AND name=?", os.path.split(fp)).fetchone())
            with database.get_conn(self.db_name) as c:
                api.remove_tag(c, d, n, *tg)
            self.assertIsNone(conn.execute(
                "SELECT * FROM files WHERE directory=? AND name=?", os.path.split(fp)).fetchone())

    def test_remove_orphan_tag(self):
        conn = database.get_conn(self.db_name)
        fp = choice(self.filepaths)
        for tg in (('', make_random_word(),), (make_random_word(), make_random_word())):
            d, n = os.path.split(fp)
            with database.get_conn(self.db_name) as c:
                api.apply_tag(c, d, n, *tg)
            self.assertIsNotNone(conn.execute(
                "SELECT * FROM tags WHERE key=? AND value=?", tg).fetchone())
            with database.get_conn(self.db_name) as c:
                api.remove_tag(c, d, n, *tg)
            self.assertIsNone(conn.execute(
                "SELECT * FROM tags WHERE key=? AND value=?", tg).fetchone())


# Let's redo all of these suckers but with a COMPLETELY DIFFERENT DATABASE NAME
def mk_dbrenamed_class(cls):
    class Out(cls):
        def setUp(self):
            super().setUp()
            self.db_name = make_random_word()
    return Out


Keyless_DBRenamed_TagChangeTester = mk_dbrenamed_class(Keyless_TagChangeTester)
Keyed_DBRenamed_TagChangeTester = mk_dbrenamed_class(Keyed_TagChangeTester)
Orphan_DBRenamed_TagChangeTester = mk_dbrenamed_class(Orphan_TagChangeTester)
Merge_DBRenamed_TagChangeTester = mk_dbrenamed_class(Merge_TagChangeTester)
Error_DBRenamed_TagChangeTester = mk_dbrenamed_class(Error_TagChangeTester)
