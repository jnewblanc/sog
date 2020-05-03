''' magic info '''    # noqa

# A player must learn a spell before casting it, either by being taught the
# spell or by examining a scroll. Once learned a spell is not forgotten.
# The player must also type in the chant for a spell to cast it, which means
# the player must also find out what the chant is.

import pprint
import random      # noqa: F401

from common.general import dLog, logger
from common.ioLib import TestIo

SpellDict = {
    'none': {
        'desc': '',
        'chant': '',
        'spellTargets': [],
        'spellType': '',
        'targetSelf': False,
        'limitedNumberPerDay': False,
        'mana': 1,
        'intRequired': 1,
        'formula': '',
        'formulaResultAtt': '',
        'levelRequired': {
            'mage': 1,
            'fighter': 1,
            'rogue': 1,
            'cleric': 1,
            'ranger': 1,
            'paladin': 1,
        },
    },
    'vigor': {
        'desc': 'Restores 5 * caster_level fatigue points',
        'chant': 'I return vigor',
        'spellType': 'health',
        'spellTargets': ['Character', 'Creature'],
        'targetSelf': True,
        'limitedNumberPerDay': False,
        'mana': 3,
        'intRequired': 10,
        'formula': '-5 * self.charObj.getLevel()',
        'formulaResultAtt': 'health',
        'levelRequired': {
            'mage': 1,
            'fighter': 1,
            'rogue': 1,
            'cleric': 1,
            'ranger': 1,
            'paladin': 1,
        },
    },
    'heal': {
        'desc': 'Restores 12 * caster_level fatigue points',
        'chant': 'Thy wounds are mended!',
        'spellType': 'health',
        'spellTargets': ['Character', 'Creature'],
        'targetSelf': True,
        'limitedNumberPerDay': False,
        'mana': 6,
        'intRequired': 10,
        'formula': '-12 * self.charObj.getLevel()',
        'formulaResultAtt': 'health',
        'levelRequired': {
            'mage': 8,
            'fighter': 8,
            'rogue': 8,
            'cleric': 4,
            'ranger': 8,
            'paladin': 6,
        },
    },
    'fireball': {
        'desc': 'Attack spell, min(3 * (lvl+1), int * 2) hp',
        'chant': 'Ball of fire fly to thee!',
        'spellType': 'damage',
        'spellTargets': ['Character', 'Creature'],
        'targetSelf': False,
        'limitedNumberPerDay': False,
        'mana': 10,
        'intRequired': 11,
        'formula': ('min(3 * (self.charObj.getLevel() + 1), ' +
                    'self.charObj.getIntelligence() * 2)'),
        'formulaResultAtt': 'damage',
        'levelRequired': {
            'mage': 2,
            'fighter': 6,
            'rogue': 5,
            'cleric': 3,
            'ranger': 4,
            'paladin': 4,
        },
    },
    'lightning': {
        'desc': 'Attack spell, min(20 + 2 * (lvl+1)) hp.',
        'chant': 'I command you to glow with energy!',
        'spellType': 'damage',
        'spellTargets': ['Character', 'Creature'],
        'targetSelf': False,
        'limitedNumberPerDay': False,
        'mana': 15,
        'intRequired': 13,
        'formula': ('min(20 + (2 * (self.charObj.getLevel() + 1)), ' +
                    'self.charObj.getIntelligence() * 2)'),
        'formulaResultAtt': 'damage',
        'levelRequired': {
            'mage': 4,
            'fighter': 8,
            'rogue': 7,
            'cleric': 5,
            'ranger': 6,
            'paladin': 6,
        },
    },
    'hurt': {
        'desc': 'Attack spell, 1-3 hp',
        'chant': 'Ouch! That hurt!',
        'spellType': 'damage',
        'spellTargets': ['Character', 'Creature'],
        'targetSelf': True,
        'limitedNumberPerDay': False,
        'mana': 6,
        'intRequired': 10,
        'formula': 'random.randint(1, 3)',
        'formulaResultAtt': 'damage',
        'levelRequired': {
            'mage': 1,
            'fighter': 1,
            'rogue': 1,
            'cleric': 1,
            'ranger': 1,
            'paladin': 1,
        },
    },
    'disintegrate': {
        'desc': 'Most powerful attack spell, lvl * 2 + ran(5 * int)',
        'chant': 'I disrupt they molecular structure!',
        'spellType': 'damage',
        'spellTargets': ['Character', 'Creature'],
        'targetSelf': False,
        'limitedNumberPerDay': True,
        'mana': 20,
        'intRequired': 14,
        'formula': ('(self.charObj.getLevel() * 2) + ' +
                    'random.randint(1 , 5 * self.charObj.getIntelligence())'),
        'formulaResultAtt': 'damage',
        'levelRequired': {
            'mage': 7,
            'fighter': 0,
            'rogue': 0,
            'cleric': 0,
            'ranger': 0,
            'paladin': 0,
        },
    },
    'turn': {
        'desc': 'Exorcise or dispell undead - target must be =< level',
        'chant': '',
        'spellType': 'slay',
        'spellTargets': ['Creature'],
        'targetSelf': False,
        'limitedNumberPerDay': False,
        'mana': 10,
        'intRequired': 9,
        'formula': '',
        'formulaResultAtt': '',
        'levelRequired': {
            'mage': 0,
            'fighter': 0,
            'rogue': 0,
            'cleric': 1,
            'ranger': 0,
            'paladin': 0,
        },
    },
    'curepoison': {
        'desc': 'Cures player of poison.',
        'chant': 'Let thy fluids run pure!',
        'spellType': 'alteration',
        'spellTargets': ['Character'],
        'targetSelf': True,
        'limitedNumberPerDay': False,
        'mana': 6,
        'intRequired': 9,
        'formula': '',
        'formulaResultAtt': '',
        'levelRequired': {
            'mage': 1,
            'fighter': 1,
            'rogue': 1,
            'cleric': 1,
            'ranger': 1,
            'paladin': 1,
        },
    },
    'befuddle': {
        'desc': 'player= paused 30 secs; monster = paused 3 * MONSPEED secs',
        'chant': 'Be thou confused utterly!',
        'spellType': 'alteration',
        'spellTargets': ['Character', 'Creature'],
        'targetSelf': False,
        'mana': 15,
        'limitedNumberPerDay': False,
        'intRequired': 11,
        'formula': '',
        'formulaResultAtt': '',
        'levelRequired': {
            'mage': 1,
            'fighter': 5,
            'rogue': 4,
            'cleric': 2,
            'ranger': 3,
            'paladin': 3,
        },
    },
    'teleport': {
        'desc': 'Randomly transported to a room# 30-300',
        'chant': 'Let me go to someplace new!',
        'spellType': 'room',
        'spellTargets': ['Character'],
        'targetSelf': True,
        'mana': 30,
        'limitedNumberPerDay': False,
        'intRequired': 14,
        'formula': 'random.randint(30, 300)',
        'formulaResultAtt': 'roomNum',
        'levelRequired': {
            'mage': 9,
            'fighter': 11,
            'rogue': 11,
            'cleric': 10,
            'ranger': 10,
            'paladin': 11,
        },
    },
    'passdoor': {
        'desc': 'Passes through any door where MAGIC=false',
        'chant': 'I refuse to be stopped!',
        'spellType': 'room',
        'spellTargets': ['Door'],
        'targetSelf': False,
        'limitedNumberPerDay': False,
        'mana': 20,
        'intRequired': 13,
        'formula': '',
        'formulaResultAtt': '',
        'levelRequired': {
            'mage': 5,
            'fighter': 9,
            'rogue': 8,
            'cleric': 6,
            'ranger': 7,
            'paladin': 7,
        },
    },
    'enchant': {
        'desc': 'Makes object magical; it must be carryable. doesnt change hp',
        'chant': 'I infuse you with magical dweomer!',
        'spellType': 'alteration',
        'spellTargets': ['Weapon', 'Armor', 'Shield'],
        'targetSelf': False,
        'limitedNumberPerDay': True,
        'mana': 20,
        'intRequired': 13,
        'formula': '',
        'formulaResultAtt': '',
        'levelRequired': {
            'mage': 5,
            'fighter': 0,
            'rogue': 0,
            'cleric': 0,
            'ranger': 0,
            'paladin': 0,
        },
    },
    'bless': {
        'desc': '+1 to piety of someone else. Must be equal or lower level.',
        'chant': 'Your soul is now pure again!',
        'spellType': 'alteration',
        'spellTargets': ['Character'],
        'targetSelf': False,
        'limitedNumberPerDay': True,
        'mana': 15,
        'intRequired': 11,
        'formula': '',
        'formulaResultAtt': '',
        'levelRequired': {
            'mage': 0,
            'fighter': 0,
            'rogue': 0,
            'cleric': 1,
            'ranger': 0,
            'paladin': 0,
        },
    },
    'protect': {
        'desc': 'Temporarily improve armor class by 1',
        'chant': 'You are being watched!',
        'spellType': 'alteration',
        'spellTargets': ['Character'],
        'targetSelf': True,
        'limitedNumberPerDay': False,
        'mana': 10,
        'intRequired': 10,
        'formula': '',
        'formulaResultAtt': '',
        'levelRequired': {
            'mage': 1,
            'fighter': 0,
            'rogue': 0,
            'cleric': 0,
            'ranger': 0,
            'paladin': 0,
        },
    },
    'curse': {
        'desc': '-1 to piety of someone else.  Must be <= caster level.',
        'chant': 'I denigrate thee for all to see!',
        'spellType': 'alteration',
        'spellTargets': ['Character', 'Object'],
        'targetSelf': False,
        'limitedNumberPerDay': True,
        'mana': 10,
        'intRequired': 10,
        'formula': '',
        'formulaResultAtt': '',
        'levelRequired': {
            'mage': 0,
            'fighter': 0,
            'rogue': 0,
            'cleric': 6,
            'ranger': 0,
            'paladin': 0,
        },
    },
    'poison': {
        'desc': 'Poison Someone',
        'chant': 'May thy blood fester in thy veins!',
        'spellType': 'alteration',
        'spellTargets': ['Character'],
        'targetSelf': False,
        'limitedNumberPerDay': False,
        'mana': 10,
        'intRequired': 10,
        'formula': '',
        'formulaResultAtt': '',
        'levelRequired': {
            'mage': 8,
            'fighter': 9,
            'rogue': 4,
            'cleric': 4,
            'ranger': 6,
            'paladin': 6,
        },
    },
    'intoxicate': {
        'desc': 'Recipient is drunk for 60 seconds',
        'chant': 'More than one hundred proof!',
        'spellType': 'alteration',
        'spellTargets': ['Character'],
        'targetSelf': True,
        'limitedNumberPerDay': False,
        'mana': 8,
        'intRequired': 9,
        'formula': '',
        'formulaResultAtt': '',
        'levelRequired': {
            'mage': 3,
            'fighter': 7,
            'rogue': 8,
            'cleric': 4,
            'ranger': 5,
            'paladin': 5,
        },
    },
    'identify': {
        'desc': 'Show all the stats of an object or player',
        'chant': 'Show thee thou true nature!',
        'spellType': 'info',
        'spellTargets': ['Character', 'Creature', 'Object'],
        'targetSelf': True,
        'limitedNumberPerDay': True,
        'mana': 20,
        'intRequired': 18,
        'formula': '',
        'formulaResultAtt': '',
        'levelRequired': {
            'mage': 5,
            'fighter': 10,
            'rogue': 8,
            'cleric': 8,
            'ranger': 7,
            'paladin': 10,
        },
    },
    'removecurse': {
        'desc': 'Removes a curse from an item',
        'chant': 'Release thou unholiness.',
        'spellType': 'alteration',
        'spellTargets': ['Character', 'Object'],
        'targetSelf': True,
        'limitedNumberPerDay': True,
        'mana': 20,
        'intRequired': 14,
        'formula': '',
        'formulaResultAtt': '',
        'levelRequired': {
            'mage': 0,
            'fighter': 0,
            'rogue': 0,
            'cleric': 10,
            'ranger': 0,
            'paladin': 10,
        },
    },
    'vuln': {
        'desc': 'Makes target vulnerable (dd) for next attack',
        'chant': 'Be afraid of what is to come.',
        'spellType': 'alteration',
        'spellTargets': ['Character', 'Creature'],
        'targetSelf': False,
        'limitedNumberPerDay': False,
        'mana': 10,
        'intRequired': 13,
        'formula': '',
        'formulaResultAtt': '',
        'levelRequired': {
            'mage': 7,
            'fighter': 12,
            'rogue': 10,
            'cleric': 5,
            'ranger': 4,
            'paladin': 10,
        },
    },
    'appeal': {
        'desc': 'Appeal to gods (DMs) - costs one piety point',
        'chant': 'Let thee rewrite history.',
        'spellType': 'ask',
        'spellTargets': [],
        'targetSelf': False,
        'limitedNumberPerDay': True,
        'mana': 10,
        'intRequired': 12,
        'formula': '',
        'formulaResultAtt': '',
        'levelRequired': {
            'mage': 10,
            'fighter': 10,
            'rogue': 10,
            'cleric': 10,
            'ranger': 10,
            'paladin': 10,
        },
    },
    'wish': {
        'desc': 'Sent to DM; DM then decides',
        'chant': 'This is the last time I want to change this chant!',
        'spellType': 'ask',
        'spellTargets': [],
        'targetSelf': False,
        'limitedNumberPerDay': True,
        'mana': 50,  # Also costs a constitution point
        'intRequired': 17,
        'formula': '',
        'formulaResultAtt': '',
        'levelRequired': {
            'mage': 10,
            'fighter': 0,
            'rogue': 0,
            'cleric': 0,
            'ranger': 0,
            'paladin': 0,
        },
    },
}

SpellList = SpellDict.keys()
# ['psiblast', 'polymorph', 'summon', 'animate', 'charm', 'illuminate']

SpellsThatTargetSelfList = [spellName
                            for spellName in SpellList
                            if (SpellDict[spellName]['targetSelf'])]


def getSpellChant(spellName=''):
    ''' Given a spell name, return the chant '''
    if spellName in SpellList:
        return(SpellDict[spellName]['chant'])


def spellCanTargetSelf(spellName):
    ''' Returns True if given spell name can target self '''
    if spellName in SpellsThatTargetSelfList:
        return(True)
    return(False)


class Spell():
    ''' Spell Class '''
    def __init__(self, charObj, targetObj=None, spellName='', chant='',
                 requiresmana=True):
        self.charObj = charObj
        self.targetObj = targetObj
        self.givenChant = chant   # Enables us to pass in chants for testing

        if charObj.client:
            self._spoolOut = charObj.client.spoolOut
        else:
            testIo = TestIo()
            self._spoolOut = testIo.spoolOut

        if spellName not in SpellDict.keys():
            spellName = 'none'

        self.spellName = spellName

        self._requiresmana = requiresmana

        self._instanceDebug = True

        # Set the spell attributes based on the values in SpellDict
        self.setSpellAttributes()

        self.failedReason = ''
        self.succeeded = self._checkIfSucceeds()
        return(None)

    def setSpellAttributes(self):
        ''' Set this instance's attributes based on the particular spell
            being cast and the corresponding values in SpellDict.
                * Special considerations:
                  - levelRequired - set based on character's className
                  - formulas, we execute them and store the result as
                    an attribute.  We get the attribute name from the
                    formulaResultAtt attribute.  Overly complicated?
                    Maybe, but the object comes out looking clean.
        '''
        for att in SpellDict[self.spellName].keys():
            if att == 'levelRequired':
                className = self.charObj.getClassName()
                setattr(self, att, SpellDict[self.spellName][att][className])
            elif att == 'formula':
                attName = SpellDict[self.spellName]['formulaResultAtt']
                if attName == '':
                    continue
                # execute formula and stick it in an attribute
                dLog('magic: formula = ' + att,
                     self._instanceDebug)
                dLog('magic: level=' + str(self.charObj.getLevel()) +
                     ' - Int=' + str(self.charObj.getIntelligence()),
                     self._instanceDebug)
                setattr(self, attName, eval(SpellDict[self.spellName][att]))
                dLog('magic: spell=' + self.spellName +
                     ' - damage=' + str(getattr(self, attName)),
                     self._instanceDebug)
            elif att == 'formulaResultAtt':
                # This is used for formula results, so don't set it as att
                continue
            else:
                setattr(self, att, SpellDict[self.spellName][att])

    def debug(self):
        return(pprint.pformat(vars(self)))

    def _preCastTasks(self):
        ''' Handle the pre-cast actions '''
        # deduct spell points from charObj
        if self._requiresmana:
            self.charObj.subtractmana(self.mana)

        # record the last attack command
        self.charObj.setLastAttack(cmd=self.spellName)

    def _castFails(self):
        ''' do everything related to failed spells '''

        msg = 'Spell failed!  ' + self.getFailedReason()
        self._spoolOut(msg)
        dLog("magic.castFails: " + msg, self._instanceDebug)
        if self.spellName == 'turn':
            self.charObj.setVulnerable(True)

    def cast(self, roomObj):
        ''' Returns true if spell was sucessfully cast '''

        # Do everything that comes before the spell's affects
        self._preCastTasks()

        if not self.succeeded:
            self._castFails()
            return(False)

        self._spoolOut("You cast " + self.spellName + "\n")

        if not self.targetObj:
            logger.warning("magic.cast: targetObj is not defined")

        if self.spellType == 'health':
            self.targetObj.addHP(self.getHealth())
        elif self.spellType == 'room':
            self.targetObj.joinRoom(self.getRoom())
        elif self.spellType == 'damage':
            self.inflictDamage()
        elif self.spellType == 'alteration':
            self.alterations()
        elif self.spellType == 'info':
            if self.spellName == 'identify':
                self.identify()
            else:
                self._spoolOut("not implemented yet\n")
        elif self.spellType == 'ask':
            self.ask()
        else:
            self._spoolOut("not implemented yet\n")

        return(True)

    def inflictDamage(self):
        ''' Execute actions for spells that cause damage '''
        logger.warning("magic.inflictDamage: " + str(self.targetObj) +
                       " was hit by a " + str(self.damage) + " damage " +
                       self.spellName + " spell from " +
                       self.charObj.getName())
        if self.charObj.client:
            self.charObj.client.gameObj.attackCreature(
                self.charObj, self.targetObj, attackCmd='spell', spellObj=self)
        else:
            logger.warning("magic.inflictDamage could not deal damage - " +
                           "charObj.client == None")

    def identify(self):
        ''' Execute actions for identify spell '''
        # Todo: something nicer than debug
        self._spoolOut(self.targetObj.debug())
        self.charObj.reduceLimitedSpellCount()

    def alterations(self):
        ''' Execute actions for alteration spells '''
        self._spoolOut("not implemented yet\n")

    def ask(self):
        ''' Execute actions for ask spells '''
        self._spoolOut("not implemented yet\n")

    def getHealth(self):
        ''' Returns health or 0 '''
        if hasattr(self, 'health'):
            return(self.health)
        return(0)

    def getDamage(self):   # used in Combat
        ''' Returns damage or 0 '''
        if hasattr(self, 'damage'):
            return(self.damage)
        return(0)

    def getRoom(self):
        ''' Returns room or 1 '''
        if hasattr(self, 'room'):
            return(self.room)
        return(1)

    def getFailedReason(self):
        return(self.failedReason)

    def _checkIfSucceeds(self):
        ''' Returns true if spell is sucessful '''
        if not self._selfCriteriaAreMet():
            return(False)
        if not self._targetCriteriaAreMet():
            return(False)
        if not self._promptForChant():
            return(False)
        return(True)

    def _promptForChant(self):
        ''' Prompts player for chant.  Returns true if chant is correct '''
        if self.chant == '':
            # empty chant means none is required
            return(True)

        if self.givenChant == '':
            prompt = "Enter Chant: "
            playerInput = self.charObj.client.promptForInput(prompt)
        else:
            playerInput = self.givenChant

        # Test if chant is correct
        if playerInput.lower() == self.chant.lower():
            return(True)

        msg = "The divine are unimpressed with your chant"
        self.failedReason += msg + '\n'

        dLog("_promptForChant Failed: bad chant", self._instanceDebug)
        return(False)

    def _selfCriteriaAreMet(self):
        logPrefix = "magic.selfCriteria: Failed - "
        cName = self.charObj.getName()
        if not self.charObj.canAttack():
            msg = "You can't attack"
            self.failedReason += msg + '\n'
            dLog(logPrefix + msg + ', ' + cName, self._instanceDebug)
            return(False)
        if self.levelRequired < 1:
            msg = "You can't cast " + self.spellName
            self.failedReason += msg + '\n'
            dLog(logPrefix + msg + ', ' + cName, self._instanceDebug)
            return(False)
        if self.charObj.getLevel() < self.levelRequired:
            msg = ("a level " + str(self.charObj.getLevel()) + ' ' +
                   self.charObj.getClassName() + ' can not cast ' +
                   self.spellName + ' which requires level ' +
                   str(self.levelRequired))
            self.failedReason += msg + '\n'
            dLog(logPrefix + msg + ', ' + cName, self._instanceDebug)
            return(False)
        if ((self.limitedNumberPerDay and not
             self.charObj.getLimitedSpellCount())):
            msg = "You have used all of your limited spells for today"
            self.failedReason += msg + '\n'
            dLog(logPrefix + msg + ', ' + cName, self._instanceDebug)
            return(False)
        if ((self._requiresmana and
             self.charObj.getmana() < self.mana)):
            msg = "You don't have enough mana for that"
            self.failedReason += msg + '\n'
            dLog(logPrefix + msg + '(char=' + str(self.charObj.getmana()) +
                 ' spell=' + str(self.mana) + ')' + ', ' +
                 cName, self._instanceDebug)
            return(False)
        return(True)

    def _targetCriteriaAreMet(self):
        logPrefix = "magic.targetCriteria: Failed - "
        cName = self.charObj.getName()
        if self.targetObj.isMagic():
            msg = "magical target can not be affected by spell"
            self.failedReason += msg + '\n'
            dLog(logPrefix + msg + ', ' + cName, self._instanceDebug)
            return(False)
        spellTargets = SpellDict[self.spellName]['spellTargets']
        if self.targetObj.getType() not in spellTargets:
            msg = (self.targetObj.getType() + " is not a valid target for " +
                   "spell " + self.spellName)
            self.failedReason += msg + '\n'
            dLog(logPrefix + msg + ', ' + cName, self._instanceDebug)
            return(False)
        return(True)
