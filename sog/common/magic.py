''' magic info '''    # noqa

# A player must learn a spell before casting it, either by being taught the
# spell or by examining a scroll. Once learned a spell is not forgotten.
# The player must also type in the chant for a spell to cast it, which means
# the player must also find out what the chant is.

SpellList = ['null',
             'vigor', 'heal', 'fireball', 'lightning', 'hurt',
             'curepoison', 'disintegrate', 'befuddle', 'teleport', 'wish',
             'passdoor', 'enchant', 'bless', 'protect', 'curse',
             'poison', 'intoxicate', 'turn', 'identify', 'appeal',
             'removecurse']
# ['psiblast', 'polymorph', 'summon', 'animate', 'charm', 'illuminate']

SpellDict = {
    '0': {
        'name': 'null',
        'desc': '',
        'chant': '',
        'limitedNumberPerDay': False,
        'magicPoints': 1,
        'intRequired': 10,
        'levelRequired': {
            'mage': 1,
            'fighter': 1,
            'rogue': 1,
            'cleric': 1,
            'ranger': 1,
            'paladin': 1,
        },
    },
    '1': {
        'name': 'vigor',
        'desc': 'Restores 5 * caster_level fatigue points',
        'chant': 'I return vigor',
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
    },
    '2': {
        'name': 'heal',
        'desc': 'Restores 12 * caster_level fatigue points',
        'chant': 'Thy wounds are mended!',
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
    },
    '3': {
        'name': 'fireball',
        'desc': 'Attack spell, min(3 * (lvl+1), int * 2) hp',
        'chant': 'Ball of fire fly to thee!',
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
    },
    '4': {
        'name': 'lightning',
        'desc': 'Attack spell, min(20 + 2 * (lvl+1)) hp.',
        'chant': 'I command you to glow with energy!',
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
    },
    '5': {
        'name': 'hurt',
        'desc': 'Attack spell, 1-3 hp',
        'chant': 'Ouch! That hurt!',
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
    },
    '6': {
        'name': 'curepoison',
        'desc': 'Cures player of poison.',
        'chant': 'Let thy fluids run pure!',
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
    },
    '7': {
        'name': 'disintegrate',
        'desc': 'Most powerful attack spell, lvl * 2 + ran(5 * int)',
        'chant': 'I disrupt they molecular structure!',
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
    },
    '8': {
        'name': 'befuddle',
        'desc': 'player= paused 30 secs; monster = paused 3 * MONSPEED secs',
        'chant': 'Be thou confused utterly!',
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
    },
    '9': {
        'name': 'teleport',
        'desc': 'Randomly transported to a room# 30-300',
        'chant': 'Let me go to someplace new!',
        'magicPoints': 30,
        'limitedNumberPerDay': False,
        'intRequired': 14,
        'levelRequired': {
            'mage': 5,
            'fighter': 9,
            'rogue': 8,
            'cleric': 6,
            'ranger': 7,
            'paladin': 7,
        },
    },
    '10': {
        'name': 'wish',
        'desc': 'Sent to DM; DM then decides',
        'chant': 'This is the last time I want to change this chant!',
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
    },
    '11': {
        'name': 'passdoor',
        'desc': 'Passes through any door where MAGIC=false',
        'chant': 'I refuse to be stopped!',
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
    },
    '12': {
        'name': 'enchant',
        'desc': 'Makes object magical; it must be carryable. doesnt change hp',
        'chant': 'I infuse you with magical dweomer!',
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
    },
    '13': {
        'name': 'bless',
        'desc': '+1 to piety of someone else. Must be equal or lower level.',
        'chant': 'Your soul is now pure again!',
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
    },
    '14': {
        'name': 'protect',
        'desc': 'Temporarily improve armor class by 1',
        'chant': 'You are being watched!',
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
    },
    '15': {
        'name': 'curse',
        'desc': '-1 to piety of someone else.  Must be <= caster level.',
        'chant': 'I denigrate thee for all to see!',
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
    },
    '16': {
        'name': 'poison',
        'desc': 'Poison Someone',
        'chant': 'May thy blood fester in thy veins!',
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
    },
    '17': {
        'name': 'intoxicate',
        'desc': 'Recipient is drunk for 60 seconds',
        'chant': 'More than one hundred proof!',
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
    },
    '18': {
        'name': 'turn',
        'desc': 'Exorcise or dispell undead - target must be =< level',
        'chant': '',
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
    },
    '19': {
        'name': 'identify',
        'desc': 'Show all the stats of an object or player',
        'chant': 'Show thee thou true nature!',
        'limitedNumberPerDay': True,
        'magicPoints': 20,
        'intRequired': 18,
        'levelRequired': {
            'mage': 10,
            'fighter': 12,
            'rogue': 12,
            'cleric': 10,
            'ranger': 11,
            'paladin': 11,
        },
    },
    '20': {
        'name': 'appeal',
        'desc': 'Appeal to gods (DMs) - costs one piety point',
        'chant': 'Let thee rewrite history.',
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
    },
    '21': {
        'name': 'removecurse',
        'desc': 'Removes a curse from an item',
        'chant': 'Release thou unholiness.',
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
        }
    }
}


class Spell():
    ''' Spell Class '''
    def __init__(self, charClass, spellId=0):
        if spellId:
            for att in SpellList[spellId].keys():
                if att == 'levelRequired':
                    setattr(self, att, SpellList[att][charClass])
                else:
                    setattr(self, att, SpellList[att])
        return(None)

    def promptForChant(self):
        return(True)

    def cast(self, target):
        return(True)
