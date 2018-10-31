import shiny
import sqlite3
import os
import os.path
import unittest
from test import DBTester
# from random import uniform, randrange
# from pyfakefs.fake_filesystem_unittest import TestCase

class TagTester(DBTester):
    def setUp(self):
        super().setUp()
        self.pairs = [('lala', "woof"),
                 ("wag", "wag"),
                 ("ferocious", "hi"),
                 ("hi hi hi", "hello"),
                 ("", "hihaoishio")]


class TestTagFunctions(TagTester):
    """ Tests the `_get_tag` method. """
    # Test `_get_tag`.
    def test_get_tag(self):
        for pair in self.pairs:
            with self.subTest(pair=pair):
                c = self.conn.cursor()
                c.execute("INSERT INTO tags (key, value) VALUES (?,?)", pair)
                self.assertEqual(pair, shiny._get_tag(c, *pair))

    def test_getting_none_key(self):
        pair = ('', "foo")
        self.conn.execute("INSERT INTO tags (key, value) VALUES (?,?)", pair).fetchone()
        got = shiny._get_tag(self.conn, None, "foo")
        self.assertEqual(('', "foo"), got)
    
    # Test `_get_tag_from_id.`
    # def test_get_tag_from_id(self):
        # pass

    # Test `add_tag`.
    def test_add_tag(self):
        for pair in self.pairs:
            with self.subTest(pair=pair):
                shiny.add_tag(self.conn.cursor(), *pair)
                result = self.conn.cursor().execute(
                        "SELECT key, value FROM tags WHERE key = ? AND value = ?",
                        pair).fetchone()
                self.assertEqual(result, pair)

    def test_adding_none_value(self):
        with self.assertRaises(sqlite3.IntegrityError):
            shiny.add_tag(self.conn, key="", value=None)

    def test_adding_none_key(self):
        pair = (None, "foo")
        shiny.add_tag(self.conn, *pair)
        res = self.conn.execute("SELECT key, value FROM tags WHERE key = ? AND value = ?",
                ('' if pair[0] is None else pair[0], pair[1]))

    def test_adding_duplicate_tag(self):
        c = self.conn.cursor()
        for pair in self.pairs:
            shiny.add_tag(c, *pair)
            with self.assertRaises(sqlite3.IntegrityError):
                shiny.add_tag(c, *pair)

    # Test `_get_or_add_tag`.
    def test_tag_getoradd(self):
        for pair in self.pairs:
            with self.subTest(pair=pair):
                c = self.conn.cursor()
                # First add.
                a = shiny._get_or_add_tag(c, *pair)
                query = c.execute(
                    """SELECT key, value FROM tags WHERE
                    key = ? AND
                    value = ?""", pair).fetchall()
                self.assertEqual(1, len(query))
                self.assertEqual(a, query.pop())
                # Next, get.
                b = shiny._get_or_add_tag(c, *pair)
                query = c.execute(
                    """SELECT key, value FROM tags WHERE
                    key = ? AND
                    value = ?""", pair).fetchall()
                self.assertEqual(1, len(query))
                self.assertEqual(b, query.pop())
                self.assertEqual(a, b)
