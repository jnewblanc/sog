''' test_magic '''   # noqa
# import re
import unittest

# from common.general import logger
import character
from common.test import TestGameBase
import creature
import object
import room
import magic


class TestMagic(TestGameBase):

    characterClasses = character.Character.classList
    testCreatureNumber = 99999
    testObjNumber = 99999
    _testAcctName = "sogTest@gadgetshead.com"

    def setUp(self):
        self.banner('start', testName=__class__.__name__)

        # Create one character of each classtype.
        # Store them in a dict with classname as the keys
        self.charDict = {}
        for oneClass in self.characterClasses:
            charObj = character.Character(acctName=self._testAcctName)
            charObj.setName('test' + oneClass.capitalize())
            charObj.setGender("male")
            charObj.setClassName(oneClass)
            charObj.setAlignment('neutral')
            charObj.setMana(10000)
            charObj.setLevel(10)
            charObj.intelligence = 20
            self.charDict[oneClass] = charObj

        # Set up targets for the spells
        self.targetCharObj = charObj
        self.targetCreaObj = creature.Creature(self.testCreatureNumber)
        self.targetDoorObj = object.Door(self.testObjNumber)
        self.roomObj = room.Room(99999)

    def testDamageSpells(self):
        spells = ['fireball', 'lightning', 'hurt', 'disintegrate']
        target = self.targetCharObj
        for charClass in self.charDict.keys():
            charObj = self.charDict[charClass]
            for level in [1, 3, 7, 10]:
                charObj.setLevel(level)
                for spellName in spells:
                    chant = magic.getSpellChant(spellName)
                    spellObj = magic.Spell(charObj, target, spellName, chant)
                    msg = ('testDamageSpells - class=' + charClass +
                           ' - level=' + str(level) +
                           ' - spell=' + spellName +
                           ' - damage=' + str(spellObj.damage))
                    assert spellObj.damage != 0, msg

    def testHealthSpells(self):
        spells = ['vigor', 'heal']
        target = self.targetCharObj
        for charClass in self.charDict.keys():
            charObj = self.charDict[charClass]
            for level in [1, 3, 7, 10]:
                charObj.setLevel(level)
                for spellName in spells:
                    chant = magic.getSpellChant(spellName)
                    spellObj = magic.Spell(charObj, target, spellName, chant)
                    msg = ('testHealthSpells - class=' + charClass +
                           ' - level=' + str(level) +
                           ' - spell=' + spellName +
                           ' - damage=' + str(spellObj.health))
                    assert spellObj.health != 0, msg

    def testDoorSpells(self):
        spells = ['passdoor']
        target = self.targetCharObj
        for charClass in self.charDict.keys():
            charObj = self.charDict[charClass]
            for level in [1, 3, 7, 10]:
                charObj.setLevel(level)
                for spellName in spells:
                    chant = magic.getSpellChant(spellName)
                    spellObj = magic.Spell(charObj, target, spellName, chant)
                    msg = ('testDoorSpells - class=' + charClass +
                           ' - level=' + str(level) +
                           ' - spell=' + spellName +
                           ' - succeeded=' + str(spellObj.succeeded))
                    # assert spellObj.succeeded != 0, msg
                    msg = msg  # remove when we complete the assert

    def testFailedChants(self):
        spells = magic.SpellList
        charObj = self.charDict.get('mage')
        target = self.targetCharObj
        chant = "I don't know the chant"
        for spellName in spells:
            if spellName == '':
                continue
            spellObj = magic.Spell(charObj, target, spellName, chant)
            assert not spellObj.succeeded

    def testMana(self):
        spells = ['vigor', 'heal',
                  'fireball', 'lightning', 'hurt', 'disintegrate',
                  'curepoison', 'befuddle', 'teleport', 'protect',
                  'poison', 'intoxicate', 'vuln']
        badMana = 1
        goodMana = 99
        charObj = self.charDict.get('mage')
        target = self.targetCharObj
        for spellName in spells:
            if spellName == '':
                continue
            charObj.setMana(goodMana)
            chant = magic.getSpellChant(spellName)
            # cast with plenty of mana - should pass
            spellObj = magic.Spell(charObj, target, spellName, chant)
            msg = ("ManaPass: spell=" + spellName + " - charHas=" +
                   str(charObj.getMana()) + " - spellReq: " +
                   str(spellObj.getMana()))
            assert spellObj.succeeded, msg

            # cast with insufficient mana - should fail
            charObj.setMana(badMana)
            spellObj = magic.Spell(charObj, target, spellName, chant)
            msg = ("ManaFail: spell=" + spellName + " - charHas=" +
                   str(charObj.getMana()) + " - spellReq: " +
                   str(spellObj.getMana()))
            assert not spellObj.succeeded, msg

    def testBadTargets(self):
        spells = ['passdoor', 'enchant']
        badTargets = [self.targetCharObj, self.targetCreaObj]
        charObj = self.charDict.get('mage')
        charObj.setLevel(10)
        for spellName in spells:
            chant = magic.getSpellChant(spellName)
            for target in badTargets:
                spellObj = magic.Spell(charObj, target, spellName, chant)
                assert not spellObj.cast(charObj)
        spells = ['vigor', 'heal',
                  'fireball', 'lightning', 'hurt', 'disintegrate', 'turn',
                  'curepoison', 'befuddle', 'teleport', 'enchant',
                  'bless', 'protect', 'curse', 'poison', 'intoxicate',
                  'vuln']
        badTargets = [self.targetDoorObj]
        for spellName in spells:
            chant = magic.getSpellChant(spellName)
            for target in badTargets:
                spellObj = magic.Spell(charObj, target, spellName, chant)
                assert not spellObj.cast(charObj)

    def testBadLevels(self):
        spells = ['lightning', 'identify', 'disintegrate']
        goodLvls = {
            'mage': {
                'lightning': [4, 7, 10],
                'identify': [5, 7, 10],
                'disintegrate': [7, 10],
            },
            'fighter': {
                'lightning': [8, 10],
                'identify': [10],
                'disintegrate': [],
            },
        }
        badLvls = {
            'mage': {
                'lightning': [1, 3],
                'identify': [1, 4],
                'disintegrate': [1, 3, 6],
            },
            'fighter': {
                'lightning': [1, 3, 7],
                'identify': [1, 4, 9],
                'disintegrate': [1, 100],
            },
        }
        target = self.targetCharObj
        for className in goodLvls.keys():
            charObj = self.charDict.get(className)
            for spellName in spells:
                chant = magic.getSpellChant(spellName)
                for level in goodLvls[className][spellName]:
                    charObj.setLevel(level)
                    spellObj = magic.Spell(charObj, target, spellName, chant)
                    lvlReq = str(spellObj.levelRequired)
                    assert spellObj.cast(charObj), (
                        "level " + str(charObj.getLevel()) + " " +
                        charObj.getClassName() + " should be able to cast " +
                        spellObj.spellName + " which requires level " +
                        str(lvlReq) + '\n' + spellObj.debug())
                for level in badLvls[className][spellName]:
                    charObj.setLevel(level)
                    spellObj = magic.Spell(charObj, target, spellName, chant)
                    lvlReq = str(spellObj.levelRequired)
                    assert not spellObj.cast(charObj), (
                        "level " + str(charObj.getLevel()) + " " +
                        charObj.getClassName() + " should not be able to " +
                        "cast " + spellObj.spellName +
                        " which requires level " + str(lvlReq))

    # def testIntRequired(self):
    #     spells = ['hurt', 'identify']


if __name__ == '__main__':
    unittest.main()
