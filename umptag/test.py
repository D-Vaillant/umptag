import shiny
import sqlite3
import unittest
from pyfakefs.fake_filesystem_unittest import TestCase
from random import randint, choice
import string

chars = string.ascii_letters + string.digits

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

    @staticmethod
    def make_random_word():
        return ''.join([choice(chars) for _ in range(randint(4, 8))])


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
    import sys
    verbosity = 0
    try:
        if sys.argv[1] == '-v':
            verbosity = 1
        elif sys.argv[1] == '-vv':
            verbosity = 2
    except IndexError:
        pass
    runner = unittest.TextTestRunner(verbosity=verbosity)
    runner.run(suite())
