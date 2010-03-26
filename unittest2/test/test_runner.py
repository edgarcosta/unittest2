import pickle

from cStringIO import StringIO
from unittest2.test.support import LoggingResult, OldTestResult

import unittest2



class TestCleanUp(unittest2.TestCase):

    def testCleanUp(self):
        class TestableTest(unittest2.TestCase):
            def testNothing(self):
                pass

        test = TestableTest('testNothing')
        self.assertEqual(test._cleanups, [])

        cleanups = []

        def cleanup1(*args, **kwargs):
            cleanups.append((1, args, kwargs))

        def cleanup2(*args, **kwargs):
            cleanups.append((2, args, kwargs))

        test.addCleanup(cleanup1, 1, 2, 3, four='hello', five='goodbye')
        test.addCleanup(cleanup2)

        self.assertEqual(test._cleanups,
                         [(cleanup1, (1, 2, 3), dict(four='hello', five='goodbye')),
                          (cleanup2, (), {})])

        result = test.doCleanups()
        self.assertTrue(result)

        self.assertEqual(cleanups, [(2, (), {}), (1, (1, 2, 3), dict(four='hello', five='goodbye'))])

    def testCleanUpWithErrors(self):
        class TestableTest(unittest2.TestCase):
            def testNothing(self):
                pass

        class MockResult(object):
            errors = []
            def addError(self, test, exc_info):
                self.errors.append((test, exc_info))

        result = MockResult()
        test = TestableTest('testNothing')
        test._resultForDoCleanups = result

        exc1 = Exception('foo')
        exc2 = Exception('bar')
        def cleanup1():
            raise exc1

        def cleanup2():
            raise exc2

        test.addCleanup(cleanup1)
        test.addCleanup(cleanup2)

        self.assertFalse(test.doCleanups())

        (test1, (Type1, instance1, _)), (test2, (Type2, instance2, _)) = reversed(MockResult.errors)
        self.assertEqual((test1, Type1, instance1), (test, Exception, exc1))
        self.assertEqual((test2, Type2, instance2), (test, Exception, exc2))

    def testCleanupInRun(self):
        blowUp = False
        ordering = []

        class TestableTest(unittest2.TestCase):
            def setUp(self):
                ordering.append('setUp')
                if blowUp:
                    raise Exception('foo')

            def testNothing(self):
                ordering.append('test')

            def tearDown(self):
                ordering.append('tearDown')

        test = TestableTest('testNothing')

        def cleanup1():
            ordering.append('cleanup1')
        def cleanup2():
            ordering.append('cleanup2')
        test.addCleanup(cleanup1)
        test.addCleanup(cleanup2)

        def success(some_test):
            self.assertEqual(some_test, test)
            ordering.append('success')

        result = unittest2.TestResult()
        result.addSuccess = success

        test.run(result)
        self.assertEqual(ordering, ['setUp', 'test', 'tearDown',
                                    'cleanup2', 'cleanup1', 'success'])

        blowUp = True
        ordering = []
        test = TestableTest('testNothing')
        test.addCleanup(cleanup1)
        test.run(result)
        self.assertEqual(ordering, ['setUp', 'cleanup1'])


class Test_TextTestRunner(unittest2.TestCase):
    """Tests for TextTestRunner."""

    def test_works_with_result_without_startTestRun_stopTestRun(self):
        class OldTextResult(OldTestResult):
            def __init__(self, *_):
                super(OldTextResult, self).__init__()
            separator2 = ''
            def printErrors(self):
                pass

        runner = unittest2.TextTestRunner(stream=StringIO(), 
                                          resultclass=OldTextResult)
        runner.run(unittest2.TestSuite())

    def test_startTestRun_stopTestRun_called(self):
        class LoggingTextResult(LoggingResult):
            separator2 = ''
            def printErrors(self):
                pass

        class LoggingRunner(unittest2.TextTestRunner):
            def __init__(self, events):
                super(LoggingRunner, self).__init__(StringIO())
                self._events = events

            def _makeResult(self):
                return LoggingTextResult(self._events)

        events = []
        runner = LoggingRunner(events)
        runner.run(unittest2.TestSuite())
        expected = ['startTestRun', 'stopTestRun']
        self.assertEqual(events, expected)

    def test_pickle_unpickle(self):
        # Issue #7197: a TextTestRunner should be (un)pickleable. This is
        # required by test_multiprocessing under Windows (in verbose mode).
        import StringIO
        # cStringIO objects are not pickleable, but StringIO objects are.
        stream = StringIO.StringIO("foo")
        runner = unittest2.TextTestRunner(stream)
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            s = pickle.dumps(runner, protocol=protocol)
            obj = pickle.loads(s)
            # StringIO objects never compare equal, a cheap test instead.
            self.assertEqual(obj.stream.getvalue(), stream.getvalue())

    def test_resultclass(self):
        def MockResultClass(*args):
            return args
        STREAM = object()
        DESCRIPTIONS = object()
        VERBOSITY = object()
        runner = unittest2.TextTestRunner(STREAM, DESCRIPTIONS, VERBOSITY,
                                         resultclass=MockResultClass)
        self.assertEqual(runner.resultclass, MockResultClass)

        expectedresult = (runner.stream, DESCRIPTIONS, VERBOSITY)
        self.assertEqual(runner._makeResult(), expectedresult)
        
    def test_oldresult(self):
        class Test(unittest2.TestCase):
            def testFoo(self):
                pass
        runner = unittest2.TextTestRunner(resultclass=OldTestResult,
                                          stream=StringIO())
        # This will raise an exception if TextTestRunner can't handle old
        # test result objects
        runner.run(Test('testFoo'))


if __name__ == '__main__':
    unittest2.main()