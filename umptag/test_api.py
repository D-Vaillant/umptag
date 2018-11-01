from test import DBTester
import shiny, tags, api
import unittest

class FilesystemTester(DBTester):
    def test_collect_files_flat(self):
        # Make a flat file hierarchy.
        fs_files = sorted([])  # Store those in here.
        fetched_files = sorted(fs.collect_files())
        self.assertEqual(fs_files, fetched_files)

    def test_collect_files_nested(self):
        # Make a non-flat hierarchy.
        fs_files = sorted([])  # Store those in here.
        fetched_files = sorted(fs.collect_files())
        self.assertEqual(fs_files, fetched_files)


class APITester(DBTester):
    def test_find_database(self):
        # Make fake hierarchy.
        # Add database file at the top level. Store its location.
        # Randomly enter a child directory.
        self.assertEquals(db_loc, api.find_database())

    def test_find_database_none(self):
        # Make hierarchy with two dirs.
        # Put the database file in one.
        # Enter the other directory.
        self.assertIs(api.find_database(), None)


