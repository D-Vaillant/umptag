""" test_database.py:
Testcases for umptag.database. """
import sqlite3
import os
from random import randint, choice
from . import DBTester, RealFS_DBTester
from .utilities import make_random_word, get_random_hierarchy
from .. import api, database


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
    # TODO
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

