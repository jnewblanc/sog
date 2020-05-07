''' test_creature '''
import unittest

from common.test import TestGameBase
from common.general import logger
import creature


class TestCreature(TestGameBase):

    testCreatureNumber = 99999
    testRoomNumber = 99999

    def spinUpCreature(self, num=99999):
        creObj = creature.Creature(num)
        creObj._name = 'bug'
        creObj._article = 'a'
        creObj._pluraldesc = 'potato bugs'
        creObj._singledesc = 'potato bug'
        creObj._longdesc = "potato bugs don't taste like potatoes"
        creObj._level = '1'
        creObj._hostile = False
        creObj._itemCatalog = ['Armor/1', 'Weapon/1']
        creObj._numOfItemsCarried = [1, 2]
        creObj.setHitPoints(20)

        assert creObj.isValid()
        creObj.autoPopulateInventory()
        logger.debug(creObj.debug())

    def testCreatureInstanciation(self):
        creObj = creature.Creature(self.testCreatureNumber)
        out = "Could not instanciate the creature object"
        self.assertEqual(creObj._name == '', True, out)
        creObj.setHitPoints(20)
        creObj.addHP(30)
        creObj.setEnterRoomTime()
        assert not creObj.fleesIfAttacked()
        assert not creObj.isInvisible()
        assert not creObj.isHidden()
        assert not creObj.isHostile()
        assert not creObj.isPermanent()
        assert not creObj.isMagic()
        assert not creObj.isAntiMagic()
        assert not creObj.isCarryable()
        assert not creObj.canBeEntered()
        assert creObj.getWeight() >= 0
        assert creObj.getValue() >= 0

    def testCreatureSpinUp(self):
        creObj = self.spinUpCreature()

        self.creObj = creObj  # Store creature to use later


if __name__ == '__main__':
    unittest.main()
