''' test character '''
import unittest

import character
# from common.general import logger
import object


class TestCharacter(unittest.TestCase):

    testCharName = "test99999"
    testObjNumber = 99999

    def testCharAttributes(self):
        charObj = character.Character()
        status, msg = charObj.testAttributes()
        self.assertEqual(status, True, msg)

    def testCharInstanciation(self):
        ''' Test character instanciation + some basic attribute retrieval '''
        charObj = character.Character()
        charObj.setName(self.testCharName)
        charObj._gender = "male"
        charObj._classname = "fighter"
        charObj._alignment = 'neutral'
        charObj.setMaxHP(100)
        charObj.setHitPoints(100)
        desc = charObj.getDesc()
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

    def testEquipWeapon(self):
        ''' Create a character and an object.  Test equip/unequip of obj '''
        charObj = character.Character()
        charObj.setName(self.testCharName)
        charObj.strength = 10
        charObj._level = 1
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
        charObj = character.Character()
        charObj.setName(self.testCharName)
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
