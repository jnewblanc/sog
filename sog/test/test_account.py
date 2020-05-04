''' test_account '''
import unittest

import account
from common.test import TestGameBase
# from common.general import logger


class TestAccount(TestGameBase):

    testAccountId = "someone@test.com"

    def setUp(self):
        self.banner('start', testName=__class__.__name__)

    def testAccountInstanciation(self):
        acctObj = account.Account(None)
        out = "Could not instanciate the account object"
        self.assertEqual(acctObj.isAdmin(), False, out)


if __name__ == '__main__':
    unittest.main()
