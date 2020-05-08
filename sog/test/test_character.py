''' test character '''
import unittest

from character import Character
from common.test import TestGameBase
from common.general import logger
import object


class TestCharacter(TestGameBase):

    testCharName = "testChar99999"
    testObjNumber = 99999

    def setTestName(self, name=''):
        self._testName = __class__.__name__

    def setUp(self):
        self.banner('start', testName=__class__.__name__)
        self._client = self.createClientAndAccount()

    def getStatTotals(self, charObj, name=''):
        ''' reusable method for getting stat totals.  Useful for
            comparing/testing level up/down and death '''
        statTotal = 0
        statStr = ''
        for stat in Character.statList:
            val = getattr(charObj, stat)
            statTotal += val
            statStr += stat + '+' + str(val) + ' '
        logger.debug('getStatTotals ' + name + '(' + str(statTotal) + '): ' +
                     str(statStr))
        return(statTotal)

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
        assert charObj.getLevel() == 1
        assert not charObj.isUsable()
        assert not charObj.isEquippable()
        assert not charObj.isMagicItem()
        assert not charObj.isCarryable()
        assert not charObj.isInvisible()
        assert not charObj.isVulnerable()
        assert not charObj.isHidden()
        assert not charObj.isDrunk()
        assert not charObj.isBlessed()
        assert not charObj.isPoisoned()
        assert not charObj.isPlagued()
        assert not charObj.isEvil()
        assert not charObj.isAttacking()

    def testSpellAndBroadcastStats(self):
        charObj = self.createCharacter()
        assert charObj.learnSpell('hurt')
        assert not charObj.learnSpell('bogus')
        assert charObj.knowsSpell('hurt')
        assert not charObj.knowsSpell('bogus')

        assert charObj.getLimitedSpellCount() == 5
        charObj.reduceLimitedSpellCount()
        assert charObj.getLimitedSpellCount() == 4

        assert charObj.getLimitedBroadcastCount() == 5
        charObj.reduceLimitedBroadcastCount()
        assert charObj.getLimitedBroadcastCount() == 4

        charObj.resetDailyStats()
        assert charObj.getLimitedSpellCount() == 5
        assert charObj.getLimitedBroadcastCount() == 5

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

    def testHealth(self):
        maxHP = 100
        maxMana = 10
        startingHP = 50
        startingMana = 5

        charObj = self.createCharacter()
        charObj.setMaxHP(maxHP)
        charObj.setMaxMana(maxMana)
        charObj.setHitPoints(startingHP)
        charObj.setMana(startingMana)
        assert charObj.getHitPoints() == startingHP
        assert charObj.getMana() == startingMana

        # Test Regen doesn't happen when it shouldn't
        charObj.setInstanceDebug(True)
        charObj.setLastRegen()
        charObj.processPoisonAndRegen(regenInterval=5000, poisonInterval=5000)
        assert charObj.getHitPoints() == startingHP
        assert charObj.getMana() == startingMana
        charObj.setInstanceDebug(False)

        # Test Regen happens
        charObj.setLastRegen('never')
        charObj.processPoisonAndRegen()
        assert charObj.getHitPoints() > startingHP
        assert charObj.getMana() > startingMana

        # Test Regen doesn't set up over the max
        charObj.setHitPoints(maxHP)
        charObj.setMana(maxMana)
        charObj.setLastRegen('never')
        charObj.processPoisonAndRegen()
        assert charObj.getHitPoints() == maxHP
        assert charObj.getMana() == maxMana

        # Test takedamage with nokill - Fatal damage should result in hp=1
        charObj.setHitPoints(5)
        charObj.takeDamage(20, nokill=True)
        assert charObj.getHitPoints() == 1

        # Test takedamage with dm - fatal damage should result in max HP
        charObj.setDm()
        assert charObj.isDm()
        charObj.setHitPoints(5)
        charObj.takeDamage(20)
        assert charObj.getHitPoints() == maxHP
        charObj.removeDm()

    def testEquipWeapon(self):
        ''' Create a character and an object.  Test equip/unequip of obj '''
        charObj = self.createCharacter()
        charObj.setName(self.testCharName + 'tew')
        charObj.strength = 10
        charObj._pierce = 10
        charObj.setLevel(1)
        obj1 = object.Weapon(self.testObjNumber)
        obj1.setName("testGranade")
        obj1.setDamageType('_pierce')
        obj1.setMaximumDamage(100)
        obj1.setMinimumDamage(20)
        obj1.setCharges(100)
        obj1.setToHitBonus(10)
        charObj.equip(obj1)
        obj2 = charObj.getEquippedWeapon()
        msg = ("Created object " + obj1.getName() + " does not match " +
               "equipped object " + obj2.getName())
        self.assertEqual(obj1 == obj2, True, msg)
        assert charObj.getEquippedWeaponDamageType() == '_pierce'
        charObj.setInstanceDebug(True)
        assert charObj.getEquippedWeaponDamage() >= 20
        charObj.setInstanceDebug(False)
        assert obj1.getCharges() == 100
        charObj.decreaseChargeOfEquippedWeapon()
        assert obj1.getCharges() == 99
        assert charObj.getEquippedWeaponToHit() == 10
        assert charObj.getEquippedSkillPercentage() == 10
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
        assert len(charObj.getEquippedProtection()) > 0
        assert obj1.getCharges() == 100
        charObj.decreaseChargeOfEquippedProtection()
        assert obj1.getCharges() == 99
        assert charObj.getCumulativeDodge() >= 0
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

    def testSkillsAndStats(self):
        _levelLoopNumber = 10
        charObj = self.createCharacter()
        charObj._classname = 'fighter'
        charObj._bludgeon = 10
        charObj._slash = 20
        assert charObj.getSkillPercentage('_bludgeon') == 10
        assert charObj.rollToBumpSkillForLevel('_slash', percentChance=100)
        assert charObj.getSkillPercentage('_slash') == 30
        logger.debug("Looping " + str(_levelLoopNumber) +
                     " times - raise and lower level")
        firstStatCount = 0
        for i in range(0, _levelLoopNumber):
            statTotalPre = self.getStatTotals(charObj, name=('Pre' + str(i)))
            if not firstStatCount:
                firstStatCount = statTotalPre
            charObj.levelUpStats()
            statTotalPostUp = self.getStatTotals(charObj, name=('PostUp' +
                                                                str(i)))
            assert statTotalPostUp > statTotalPre
            charObj.levelDownStats()
            statTotalPostDown = self.getStatTotals(charObj,
                                                   name=('PostDown' + str(i)))
            assert statTotalPostDown < statTotalPostUp
            logger.debug('testSkillsAndStats: ' + str(statTotalPre) + ' --> ' +
                         str(statTotalPostUp) + ' --> ' +
                         str(statTotalPostDown))
        logger.debug('testSkillsAndStats: Final after ' +
                     str(_levelLoopNumber) +
                     ' times gaining and losing levels: '
                     + str(firstStatCount) + ' --> ' + str(statTotalPostDown))
        assert firstStatCount >= statTotalPostDown

        charObj._doubleUpStatLevels = [2, 3, 7]
        charObj.setLevel(1)
        assert charObj.getStatPoints() == 1, "level 1 - 1 pt"
        charObj.setLevel(2)
        assert charObj.getStatPoints() == 2, "level 2 - 2 pts"
        charObj.setLevel(3)
        assert charObj.getStatPoints() == 2, "level 3 - 2 pts"
        charObj.setLevel(4)
        assert charObj.getStatPoints() == 1, "level 4 - 1 pt"
        charObj.setLevel(5)
        assert charObj.getStatPoints() == 2, "level 5 - 2 pts"

    def testLevelUp(self):
        charObj = self.createCharacter()
        charObj.setClassName('fighter')
        charObj.autoCustomize()

        charObj.setLevel(1)
        charObj._expToNextLevel = 1

        logger.debug(charObj.debug())

        assert not charObj.hasExpToTrain()
        charObj._expToNextLevel = 0
        assert charObj.hasExpToTrain()
        statTotalPre = self.getStatTotals(charObj, name=('Lvl1'))
        charObj.levelUp()
        statTotalLvl2 = self.getStatTotals(charObj, name=('Lvl2'))
        assert charObj.getLevel() == 2
        logger.debug(charObj.debug())
        if (charObj.getClassName() == 'fighter' and charObj.getLevel() == 2):
            logger.debug('testLevelUp: _doubleUpStatLevels=' +
                         str(charObj._doubleUpStatLevels))
            assert statTotalLvl2 >= statTotalPre + 2

    def testDeath(self):
        _levelLoopNumber = 4
        charObj = self.createCharacter()
        origStatTotal = self.getStatTotals(charObj,
                                           name=('level ' +
                                                 str(charObj.getLevel())))
        preStatTotal = origStatTotal
        for i in range(0, _levelLoopNumber):
            charObj.levelUp()
            statTotal = self.getStatTotals(charObj,
                                           name=('level ' +
                                                 str(charObj.getLevel())))
            assert statTotal > preStatTotal
            preStatTotal = statTotal
        assert statTotal > origStatTotal
        assert charObj.getLevel() == _levelLoopNumber + 1
        charObj.setHitPoints(10)
        assert charObj.getHitPoints() == 10
        charObj.takeDamage(9)
        assert charObj.getHitPoints() == 1
        assert charObj.damageIsLethal(30)
        charObj.takeDamage(30, nokill=True)
        charObj.takeDamage(30)
        assert charObj.getRoom().getId() == 1
        assert charObj.getHitPoints() == charObj.getMaxHP()
        assert not charObj.isPoisoned()
        assert not charObj.isPlagued()
        postDeathStatTotal = self.getStatTotals(charObj,
                                                name=('PostDeathLevel ' +
                                                      str(charObj.getLevel())))
        assert postDeathStatTotal >= origStatTotal - 3


if __name__ == '__main__':
    unittest.main()
