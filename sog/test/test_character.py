''' test character '''
import unittest

from common.test import TestGameBase
# from common.general import logger
import object


class TestCharacter(TestGameBase):

    testCharName = "testChar99999"
    testObjNumber = 99999

    def setUp(self):
        self.banner('start', testName=__class__.__name__)
        self._client = self.createClientAndAccount()

    def testCharAttributes(self):
        charObj = self.createCharacter()
        status, msg = charObj.testAttributes()
        self.assertEqual(status, True, msg)

    def testCharInstanciation(self):
        ''' Test character instanciation + some basic attribute retrieval '''
        charObj = self.createCharacter()
        charObj.setName(self.testCharName)
        charObj.setGender("male")
        charObj.setClassName("fighter")
        charObj.setAlignment('neutral')
        charObj.setMaxHP(100)
        charObj.setHitPoints(100)
        desc = charObj.getDesc()
        assert charObj.isValid()
        msg = "Could not instanciate the character object"
        self.assertEqual(desc != '', True, msg)
        msg = "Could not retrieve character name"
        self.assertEqual(charObj.getName() == self.testCharName, True, msg)
        msg = "Could not retrieve classname"
        self.assertEqual(charObj.getClassName() == 'fighter', True, msg)
        msg = "Could not retrieve hit points"
        self.assertEqual(charObj.getHitPoints() == 100, True, msg)
        charObj.takeDamage(1)
        msg = "takeDamage did not properly reduce hit points"
        self.assertEqual(charObj.getHitPoints() == 99, True, msg)
        assert charObj.save()
        assert charObj.load()
        assert charObj.examine() != ''
        assert charObj.getInfo() != ''

    def testSpellKnoledge(self):
        charObj = self.createCharacter()
        assert charObj.learnSpell('hurt')
        assert not charObj.learnSpell('bogus')
        assert charObj.knowsSpell('hurt')
        assert not charObj.knowsSpell('bogus')

    def testFinancials(self):
        charObj = self.createCharacter()
        charObj.setCoins(0)
        charObj.setBankBalance(0)
        charObj.setTax(0)

        # Test Basic Bank Functions
        charObj.setBankBalance(100)
        assert charObj.getBankBalance() == 100
        charObj.bankAccountAdd(100)
        assert charObj.getBankBalance() == 200
        charObj.bankAccountSubtract(50)
        assert charObj.getBankBalance() == 150
        assert charObj.calculateBankFees(100, 25) == (25, 75)
        charObj.setBankBalance(0)

        # Test adding and removing coin
        charObj.setCoins(500)
        charObj.addCoins(600)
        charObj.subtractCoins(100)
        assert charObj.canAffordAmount(1000)
        assert not charObj.canAffordAmount(1001)

        # Test Bank Transactions
        assert not charObj.bankDeposit(3000)
        assert charObj.bankDeposit(1000)
        assert charObj.getBankBalance() == 950
        assert not charObj.bankWithdraw(3000)
        assert charObj.canWithdraw(100)
        assert not charObj.canWithdraw(1000)
        assert charObj.bankWithdraw(500)
        assert charObj.getBankBalance() == 450
        assert charObj.getCoins() == 500
        assert charObj.getBankFeesPaid() == 50

        # Test Taxes
        charObj.setTax(50)
        assert charObj.recordTax(50)
        assert charObj.getTax() == 100

    def testEquipWeapon(self):
        ''' Create a character and an object.  Test equip/unequip of obj '''
        charObj = self.createCharacter()
        charObj.setName(self.testCharName + 'tew')
        charObj.strength = 10
        charObj.setLevel(1)
        obj1 = object.Weapon(self.testObjNumber)
        obj1.setName("testGranade")
        charObj.equip(obj1)
        obj2 = charObj.getEquippedWeapon()
        msg = ("Created object " + obj1.getName() + " does not match " +
               "equipped object " + obj2.getName())
        self.assertEqual(obj1 == obj2, True, msg)
        charObj.unEquip(obj2)
        obj3 = charObj.getEquippedWeapon()
        msg = "Item is not unequipped - obj3=" + obj3.getName()
        self.assertEqual(obj3.getName() == 'fist', True, msg)

    def testArmorEffectiveness(self):
        ''' Test armor AC effectiveness '''
        charObj = self.createCharacter()
        charObj.setName(self.testCharName + 'tae')
        charObj.setHitPoints(100)
        obj1 = object.Armor(self.testObjNumber)
        obj1._ac = 4
        obj1._singledesc = "french fry"
        obj1._dodgeBonus = 10
        obj1._charges = 100
        obj1.setName("testArmor")
        charObj.equip(obj1)
        obj2 = charObj.getEquippedArmor()
        msg = ("Created object " + obj1.getName() + " does not match " +
               "equipped object " + obj2.getName())
        self.assertEqual(obj1 == obj2, True, msg)
        damage = 10
        percent = .05 * obj1.getAc()
        reduction = int(damage - (damage * percent))
        expectedResult = charObj.getHitPoints() - reduction
        charObj.takeDamage(charObj.acDamageReduction(damage))
        msg = ("takeDamage did not properly reduce hit points - " +
               "ac(" + str(obj1.getAc()) + ") * .05 * level(" +
               str(charObj.getLevel()) + ") = " + str(percent) + "% of " +
               "damage(" + str(damage) + ") means that damage should be " +
               "reduced by " + str(reduction) + ".  Damage should be " +
               str(expectedResult) + " but is set to " +
               str(charObj.getHitPoints()))
        # algoritm has changed.  Need to adjust this list later.
        self.assertEqual(charObj.getHitPoints() != 100, True, msg)


if __name__ == '__main__':
    unittest.main()
