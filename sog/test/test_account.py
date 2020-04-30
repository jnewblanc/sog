''' test_account '''
import unittest

import account
# from common.general import logger


class TestAccount(unittest.TestCase):

    testAccountId = "someone@test.com"

    def testAccountInstanciation(self):
        acctObj = account.Account(None)
        out = "Could not instanciate the account object"
        self.assertEqual(acctObj.isAdmin(), False, out)


if __name__ == '__main__':
    unittest.main()
