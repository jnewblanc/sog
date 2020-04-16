''' attack functions '''

import random

attackList = {
    'attack': {
        'desc': "a standard attack",
        'damage': 0,
        'tohit': 0,
        'exposure': 0,
        'dodge': 0,
        'slashAdj': 0,
        'bludgeonAdj': 0,
        'pierceAdj': 0
    },
    'backstab': {
        'desc': "a standard attack",
        'damage': 0,
        'tohit': 0,
        'exposure': 0,
        'dodge': 0,
        'slashAdj': 0,
        'bludgeonAdj': 0,
        'pierceAdj': 0
    },
    'block': {
        'desc': "a standard attack",
        'damage': 0,
        'tohit': 0,
        'exposure': 0,
        'dodge': 0,
        'slashAdj': 0,
        'bludgeonAdj': 0,
        'pierceAdj': 0
    },
    'feint': {
        'desc': "a standard attack",
        'damage': 0,
        'tohit': 0,
        'exposure': 0,
        'dodge': 0,
        'slashAdj': 0,
        'bludgeonAdj': 0,
        'pierceAdj': 0
    },
    'kill': {
        'desc': "a standard attack",
        'damage': 0,
        'tohit': 0,
        'exposure': 0,
        'dodge': 0,
        'slashAdj': 0,
        'bludgeonAdj': 0,
        'pierceAdj': 0
    },
    'parry': {
        'desc': "a standard attack",
        'damage': 0,
        'tohit': 0,
        'exposure': 0,
        'dodge': 0,
        'slashAdj': 0,
        'bludgeonAdj': 0,
        'pierceAdj': 0
    },
    'smash': {
        'desc': "a standard attack",
        'damage': 0,
        'tohit': 0,
        'exposure': 0,
        'dodge': 0,
        'slashAdj': 0,
        'bludgeonAdj': 0,
        'pierceAdj': 0
    },
    'strike': {
        'desc': "a standard attack",
        'damage': 0,
        'tohit': 0,
        'exposure': 0,
        'dodge': 0,
        'slashAdj': 0,
        'bludgeonAdj': 0,
        'pierceAdj': 0
    },
    'thrust': {
        'desc': "a standard attack",
        'damage': 0,
        'tohit': 0,
        'exposure': 0,
        'dodge': 0,
        'slashAdj': 0,
        'bludgeonAdj': 0,
        'pierceAdj': 0
    }
}


def attackHit(charObj, monstObj):
    ''' Determine if an attack hits '''
    hitRoll = random.randint(1, 20)
    baseToHit = charObj.level - monstObj.level + 10
    factor = 0
    if (hitRoll > baseToHit + factor):
        return(True)
    return(False)


def getEquippedWeaponDamage(charObj, attackCmd='attack'):
    ''' Given the equipped weapon and and attack type, return the damage '''
    damage = 0
    weapon = charObj.getEquippedWeapon()
    skillPercent = charObj.getSkill(weapon.getWeaponSkillType(weapon))
    # if weapon type matches weapon skill, apply a skill bonus
    # Skill percentile/10
    damage = skillPercent / 10
    return (damage)


def attackDamage(charObj, opponentObj, attackCmd='attack'):
    ''' determine the amount of damage dealt by an attack '''
    weaponDamage = getEquippedWeaponDamage(charObj, attackCmd)

    # if char is chaotic and monster is lawful, then bonus
    alignmentAdj = 0
    if ((charObj.getAlignment() == 'chaotic' and
         opponentObj.getAlignment() == 'lawful')):
        alignmentAdj = 1
    elif ((charObj.getAlignment() == 'lawful' and
           opponentObj.getAlignment() == 'chaotic')):
        alignmentAdj = 1

    # Certain classes get damage adjustments
    classAdj = charObj.classDict[charObj.getClassKey()]['damageAdjustment']

    levelAdj = 0
    if charObj.level == 1:
        levelAdj = 2

    hiddenAdj = 0
    if opponentObj.isHidden():
        hiddenAdj = -4

    # -level(player)/2 if player is parrying
    # +level(player) if thrusting (but subtract level(player) from fatigue)
    # 5 if backstabbing and hidden
    # -5 if backstabbing and not hidden,
    #    monster gets double damage on next attack

    attackTypeAdj = attackList[attackCmd]['damage']

    damage = (weaponDamage + attackTypeAdj + (charObj.strength/6) +
              alignmentAdj + classAdj + levelAdj + hiddenAdj)

    # 8% chance of double damage
    ddRoll = random.randint(1, 100)
    if ddRoll <= 8:
        damage = damage * 2


def attackFumbled():
    # 1% chance of fumble
    fumbleRoll = random.randint(1, 100)
    if fumbleRoll == 1:
        return(True)
    return(False)


def stopPlayerAtk():
    return(True)


def stopOtherAtk():
    return(True)
