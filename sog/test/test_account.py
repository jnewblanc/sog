''' test_account '''
import re
import unittest

from common.testLib import TestGameBase
from common.general import logger


class TestAccount(TestGameBase):

    testAccountId = "accountTest@test.com"
    _instanceDebug = False

    def setUp(self):
        self.banner('start', testName=__class__.__name__)
        self._testAcctName = self.testAccountId
        self._client = self.createClientAndAccount()
        self._acctObj = self.getAcctObj()

    def testAccountInstanciation(self):
        testCharName1 = 'TestAcctChar1'
        acctObj = self._acctObj
        acctObj.setDisplayName(testCharName1)
        assert acctObj.getName() == testCharName1
        assert acctObj.getEmail() == self.testAccountId
        assert acctObj.getId() == self.testAccountId
        acctObj.setLoginDate()
        assert acctObj.getLastLoginDate()
        acctObj.setLogoutDate()
        assert acctObj.getLastLogoutDate()
        assert acctObj.isValid()
        assert not acctObj.isAdmin()
        assert acctObj.describe() != ''
        assert acctObj.getInfo() != ''
        assert not acctObj.adminFileExists()

    def testChangeEmail(self):
        assert self._acctObj.setUserEmailAddress('acctTest@test.com')
        assert not self._acctObj.setUserEmailAddress('badEmail.com')

    def testCharacterList(self):
        testCharName1 = 'TestAcctChar2'
        testCharName2 = 'TestAcctChar3'
        self._acctObj.addCharacterToAccount(testCharName1)
        assert testCharName1 in self._acctObj.getCharacterList()
        self._acctObj.addCharacterToAccount(testCharName2)
        if self._instanceDebug:
            logger.debug(self._acctObj.showCharacterList())
        assert re.search(testCharName2, self._acctObj.showCharacterList())
        self._acctObj.removeCharacterFromAccount(testCharName1)
        assert testCharName1 not in self._acctObj.getCharacterList()
        assert self._acctObj.getMaxNumOfCharacters() == 5
        assert self._acctObj.getCharacterList() == [testCharName2]


if __name__ == '__main__':
    unittest.main()
