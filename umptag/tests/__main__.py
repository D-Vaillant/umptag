import sys
import unittest


def load(suite, name):
    suite.addTest(unittest.defaultTestLoader.loadTestsFromName(name))


def suite():
    suite = unittest.TestSuite()
    load(suite, 'test_tags')
    load(suite, 'test_files')
    load(suite, 'test_filetag')
    # load(suite, 'test_api')
    # load(suite, 'test_filesystem')
    return suite


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
