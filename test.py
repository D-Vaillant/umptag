import sys
import unittest


def load(suite, name):
    suite.addTest(unittest.defaultTestLoader.loadTestsFromName(name))


def suite():
    suite = unittest.TestSuite()

    load(suite, 'umptag.tests.test_tags')
    load(suite, 'umptag.tests.test_files')
    load(suite, 'umptag.tests.test_filetag')
    load(suite, 'umptag.tests.test_api')
    # load(suite, 'test_filesystem') # This causes relative import issues.  # Ah, python importing. My nemesis.
    # return unittest.defaultTestLoader.discover('./umptag/tests')
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
