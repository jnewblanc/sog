''' test_object '''
import re
import unittest

from common.testLib import TestGameBase
from common.general import logger, getNeverDate, dateStr
from object import ObjFactoryTypes


class TestObject(TestGameBase):

    testObjNumber = 99999

    _equippables = ['armor', 'shield', 'weapon', 'necklace', 'ring']
    _magics = ['card', 'scroll', 'potion', 'staff', 'teleport']
    _permanents = ['portal', 'door', 'container']
    _others = ['key', 'coins', 'treasure']

    def setTestName(self, name=''):
        self._testName = __class__.__name__

    def testObjectInstanciation(self):
        for num, oneType in enumerate(ObjFactoryTypes,
                                      start=self.testObjNumber):
            if oneType.lower() == 'object':
                continue
            obj = self.createObject(num=num,
                                    type=oneType,
                                    name=(oneType + str(num)))
            assert obj.isValid()
            assert obj.describe() != ''
            assert obj.debug() != ''
            assert obj.examine() != ''
            assert obj.identify() != ''
            assert obj.getId() != 0
            assert obj.getType() != ''
            assert obj.getName() != ''
            assert obj.getArticle() != ''
            assert obj.getSingular() != ''
            assert obj.getPlural() != ''
            assert not obj.isCursed()
            assert not obj.isHidden()
            assert not obj.isInvisible()
            assert obj.getValue() >= 0
            assert obj.getWeight() >= 0
            assert obj.adjustPrice(10) == 10
            typeStr = 'type=' + oneType
            if oneType in self._equippables + self._magics + ['key']:
                assert obj.isUsable(), 'type=' + oneType
            else:
                assert not obj.isUsable(), typeStr
            if oneType in self._permanents:
                assert obj.isPermanent(), typeStr
                if not oneType == 'container':  # containers can be perm&carry
                    assert not obj.isCarryable()
            else:
                assert not obj.isPermanent(), typeStr
                assert obj.isCarryable()
            if oneType in self._magics:
                assert obj.isMagic()
            else:
                assert not obj.isMagic()

    def testLimitations(self):
        charObj = self.getCharObj()
        obj = self.createObject(num=self.testObjNumber,
                                type='Door',
                                name='door1')

        # Test class limitations
        obj._classesAllowed = ['mage', 'paladin']
        charObj._classname = 'fighter'
        assert not obj.limitationsAreSatisfied(charObj), charObj.getClassName()
        charObj._classname = 'paladin'
        assert obj.limitationsAreSatisfied(charObj), charObj.getClassName()

        # Test class limitations
        obj._alignmentsAllowed = ['lawful', 'neutral']
        charObj._alignment = 'chaotic'
        assert not obj.limitationsAreSatisfied(charObj), charObj.getAlignment()
        charObj._alignment = 'neutral'
        assert obj.limitationsAreSatisfied(charObj), charObj.getAlignment()

        # Test gender limitations
        obj._gendersAllowed = ['male', 'pan']
        charObj._gender = 'female'
        assert not obj.limitationsAreSatisfied(charObj), charObj.getGender()
        charObj._gender = 'male'
        assert obj.limitationsAreSatisfied(charObj), charObj.getGender()

        # Test level limitations
        obj._minLevelAllowed = 3
        obj._maxLevelAllowed = 5
        charObj.setLevel(2)
        assert not obj.limitationsAreSatisfied(charObj), charObj.getLevel()
        charObj.setLevel(6)
        assert not obj.limitationsAreSatisfied(charObj), charObj.getLevel()
        charObj.setLevel(3)
        assert obj.limitationsAreSatisfied(charObj), charObj.getLevel()
        charObj.setLevel(4)
        assert obj.limitationsAreSatisfied(charObj), charObj.getLevel()
        charObj.setLevel(5)
        assert obj.limitationsAreSatisfied(charObj), charObj.getLevel()

        logger.info(str(obj))

    def testExhaustible(self):
        obj = self.createObject(num=self.testObjNumber,
                                type='Shield',
                                name='shield1')
        obj.setLastUse()
        assert obj.getLastUse() != getNeverDate(), dateStr(obj.getLastUse)
        assert obj.isCool(), dateStr(obj.getLastUse())
        obj._cooldown = 60
        assert not obj.isCool(), (dateStr(obj.getLastUse()) + " - " +
                                  str(obj._cooldown))
        obj._cooldown = 0

        # test repair on typical targe charge devices
        obj.setMaxCharges(100)
        assert obj.getMaxCharges()
        obj.setCharges(50)
        assert obj.percentOfChargesRemaining() == 50
        assert not obj.canBeRepaired()
        obj.setCharges(10)
        origCharges = 10
        assert obj.canBeRepaired()
        obj.repair()
        assert obj.getCharges() > origCharges

        # Test repair on small charge devices
        obj.setMaxCharges(5)
        obj.setCharges(2)
        assert not obj.canBeRepaired()
        obj.setCharges(1)
        origCharges = 1
        assert obj.canBeRepaired()
        obj.repair()
        assert obj.getCharges() > origCharges

        # Test canBeRepaired on broken and depleted devices
        obj.setMaxCharges(500)
        obj.setCharges(1)
        obj.decrementChargeCounter()
        assert obj.isBroken()
        assert obj.isDepleated()
        assert not obj.canBeRepaired()
        obj._broken = True
        assert not obj.canBeRepaired()

        # Test that value drops depending on charges
        obj._broken = False
        obj._value = 5000
        obj.setMaxCharges(100)
        obj.setCharges(10)
        assert obj.adjustPrice(5000) == 500

    def testEquippable(self):
        obj = self.createObject(num=self.testObjNumber,
                                type='Shield',
                                name='shield1')

        assert obj.isUsable()
        assert obj.isEquippable()
        assert obj.getEquippedSlotName() == '_equippedShield'
        obj.setEquippedSlotName('bubble')
        assert obj.getEquippedSlotName() == 'bubble'

    def testMagicDevice(self):
        charObj = self.getCharObj()
        obj = self.createObject(num=self.testObjNumber,
                                type='Scroll',
                                name='scroll1')
        assert obj.isMagicItem()
        obj._spell = 'fireball'
        assert obj.getSpellName() == 'fireball'
        obj.cast(charObj, charObj)
        msg = charObj.client.popOutSpool()
        logger.info('\n' + msg)
        assert 'You cast fireball' in msg.split('\n')

    def testTrapTxt(self):
        inputs = [(1, False, 150),
                  (22, False, 150),
                  (69, False, 150),
                  (135, False, 150),
                  (135, False, 50),
                  (9, True, 150),
                  (21, True, 150),
                  (80, True, 150),
                  ]
        outputs = ["Splinters on your hand!",
                   "Putrid dust sprays in your eyes!",
                   "Blam!  Explosion in your face!",
                   "Boooooom!",
                   "Tons of rocks tumble down upon you!",
                   "Poison dart!",
                   "Cobra lunges at you!",
                   "Gas spores explode!"
                   ]
        for num, input in enumerate(inputs):
            obj1 = self.createObject(num=self.testObjNumber,
                                     type='Door',
                                     name='door1')
            result = obj1.trapTxt(inputs[num][0], inputs[num][1],
                                  inputs[num][2])
            out = ("Input: " + str(inputs[num]) + " - Output: " + str(result) +
                   " - Expected: " + str(outputs[num]))
            status = bool(result == outputs[num])
            self.assertEqual(status, True, out)

    def testObjLoad(self):
        objNumber = 1
        for num, oneType in enumerate(ObjFactoryTypes,
                                      start=self.testObjNumber):
            if oneType.lower() == 'object':
                continue
            obj = self.createObject(num=objNumber,
                                    type=oneType,
                                    name=(oneType + str(num)))
            obj.load()

    def testContainer(self):
        box = self.createObject(num=99999,
                                type='Container',
                                name='box')
        axe = self.createObject(num=99998,
                                type='Weapon',
                                name='Axe')
        pin = self.createObject(num=99997,
                                type='Treasure',
                                name='Pin')
        charObj = self.createCharacter(name='Smoochie')
        charObj.addToInventory(axe)
        box.addToInventory(pin)
        logger.info(box.examine())
        assert re.search('Pin', box.examine())
        assert not re.search('Axe', box.examine())
        assert not box.deposit(charObj, pin, saveItem=False)
        assert box.deposit(charObj, axe, saveItem=False)
        logger.info(box.examine())
        assert box.getWeight() > box.getContainerWeight()
        assert re.search('Axe', box.examine())
        assert re.search('Pin', box.examine())
        assert box.withdraw(charObj, pin, saveItem=False)
        logger.info(box.examine())
        assert not box.withdraw(charObj, pin, saveItem=False)
        assert not box.withdraw(charObj, None, saveItem=False)
        assert not box.deposit(charObj, None, saveItem=False)
        box.close(charObj, saveItem=False)
        logger.info(box.examine())
        assert not box.deposit(charObj, axe, saveItem=False)


if __name__ == '__main__':
    unittest.main()
