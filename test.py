import unittest

if __name__ == '__main__':
    """
    Run all the tests
    """
    loader = unittest.TestLoader()
    tests = loader.discover('.')
    testRunner = unittest.runner.TextTestRunner()
    testRunner.run(tests)
