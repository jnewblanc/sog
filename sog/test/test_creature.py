''' test_creature '''
import unittest

from common.test import TestGameBase
from common.general import logger


class TestCreature(TestGameBase):

    testCreatureNumber = 99999
    testRoomNumber = 99999

    def setTestName(self, name=''):
        self._testName = __class__.__name__

    def testCreatureBasics(self):
        creObj = self.createCreature(num=self.testCreatureNumber, name="bug")
        assert creObj.attacksBack()
        assert not creObj.blocksFromLeaving()
        assert creObj.describe() != ''
        assert creObj.debug() != ''
        assert not creObj.canBeEntered()
        assert creObj.examine() != ''
        assert not creObj.fleesIfAttacked()
        assert creObj.getAc() >= 0
        assert creObj.getAlignment() != ''
        assert creObj.getArticle() != ''
        assert creObj.getAttackRate() >= 0
        assert creObj.getCumulativeDodge() >= 0
        assert not creObj.getCurrentlyAttacking()
        assert creObj.getId() != ''
        assert creObj.getEquippedWeaponToHit() >= 0
        assert creObj.getExp() >= 0
        assert creObj.getFrequency() >= 0
        assert creObj.getHitPoints() >= 0
        assert creObj.getLevel() >= 0
        assert creObj.getMaxHP() != ''
        assert creObj.getName() != ''
        assert creObj.getPlural() != ''
        assert creObj.getSingular() != ''
        assert creObj.getToHit() >= 0
        assert creObj.getType() != ''
        assert creObj.getWeight() >= 0
        assert creObj.getValue() >= 0
        assert not creObj.guardsTreasure()
        assert not creObj.isAntiMagic()
        assert not creObj.isAttacking()
        assert not creObj.isCarryable()
        assert not creObj.isHidden()
        assert not creObj.isHostile()
        assert not creObj.isInvisible()
        assert not creObj.isMagic()
        assert not creObj.isPermanent()
        assert not creObj.isUndead()
        assert not creObj.isUnKillable()
        assert not creObj.isVulnerable()
        assert not creObj.kidnaps()
        assert not creObj.sendsToJail()

        creObj.setVulnerable()
        assert creObj.isVulnerable()
        creObj.setEnterRoomTime()
        creObj.setLastAttack()
        creObj.setLastAttackDate()

    def testCreatureParams(self):
        creObj = self.createCreature(num=self.testCreatureNumber, name="bug")
        creObj.setHitPoints(20)
        creObj.addHP(30)
        assert creObj.getHitPoints() == 50
        assert creObj.getDamage(level=1) < creObj.getDamage(level=2)
        creObj.takeDamage(10)
        assert creObj.getHitPoints() == 40
        assert not creObj.damageIsLethal(39)
        assert creObj.damageIsLethal(40)
        assert creObj.damageIsLethal(41)
        creObj._maxhp = 100
        assert creObj.getHitPointPercent() == 40

        creObj._follow = True
        assert creObj.getAttributeCount(which='primary') == 2
        creObj._antiMagic = True
        assert creObj.getAttributeCount(which='secondary') == 1

        creObj._level = 3
        creObj._exp = 5555
        creObj.setExp()
        assert creObj.getExp() > 100

    def testCreatureAttackMethods(self):
        charObj = self.getCharObj()
        creObj = self.createCreature(num=self.testCreatureNumber, name="bug")
        assert creObj.initiateAttack(charObj, alwaysNotices=True)
        assert creObj.isAttacking()
        assert creObj.getCurrentlyAttacking() == charObj
        creObj._ac = 2
        assert creObj.acDamageReduction(100) == 90   # dmg - (.05 * ac * dmg)
        assert creObj.fumbles(basePercent=500, secsToWait=20)
        assert creObj.getSecondsUntilNextAttack() > 10
        assert not creObj.fumbles(basePercent=0)

        creObj._attackRate = 100
        creObj.setSecondsUntilNextAttack(300)
        assert not creObj.canAttack(allowOptOut=False)
        creObj.setSecondsUntilNextAttack(0)
        assert creObj.canAttack(allowOptOut=False)
        creObj._attackRate = 0
        creObj.setInstanceDebug(True)
        assert not creObj.canAttack(allowOptOut=False)
        creObj.setInstanceDebug(False)

        assert creObj.flees() is True or creObj.flees() is False

    def testCreatureParley(self):
        creObj = self.createCreature(num=self.testCreatureNumber, name="bug")
        creObj._parleyAction = 'None'
        creObj._parleyTeleportRooms = [320]
        creObj._parleyTxt = ['eats your eyeballs']
        assert creObj.getParleyAction() == 'None'
        assert creObj.getParleyTeleportRoomNum() == 320
        # Test that the none type doesn't say "says"
        assert creObj.getParleyTxt() == 'The bug eats your eyeballs'
        creObj._parleyTxt = ['bzzt']
        # Test that other types say "says"
        creObj._parleyAction = 'Custom'
        assert creObj.getParleyTxt() == 'The bug says, Bzzt'
        # Test that no message is correct
        creObj._parleyTxt = ['']
        assert creObj.getParleyTxt() == 'The bug does not respond'

        # Test that parly sale item works
        creObj._itemCatalog = ['Weapon/1']
        creObj._numOfItemsCarried = [1]
        creObj.autoPopulateInventory()
        assert creObj.getParleySaleItem().getType() == 'Weapon'

        charObj = self.getCharObj()
        charObj.setLevel(1)
        charObj.charisma = 10
        charObj.setCoins(10)

        for onelvl in range(1, 10):
            creObj._level = onelvl
            logger.info("bribe amount for lvl " + str(creObj.getLevel()) +
                        " = " + str(creObj.getDesiredBribe(charObj)))
        creObj._level = 6

        # Test char does not have enough coins
        assert creObj.getDesiredBribe(charObj) == 3144
        assert not creObj.acceptsBribe(charObj, 5000)
        assert charObj.getCoins() == 10
        logger.debug(charObj.client.popOutSpool())

        # Test sucessful bribe, coins are taken
        charObj.setCoins(10000)
        assert creObj.acceptsBribe(charObj, 5000)
        assert charObj.getCoins() == 5000
        resultMsg = charObj.client.popOutSpool()
        logger.debug(resultMsg)

        # Test unsucessful bribe, coins are taken
        charObj.setCoins(10000)
        assert not creObj.acceptsBribe(charObj, 100)
        assert charObj.getCoins() == 9900
        resultMsg = charObj.client.popOutSpool()
        logger.debug(resultMsg)
        assert '3144' not in resultMsg.split(' ')

        # Test unsucessful bribe, coins are not taken
        charObj.setCoins(10000)
        assert not creObj.acceptsBribe(charObj, 3000)
        assert charObj.getCoins() == 10000
        resultMsg = charObj.client.popOutSpool()
        logger.debug(resultMsg)
        assert '3144' in resultMsg.split(' ')

        # Test unsucessful bribe, coins taken, but amount is shown
        charObj.setCoins(10000)
        assert not creObj.acceptsBribe(charObj, 500)
        assert charObj.getCoins() == 9500
        resultMsg = charObj.client.popOutSpool()
        logger.debug(resultMsg)
        assert '3144' in resultMsg.split(' ')

    def testCreatureLoad(self):
        creatureNumber = 2
        creObj = self.createCreature(num=creatureNumber)
        creObj.load()


if __name__ == '__main__':
    unittest.main()
