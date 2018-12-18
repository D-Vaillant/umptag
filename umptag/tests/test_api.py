""" test_api.py:
TestCases for umptag.api. """
import logging
import os
import os.path
import sqlite3
import unittest
from collections import defaultdict
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


class AddRemove_TagChangeTester(TagChangeTester):
    def setUp(self):
        super().setUp()
        self.DEBUG = False

    def test_simple_apply_tag(self):
        """ Testing api.apply_tag on single file. """
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


    def test_simple_remove_tag(self):
        """ Testing api.remove_tag on a single file. """
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


    """ NOTE: Well, can't I merge the below two functions? The remove_tag func
    is checking to see if the tag was added redundantly; I don't want to
    remove that because, even if it works through apply_tag, I'm paranoid. """
    def test_apply_tag(self):
        """ Adding multiple tags to files. """
        DEBUG = False
        # Choose some random files to tag.
        attached_tags = defaultdict(set)
        len_fp = len(self.filepaths)
        # We create a random number of tags and then apply it to a random
        # number of files. We note which files that the tag was applied to.
        for has_key in [True, False]:
            with self.subTest(has_key=has_key):
                for namelen in range(3, randint(4, 10)):  # Avoid duplicates by various lengths.
                    random_tag = make_random_word(a=namelen, b=namelen)
                    if has_key:
                        random_key = ''
                        apply_tag = lambda c, d, n: api.apply_tag(c, d, n, random_tag)
                    else:
                        random_key = make_random_word(a=namelen, b=namelen)
                        apply_tag = lambda c, d, n: api.apply_tag(c, d, n, random_key, random_tag)
                    # The files we're tagging.
                    files_to_tag = set(os.path.split(choice(self.filepaths))
                                 for _ in range(randint(1, len_fp-2)))
                    self.assertNotEqual(files_to_tag, {})
                    for (d, n) in files_to_tag:
                        # We note which tag we're putting on the file for Later.
                        attached_tags[(d, n)].add((random_key, random_tag))
                        # And we tag the file.
                        with database.get_conn(self.db_name) as c:
                            apply_tag(c, d, n)
                        # And we test if it's been tagged.
                        with database.get_conn(self.db_name) as c:
                            self.assertIn((d, n),
                                          filetags.files_of_tag(c,
                                              random_key,
                                              random_tag))
                            self.assertIn((random_key, random_tag),
                                          filetags.tags_of_file(c, d, n))
                    # We finished tagging the files.
                    with database.get_conn(self.db_name) as c:
                        # What actually got tagged.
                        actually_tagged = set(filetags.files_of_tag(c, random_key, random_tag))
                    if DEBUG:
                        print(f"Test case for {(random_key+'=' if random_key else '')}{random_tag}.")
                        print(actually_tagged)
                        print(files_to_tag)
                        print()
                    self.assertEqual(files_to_tag, actually_tagged)
            # This is Later, after the keyed and then after unkeyed.
            for file, file_tags in attached_tags.items():
                # We make sure that the files have the tags we wanted them to have.
                self.assertEqual(set(filetags.tags_of_file(c, *file)),
                                 file_tags)

    def test_remove_tag(self):
        """ Testing api.remove_tag on multiple files. """
        DEBUG = False
        # Choose some random files to tag.
        attached_tags = defaultdict(set)
        len_fp = len(self.filepaths)
        # We create a random number of tags and then apply it to a random
        # number of files. We note which files that the tag was applied to.
        for has_key in [True, False]:
            with self.subTest(has_key=has_key):
                for namelen in range(3, randint(4, 10)):  # Avoid duplicates by various lengths.
                    # Preparing our environment.
                    random_tag = make_random_word(a=namelen, b=namelen)
                    if has_key:
                        random_key = ''
                        apply_tag = lambda c, d, n: api.apply_tag(
                                c, d, n, random_tag)
                        remove_tag = lambda c, rm_d, rm_n: api.remove_tag(
                                c, rm_d, rm_n, random_tag)
                    else:
                        random_key = make_random_word(a=namelen, b=namelen)
                        apply_tag = lambda c, d, n: api.apply_tag(
                                c, d, n, random_key, random_tag)
                        remove_tag = lambda c, rm_d, rm_n: api.remove_tag(
                                c, rm_d, rm_n, random_key, random_tag)
                    # Avoid duplicates by using a set.
                    files_to_tag = set(os.path.split(choice(self.filepaths))
                                       for _ in range(randint(1, len_fp-2)))
                    for (d, n) in files_to_tag:
                        attached_tags[(d, n)].add((random_key, random_tag))
                        with database.get_conn(self.db_name) as c:
                            apply_tag(c, d, n)
                        # Make sure we actually tagged it.
                        with database.get_conn(self.db_name) as c:
                            self.assertIn((d, n),
                                          filetags.files_of_tag(c,
                                              random_key,
                                              random_tag))
                            self.assertIn((random_key, random_tag),
                                          filetags.tags_of_file(c, d, n))
                    while files_to_tag:
                        rm_d, rm_n = files_to_tag.pop()
                        attached_tags[(rm_d, rm_n)].remove((random_key, random_tag))
                        with database.get_conn(self.db_name) as c:
                            remove_tag(c, rm_d, rm_n)
                            self.assertNotIn((random_key, random_tag),
                                    filetags.tags_of_file(c, rm_d, rm_n))
                            self.assertNotIn((rm_d, rm_n),
                                    filetags.files_of_tag(c,
                                                          random_key,
                                                          random_tag))
                        self.assertEqual(attached_tags[(rm_d, rm_n)],
                                set(filetags.tags_of_file(c, rm_d, rm_n)))



class Merge_TagChangeTester(TagChangeTester):
    def test_merge_tag(self):
        """ Testing api.merge_tag. """ 
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
        """ Testing if api.apply_tag handles adding duplicate tags. """
        d, n = os.path.split(choice(self.filepaths))
        for tg in ((make_random_word(),), (make_random_word(), make_random_word())):
            with database.get_conn(self.db_name) as c:
                api.apply_tag(c, d, n, *tg)
            with database.get_conn(self.db_name) as c:
                self.assertEqual(1, api.apply_tag(c, d, n, *tg))

    def test_remove_null_tag(self):
        """ Testing if api.remove_tag handles removing tags that aren't there. """
        d, n = os.path.split(choice(self.filepaths))
        with database.get_conn(self.db_name) as c:
            self.assertEqual(1, api.remove_tag(c, d, n, make_random_word()))


class Orphan_TagChangeTester(TagChangeTester):
    def test_remove_orphan_file(self):
        """ Testing api.remove_orphans for files. """
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
        """ Testing api.remove_orphans for tags. """
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


class GetInfo_TagChangeTester(TagChangeTester):
    def test_show_tags(self):
        """ Testing printing out which tags a file has. """
        len_fp = len(self.filepaths)
        tagged_files = defaultdict(set)
        filed_tags = defaultdict(set)
        for has_key in [True, False]:
            for namelen in range(3, randint(4, 10)):  # Avoid duplicates by various lengths.
                random_tag = make_random_word(a=namelen, b=namelen)
                if has_key:
                    random_key = ''
                    apply_tag = lambda c, d, n: api.apply_tag(c, d, n, random_tag)
                else:
                    random_key = make_random_word(a=namelen, b=namelen)
                    apply_tag = lambda c, d, n: api.apply_tag(c, d, n, random_key, random_tag)
                # The files we're tagging.
                files_to_tag = set(os.path.split(choice(self.filepaths))
                             for _ in range(randint(1, len_fp-2)))
                filed_tags[(random_key, random_tag)] = files_to_tag
                for (d, n) in files_to_tag:
                    tagged_files[(d, n)].add((random_key, random_tag))
                    with database.get_conn(self.db_name) as c:
                        apply_tag(c, d, n)
        with self.subTest("Testing show_tags."):
            for file, tagged in tagged_files.items():
                tagged = set((k+'=' if k else '')+t for (k, t) in tagged)
                with database.get_conn(self.db_name) as c:
                    self.assertEqual(tagged, set(api.show_tags(c, *file)))
        with self.subTest("Testing show_files."):
            for tag_, files_ in filed_tags.items():
                tag_str = (tag_[0]+'=' if tag_[0] else '')+tag_[1]
                filed = set(os.path.join(d, n) for (d, n) in files_)
                with database.get_conn(self.db_name) as c:
                    show_output = set(api.show_files(c, *tag_))


    def test_show_files(self):
        """ Testing printing out what files have a specific tag. """
        pass


def tag_sorter(kv1, kv2):
    """ This is going to be USEFUL at some point """
    k1, v1 = kv1
    k2, v2 = kv2
    if k1 == '':
        if k2 != '':
            # kv1 is unkeyed, kv2 not
            return True
        else:
            # Both unkeyed
            return v1 <= v2
    elif k2 == '':
        # kv2 unkeyed, kv1 not
        return False
    elif k1 < k2:
        return True
    elif k1 == k2:
        return v1 <= v2
    else:
        return False
            

# Let's redo all of these suckers but with a COMPLETELY DIFFERENT DATABASE NAME
def is_test_method(cls, func):
    return callable(getattr(cls, func)) and func.startswith('test_')

def mk_dbrenamed_class(cls):
    class Out(cls):
        def setUp(self):
            super().setUp()
            self.db_name = make_random_word()
    Out.__name__ = 'DBRenamed_' + cls.__name__
    # As per PEP3155. And StackOverflow.
    Out.__qualname__ = Out.__name__
    """ Boy, this just is not working.
    for method in (func for func in dir(Out) if is_test_method(Out, func)):
        original_doc = (getattr(cls, method).__doc__ or '')
        getattr(cls, method).__doc__ = original_doc + "Using a different database name.\n"
    """
    return Out

DBRenamed_AddRemove_TagChangeTester = mk_dbrenamed_class(AddRemove_TagChangeTester)
DBRenamed_Orphan_TagChangeTester = mk_dbrenamed_class(Orphan_TagChangeTester)
DBRenamed_Merge_TagChangeTester = mk_dbrenamed_class(Merge_TagChangeTester)
Error_DBRenamed_TagChangeTester = mk_dbrenamed_class(Error_TagChangeTester)
