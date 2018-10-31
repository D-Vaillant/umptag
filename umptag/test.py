import shiny
import sqlite3
import unittest
from pyfakefs.fake_filesystem_unittest import TestCase


class DBTester(TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self.conn = sqlite3.connect(':memory:',
                detect_types=sqlite3.PARSE_DECLTYPES)
        # Breaks basically all of my dang tests. But Rows are better. A Tragedy.
        # self.conn.row_factory = sqlite3.Row
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter("boolean", lambda v: bool(int(v)))
        shiny.initialize_tables(self.conn.cursor())

    def tearDown(self):
        self.conn.close()


def load(suite, name):
    suite.addTest(unittest.defaultTestLoader.loadTestsFromName(name))

def suite():
    suite = unittest.TestSuite()
    
    #load('test_files')
    load(suite, 'test_tags')
    load(suite, 'test_files')
    load(suite, 'test_filetag')
    #loadTestsFromName(suite, 'test_filetag_junction')
    # suite.addTest(unittest.defaultTestLoader.loadTestsFromName('test_filetag_junction'))
    #loadTestsFromName(suite, 'test_filetag_junction')
    return suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
