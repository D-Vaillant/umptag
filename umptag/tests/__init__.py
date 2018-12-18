import sqlite3
import unittest
import logging
from os import getcwd, mkdir, chdir
from shutil import rmtree
from pyfakefs.fake_filesystem_unittest import TestCase
from .. import database


format_ = "%(levelname)s :: %(funcName)s -> %(message)s"
logging.basicConfig(format=format_, level=logging.INFO)


class DBTester(TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self.conn = sqlite3.connect(':memory:',
                detect_types=sqlite3.PARSE_DECLTYPES)
        # Breaks basically all of my dang tests. But Rows are better. A Tragedy.
        # self.conn.row_factory = sqlite3.Row
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter("boolean", lambda v: bool(int(v)))
        database._initialize_tables(self.conn.cursor())

    def tearDown(self):
        self.conn.close()


class RealFS_DBTester(unittest.TestCase):
    """ Creates a temporary folder and changes into it.
    Deletes it afterwards. """
    def setUp(self):
        #self.tmp_directory = os.path.abspath('.ump_tmp')
        self.start = getcwd()
        self.tmpdir = '.ump_tmp'
        try:
            mkdir(self.tmpdir)
        except FileExistsError:
            self.tearDown()
            unittest.skip("Folder already existed; tearing down and skipping.")
        chdir(self.tmpdir)

    def tearDown(self):
        chdir(self.start)
        rmtree(self.tmpdir)
