from  ulearn.core.testing import ULEARN_CORE_FUNCTIONAL_TESTING
from plone.testing import layered
import robotsuite
import unittest


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        layered(robotsuite.RobotTestSuite("robot_test.txt"),
                layer=ULEARN_CORE_FUNCTIONAL_TESTING)
    ])
    return suite