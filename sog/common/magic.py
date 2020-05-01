''' magic info '''    # noqa

# A player must learn a spell before casting it, either by being taught the
# spell or by examining a scroll. Once learned a spell is not forgotten.
# The player must also type in the chant for a spell to cast it, which means
# the player must also find out what the chant is.

import random      # noqa: F401

from common.general import dLog


SpellDict = {
    'none': {
        'desc': '',
        'chant': '',
        'spellTargets': [],
        'limitedNumberPerDay': False,
        'magicPoints': 1,
        'intRequired': 1,
        'levelRequired': {
            'mage': 1,
            'fighter': 1,
            'rogue': 1,
            'cleric': 1,
            'ranger': 1,
            'paladin': 1,
        },
        'formula': '',
        'formulaResultAtt': ''
    },
    'vigor': {
        'desc': 'Restores 5 * caster_level fatigue points',
        'chant': 'I return vigor',
        'spellTargets': ['Character', 'Creature'],
        'limitedNumberPerDay': False,
        'magicPoints': 3,
        'intRequired': 10,
        'levelRequired': {
            'mage': 1,
            'fighter': 1,
            'rogue': 1,
            'cleric': 1,
            'ranger': 1,
            'paladin': 1,
        },
        'formula': '-5 * self.charObj.getLevel()',
        'formulaResultAtt': 'health'
    },
    'heal': {
        'desc': 'Restores 12 * caster_level fatigue points',
        'chant': 'Thy wounds are mended!',
        'spellTargets': ['Character', 'Creature'],
        'limitedNumberPerDay': False,
        'magicPoints': 6,
        'intRequired': 10,
        'levelRequired': {
            'mage': 0,
            'fighter': 0,
            'rogue': 0,
            'cleric': 2,
            'ranger': 0,
            'paladin': 0,
        },
        'formula': '-12 * self.charObj.getLevel()',
        'formulaResultAtt': 'health'
    },
    'fireball': {
        'desc': 'Attack spell, min(3 * (lvl+1), int * 2) hp',
        'chant': 'Ball of fire fly to thee!',
        'spellTargets': ['Character', 'Creature'],
        'limitedNumberPerDay': False,
        'magicPoints': 10,
        'intRequired': 11,
        'levelRequired': {
            'mage': 2,
            'fighter': 6,
            'rogue': 5,
            'cleric': 3,
            'ranger': 4,
            'paladin': 4,
        },
        'formula': ('min(3 * (self.charObj.getLevel() + 1), ' +
                    'self.charObj.getIntelligence() * 2)'),
        'formulaResultAtt': 'damage'
    },
    'lightning': {
        'desc': 'Attack spell, min(20 + 2 * (lvl+1)) hp.',
        'chant': 'I command you to glow with energy!',
        'spellTargets': ['Character', 'Creature'],
        'limitedNumberPerDay': False,
        'magicPoints': 15,
        'intRequired': 13,
        'levelRequired': {
            'mage': 4,
            'fighter': 8,
            'rogue': 7,
            'cleric': 5,
            'ranger': 6,
            'paladin': 6,
        },
        'formula': ('min(20 + (2 * (self.charObj.getLevel() + 1)), ' +
                    'self.charObj.getIntelligence() * 2)'),
        'formulaResultAtt': 'damage'
    },
    'hurt': {
        'desc': 'Attack spell, 1-3 hp',
        'chant': 'Ouch! That hurt!',
        'spellTargets': ['Character', 'Creature'],
        'limitedNumberPerDay': False,
        'magicPoints': 6,
        'intRequired': 10,
        'levelRequired': {
            'mage': 1,
            'fighter': 1,
            'rogue': 1,
            'cleric': 1,
            'ranger': 1,
            'paladin': 1,
        },
        'formula': 'random.randint(1, 3)',
        'formulaResultAtt': 'damage'
    },
    'disintegrate': {
        'desc': 'Most powerful attack spell, lvl * 2 + ran(5 * int)',
        'chant': 'I disrupt they molecular structure!',
        'spellTargets': ['Character', 'Creature'],
        'limitedNumberPerDay': True,
        'magicPoints': 20,
        'intRequired': 14,
        'levelRequired': {
            'mage': 7,
            'fighter': 0,
            'rogue': 0,
            'cleric': 0,
            'ranger': 0,
            'paladin': 0,
        },
        'formula': ('(self.charObj.getLevel() * 2) + ' +
                    'random.randint(1 , 5 * self.charObj.getIntelligence())'),
        'formulaResultAtt': 'damage'
    },
    'turn': {
        'desc': 'Exorcise or dispell undead - target must be =< level',
        'chant': '',
        'spellTargets': ['Creature'],
        'limitedNumberPerDay': False,
        'magicPoints': 10,
        'intRequired': 9,
        'levelRequired': {
            'mage': 0,
            'fighter': 0,
            'rogue': 0,
            'cleric': 1,
            'ranger': 0,
            'paladin': 0,
        },
        'formula': '',
        'formulaResultAtt': ''
    },
    'curepoison': {
        'desc': 'Cures player of poison.',
        'chant': 'Let thy fluids run pure!',
        'spellTargets': ['Character'],
        'limitedNumberPerDay': False,
        'magicPoints': 6,
        'intRequired': 9,
        'levelRequired': {
            'mage': 1,
            'fighter': 1,
            'rogue': 1,
            'cleric': 1,
            'ranger': 1,
            'paladin': 1,
        },
        'formula': '',
        'formulaResultAtt': ''
    },
    'befuddle': {
        'desc': 'player= paused 30 secs; monster = paused 3 * MONSPEED secs',
        'chant': 'Be thou confused utterly!',
        'spellTargets': ['Character', 'Creature'],
        'magicPoints': 15,
        'limitedNumberPerDay': False,
        'intRequired': 11,
        'levelRequired': {
            'mage': 1,
            'fighter': 5,
            'rogue': 4,
            'cleric': 2,
            'ranger': 3,
            'paladin': 3,
        },
        'formula': '',
        'formulaResultAtt': ''
    },
    'teleport': {
        'desc': 'Randomly transported to a room# 30-300',
        'chant': 'Let me go to someplace new!',
        'spellTargets': ['Character'],
        'magicPoints': 30,
        'limitedNumberPerDay': False,
        'intRequired': 14,
        'levelRequired': {
            'mage': 9,
            'fighter': 11,
            'rogue': 11,
            'cleric': 10,
            'ranger': 10,
            'paladin': 11,
        },
        'formula': 'random.randint(30, 300)',
        'formulaResultAtt': 'roomNum'
    },
    'passdoor': {
        'desc': 'Passes through any door where MAGIC=false',
        'chant': 'I refuse to be stopped!',
        'spellTargets': ['Door'],
        'limitedNumberPerDay': False,
        'magicPoints': 20,
        'intRequired': 13,
        'levelRequired': {
            'mage': 5,
            'fighter': 9,
            'rogue': 8,
            'cleric': 6,
            'ranger': 7,
            'paladin': 7,
        },
        'formula': '',
        'formulaResultAtt': ''
    },
    'enchant': {
        'desc': 'Makes object magical; it must be carryable. doesnt change hp',
        'chant': 'I infuse you with magical dweomer!',
        'spellTargets': ['Weapon', 'Armor', 'Shield'],
        'limitedNumberPerDay': True,
        'magicPoints': 20,
        'intRequired': 13,
        'levelRequired': {
            'mage': 5,
            'fighter': 0,
            'rogue': 0,
            'cleric': 0,
            'ranger': 0,
            'paladin': 0,
        },
        'formula': '',
        'formulaResultAtt': ''
    },
    'bless': {
        'desc': '+1 to piety of someone else. Must be equal or lower level.',
        'chant': 'Your soul is now pure again!',
        'spellTargets': ['Character'],
        'limitedNumberPerDay': True,
        'magicPoints': 15,
        'intRequired': 11,
        'levelRequired': {
            'mage': 0,
            'fighter': 0,
            'rogue': 0,
            'cleric': 1,
            'ranger': 0,
            'paladin': 0,
        },
        'formula': '',
        'formulaResultAtt': ''
    },
    'protect': {
        'desc': 'Temporarily improve armor class by 1',
        'chant': 'You are being watched!',
        'spellTargets': ['Character'],
        'limitedNumberPerDay': False,
        'magicPoints': 10,
        'intRequired': 10,
        'levelRequired': {
            'mage': 1,
            'fighter': 0,
            'rogue': 0,
            'cleric': 0,
            'ranger': 0,
            'paladin': 0,
        },
        'formula': '',
        'formulaResultAtt': ''
    },
    'curse': {
        'desc': '-1 to piety of someone else.  Must be <= caster level.',
        'chant': 'I denigrate thee for all to see!',
        'spellTargets': ['Character', 'Object'],
        'limitedNumberPerDay': True,
        'magicPoints': 10,
        'intRequired': 10,
        'levelRequired': {
            'mage': 0,
            'fighter': 0,
            'rogue': 0,
            'cleric': 6,
            'ranger': 0,
            'paladin': 0,
        },
        'formula': '',
        'formulaResultAtt': ''
    },
    'poison': {
        'desc': 'Poison Someone',
        'chant': 'May thy blood fester in thy veins!',
        'spellTargets': ['Character'],
        'limitedNumberPerDay': False,
        'magicPoints': 10,
        'intRequired': 10,
        'levelRequired': {
            'mage': 7,
            'fighter': 9,
            'rogue': 5,
            'cleric': 5,
            'ranger': 6,
            'paladin': 6,
        },
        'formula': '',
        'formulaResultAtt': ''
    },
    'intoxicate': {
        'desc': 'Recipient is drunk for 60 seconds',
        'chant': 'More than one hundred proof!',
        'spellTargets': ['Character'],
        'limitedNumberPerDay': False,
        'magicPoints': 8,
        'intRequired': 9,
        'levelRequired': {
            'mage': 3,
            'fighter': 7,
            'rogue': 8,
            'cleric': 4,
            'ranger': 5,
            'paladin': 5,
        },
        'formula': '',
        'formulaResultAtt': ''
    },
    'identify': {
        'desc': 'Show all the stats of an object or player',
        'chant': 'Show thee thou true nature!',
        'spellTargets': ['Character', 'Creature', 'Object'],
        'limitedNumberPerDay': True,
        'magicPoints': 20,
        'intRequired': 18,
        'levelRequired': {
            'mage': 5,
            'fighter': 10,
            'rogue': 8,
            'cleric': 8,
            'ranger': 7,
            'paladin': 10,
        },
        'formula': '',
        'formulaResultAtt': ''
    },
    'removecurse': {
        'desc': 'Removes a curse from an item',
        'chant': 'Release thou unholiness.',
        'spellTargets': ['Character', 'Object'],
        'limitedNumberPerDay': True,
        'magicPoints': 20,
        'intRequired': 14,
        'levelRequired': {
            'mage': 0,
            'fighter': 0,
            'rogue': 0,
            'cleric': 10,
            'ranger': 0,
            'paladin': 10,
        },
        'formula': '',
        'formulaResultAtt': ''
    },
    'vuln': {
        'desc': 'Makes target vulnerable (dd) for next attack',
        'chant': 'Be afraid of what is to come.',
        'spellTargets': ['Character', 'Creature'],
        'limitedNumberPerDay': False,
        'magicPoints': 10,
        'intRequired': 13,
        'levelRequired': {
            'mage': 7,
            'fighter': 12,
            'rogue': 10,
            'cleric': 5,
            'ranger': 4,
            'paladin': 10,
        },
        'formula': '',
        'formulaResultAtt': ''
    },
    'appeal': {
        'desc': 'Appeal to gods (DMs) - costs one piety point',
        'chant': 'Let thee rewrite history.',
        'spellTargets': [],
        'limitedNumberPerDay': True,
        'magicPoints': 10,
        'intRequired': 12,
        'levelRequired': {
            'mage': 10,
            'fighter': 10,
            'rogue': 10,
            'cleric': 10,
            'ranger': 10,
            'paladin': 10,
        },
        'formula': '',
        'formulaResultAtt': ''
    },
    'wish': {
        'desc': 'Sent to DM; DM then decides',
        'chant': 'This is the last time I want to change this chant!',
        'spellTargets': [],
        'limitedNumberPerDay': True,
        'magicPoints': 50,  # Also costs a constitution point
        'intRequired': 17,
        'levelRequired': {
            'mage': 10,
            'fighter': 0,
            'rogue': 0,
            'cleric': 0,
            'ranger': 0,
            'paladin': 0,
        },
        'formula': '',
        'formulaResultAtt': ''
    },
}

SpellList = SpellDict.keys()
# ['psiblast', 'polymorph', 'summon', 'animate', 'charm', 'illuminate']


def getSpellChant(spellName=''):
    ''' Given a spell name, return the chant '''
    if spellName in SpellList:
        return(SpellDict[spellName]['chant'])


class Spell():
    ''' Spell Class '''
    def __init__(self, charObj, targetObj, spellName='', chant=''):
        self.charObj = charObj
        self.targetObj = targetObj
        self.givenChant = chant   # Enables us to pass in chants for testing

        if spellName not in SpellDict.keys():
            spellName = 'none'

        self.spellName = spellName

        self._instanceDebug = False

        # Set attributes based on particular spell
        for att in SpellDict[spellName].keys():
            if att == 'levelRequired':
                setattr(self, att,
                        SpellDict[spellName][att][charObj.getClassName()])
            elif att == 'formula':
                # for formulas, we execute them and store the result as
                # an attribute.  We get the attribute name from the
                # formulaResultAtt attribute.  Overly complicated?  Maybe,
                # but the object comes out looking clean.
                attName = SpellDict[spellName]['formulaResultAtt']
                if attName == '':
                    continue
                # execute formula and stick it in an attribute
                dLog('magic: formula = ' + att,
                     self._instanceDebug)
                dLog('magic: level=' + str(self.charObj.getLevel()) +
                     ' - Int=' + str(self.charObj.getIntelligence()),
                     self._instanceDebug)
                setattr(self, attName, eval(SpellDict[spellName][att]))
                dLog('magic: spell=' + self.spellName +
                     ' - damage=' + str(getattr(self, attName)),
                     self._instanceDebug)
            elif att == 'formulaResultAtt':
                # This is used for formula results, so don't set it as att
                continue
            else:
                setattr(self, att, SpellDict[spellName][att])

        self.succeeded = self._checkIfSucceeds()
        return(None)

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
            playerInput = self.charObj.client.promptForInput()
        else:
            playerInput = self.givenChant

        if playerInput.lower() == self.chant.lower():
            return(True)

        dLog("_promptForChant Failed: bad chant", self._instanceDebug)
        return(False)

    def _selfCriteriaAreMet(self):
        if not self.charObj.canAttack():
            dLog("_selfCriteriaAreMet Failed: Character cant attack",
                 self._instanceDebug)
            return(False)
        if self.levelRequired < 1:
            dLog("_selfCriteriaAreMet Failed: Character can't cast " +
                 self.spellName, self._instanceDebug)
            return(False)
        if self.charObj.getLevel() < self.levelRequired:
            dLog("lvlChk falied: a level " + str(self.charObj.getLevel()) +
                 ' ' + self.charObj.getClassName() + ' can not cast ' +
                 self.spellName + ' which requires level ' +
                 str(self.levelRequired), self._instanceDebug)
            return(False)
        return(True)

    def _targetCriteriaAreMet(self):
        if self.targetObj.isMagic():
            dLog("_targetCriteriaAreMet Failed: target is Magic",
                 self._instanceDebug)
            return(False)
        spellTargets = SpellDict[self.spellName]['spellTargets']
        if self.targetObj.getType() not in spellTargets:
            dLog("_targetCriteriaAreMet Failed: invalid target",
                 self._instanceDebug)
            return(False)
        return(True)
