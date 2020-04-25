''' attack functions '''

# import logging
import random

from character import Character
from common.general import dLog


class Combat():

    attackList = {
        'attack': {
            'desc': "a standard attack",
            'damagepctBonus': 0,
            'tohit': 0,
            'dodge': 0,
            'slashAdj': 0,
            'bludgeonAdj': 0,
            'pierceAdj': 0,
            'vulnerable': False
        },
        'backstab': {
            'desc': "a standard attack",
            'damagepctBonus': 50,
            'tohit': 0,
            'dodge': 0,
            'slashAdj': 0,
            'bludgeonAdj': 0,
            'pierceAdj': 0,
            'vulnerable': True
        },
        'block': {
            'desc': "a standard attack",
            'damagepctBonus': -30,
            'tohit': 0,
            'dodge': 30,
            'slashAdj': 0,
            'bludgeonAdj': 0,
            'pierceAdj': 0,
            'vulnerable': False
        },
        'feint': {
            'desc': "a standard attack",
            'damagepctBonus': -50,
            'tohit': 0,
            'dodge': 50,
            'slashAdj': 0,
            'bludgeonAdj': 0,
            'pierceAdj': 0,
            'vulnerable': False
        },
        'kill': {
            'desc': "a standard attack",
            'damagepctBonus': 10,
            'tohit': 0,
            'dodge': -10,
            'slashAdj': 0,
            'bludgeonAdj': 0,
            'pierceAdj': 0,
            'vulnerable': False
        },
        'parry': {
            'desc': "a standard attack",
            'damagepctBonus': -50,
            'tohit': 0,
            'dodge': 0,
            'slashAdj': 0,
            'bludgeonAdj': 0,
            'pierceAdj': 0,
            'vulnerable': False
        },
        'slay': {
            'desc': "a mighty DM only attack",
            'damagepctBonus': 99999,
            'tohit': 99999,
            'dodge': 99999,
            'slashAdj': 0,
            'bludgeonAdj': 0,
            'pierceAdj': 0,
            'vulnerable': False
        },
        'strike': {
            'desc': "a standard attack",
            'damagepctBonus': 0,
            'tohit': 0,
            'dodge': 0,
            'slashAdj': 0,
            'bludgeonAdj': 0,
            'pierceAdj': 0,
            'vulnerable': False
        },
        'thrust': {
            'desc': "a standard attack",
            'damagepctBonus': 20,
            'tohit': 0,
            'dodge': -20,
            'slashAdj': 0,
            'bludgeonAdj': 0,
            'pierceAdj': 0,
            'vulnerable': True
        }
    }

    _secsBetweenAttacks = 3

    def attackHit(self, attackerObj, defenderObj):
        ''' Determine if an attack hits '''
        hitRoll = random.randint(1, 20)
        baseToHit = attackerObj.getLevel() - defenderObj.getLevel() + 10
        factor = 0
        if (hitRoll > baseToHit + factor):
            return(True)
        return(False)

    def calcDmgPct(self, attackerObj, opponentObj, attackCmd='attack'):
        ''' Calculate damage percentage '''
        logPrefix = "combat.calcDmgPct: "
        damagePercent = 100

        if isinstance(attackerObj, Character):
            # if char is chaotic and monster is lawful, then bonus
            if ((attackerObj.getAlignment() == 'chaotic' and
                 opponentObj.getAlignment() == 'good')):
                damagePercent += 10
                dLog(logPrefix + "10% alignment bonus", self._instanceDebug)
            elif ((attackerObj.getAlignment() == 'lawful' and
                   opponentObj.getAlignment() == 'evil')):
                damagePercent += 10
                dLog(logPrefix + "10% alignment bonus", self._instanceDebug)

            # skill bonus
            skillPercent = attackerObj.getEquippedSkillPercentage()
            damagePercent += skillPercent
            dLog(logPrefix + str(skillPercent) + "% skill bonus",
                 self._instanceDebug)

            # strength bonus/penalty
            strengthPercent = int((attackerObj.getStrength() - 12) / 3) * 10
            damagePercent += strengthPercent
            dLog(logPrefix + str(strengthPercent) + "% strength adj",
                 self._instanceDebug)

        # significantly less damage dealt to unseen opponents
        if opponentObj.isHidden() or opponentObj.isInvisible():
            damagePercent -= 40
            dLog(logPrefix + "-40% hidden target penalty", self._instanceDebug)

        # backstab bonus/penalty - risk = reward
        if attackCmd == 'backstab':
            if attackerObj.isHidden():
                cmdPercent = self.attackList[attackCmd]['damagepctBonus']
            else:
                cmdPercent = -(self.attackList[attackCmd]['damagepctBonus'])
        elif attackCmd in self.attackList.keys():
            # specialized attacks
            cmdPercent = self.attackList[attackCmd]['damagepctBonus']
        else:
            # standard attack
            cmdPercent = self.attackList['attack']['damagepctBonus']

        damagePercent += cmdPercent
        dLog(logPrefix + str(cmdPercent) + "% attack cmd bonus",
             self._instanceDebug)

        dLog(logPrefix + str(damagePercent) + "% total damage percent",
             self._instanceDebug)
        return(damagePercent)

    def checkForCrit(self, cpercent=2):
        if random.randint(1, 100) <= cpercent:
            return(True)
        return(False)

    def checkForDD(self, ddpercent=6):
        if random.randint(1, 100) <= ddpercent:
            return(True)
        return(False)

    def applyCritOrDD(self, damage, notify=[]):
        logPrefix = "applyCritOrDD: "
        buf = ''

        if self.checkForCrit():
            buf = "Critical Damage!\n"
            damage = max(1, damage) * 3   # critical hit
            dLog(logPrefix + "critical damage (*3)", self._instanceDebug)
        elif self.checkForDD():
            buf = "Double Damage!\n"
            damage = max(1, damage) * 2   # double damage
            dLog(logPrefix + "double damage (*2)", self._instanceDebug)

        if buf != '':
            for recipient in notify:
                if recipient.getType() == 'Character':
                    self.charMsg(recipient, buf)
        return(damage)

    def attackDamage(self, attackerObj, opponentObj, attackCmd='attack'):
        ''' determine the amount of damage dealt by a creature or characters
            attack '''
        logPrefix = "combat.AttackDamage: "

        weaponDamage = attackerObj.getEquippedWeaponDamage()

        damagePercent = int(self.calcDmgPct(attackerObj, opponentObj,
                                            attackCmd=attackCmd) / 100)

        damage = weaponDamage * damagePercent

        dLog(logPrefix + "weapon damage(" + str(weaponDamage) +
             ") * damagePercent(" + str(damagePercent) + ") = preAcDamage(" +
             str(damage) + ')', self._instanceDebug)

        damage = opponentObj.acDamageReduction(damage)

        # check for crit or double damage
        damage = self.applyCritOrDD(damage, [attackerObj, opponentObj])

        dLog(logPrefix + "total damage(" + str(damage) + ")",
             self._instanceDebug)
        return(damage)

    def stopPlayerAtk(self):
        return(True)

    def stopOtherAtk(self):
        return(True)

    def kidnap(self, charObj, roomNum=184):
        ''' Instead of death:
        * Player is teleported to room
        * ??? monster will placed in the room connected to the door in room 7.
        '''
        self.charMsg(self.charObj, "Everything goes black...  As you start " +
                                   "to come around, you find yourself in\n" +
                                   "an awkward, and dangerous predicament.  " +
                                   "You opt to remain perfectly still\n" +
                                   "until you can assess the situation")
        self.gameObj.joinRoom(roomNum, charObj)
        return(True)

    def allocateExp(self, killerObj, roomObj, target):
        ''' Assign exp to the attackers.
            * Killer gets 50% right off the bat
            * remaining exp is divided amoungst all attackers (killer included)
            * remaining exp is scaled according to the players level in
              relationship to the average level of attackers
        '''
        # build attacking players list so we can dole out the experience
        attackingPlayers = []
        attckPlayerLevelSum = 0
        for player in roomObj.getCharacterList():
            if player.getCurrentlyAttacking() == target:
                attackingPlayers.append(player)
                attckPlayerLevelSum += player.getLevel()

        # dole out experience - non killers get some % exp
        creatureExp = target.getExp()
        if len(attackingPlayers) == 1:
            killerObj.addExp(creatureExp)
        else:
            # Killer gets 50%, right off the bat
            killerObj.addExp(int(creatureExp * .50))
            # remaining 50% gets split amoungst attackers (killer included)
            # should be scaled according to level
            remainingExp = (creatureExp * .50)
            baseExpPerPlayer = remainingExp / len(attackingPlayers)
            averageLevel = attckPlayerLevelSum / len(attackingPlayers)
            for player in attackingPlayers:
                exp = baseExpPerPlayer * (player.getLevel() / averageLevel)
                player.addExp(int(exp))
                remainingExp -= exp
        return(True)

    def attackCreature(self, charObj, target, attackCmd='attack'):  # noqa: C901, E501
        logPrefix = "Game attackCreature: "
        roomObj = charObj.getRoom()

        self._instanceDebug = True

        if not target:
            return(False)

        if not charObj.canAttack():
            return(False)

        charObj.setHidden(False)
        charObj.setSecondsUntilNextAttack(self._secsBetweenAttacks)
        charObj.setLastAttack()

        dLog(logPrefix + charObj.getName() + " attacks " + target.getName() +
             " with " + attackCmd, self._instanceDebug)

        # creature begins to attack player
        if target.attacksBack():
            target.setCurrentlyAttacking(charObj)

        # player is becomes locked on to creature
        if charObj.getCurrentlyAttacking() != target:
            charObj.setCurrentlyAttacking(target)
            self.othersInRoomMsg(charObj, roomObj, charObj.getName() +
                                 " attacks " + target.describe() + "\n")

        if charObj.fumbles():
            self.charMsg(charObj, "Fumble!  You trip and drop your gear" +
                         " to catch yourself.\n")
            self.othersInRoomMsg(charObj, roomObj, charObj.getName() +
                                 " stumbles.\n")

        # calculate attack damage
        damage = self.attackDamage(charObj, target, attackCmd)

        dLog(logPrefix + "target takes damage", self._instanceDebug)
        if charObj.getEquippedWeapon().getName() == 'fist':
            # It's important that we clearly identify weaponless attacks
            self.charMsg(charObj, "Pow!  You punch " + target.describe() +
                         " for " + str(damage) + " damage.\n")
        else:
            self.charMsg(charObj, "You hit " + target.describe() +
                         " for " + str(damage) + " damage.\n")

        if target.damageIsLethal(damage):
            dLog(logPrefix + "target dies", self._instanceDebug)

            self.charMsg(charObj, "You killed " + target.describe() + "\n")
            self.othersInRoomMsg(charObj, roomObj, charObj.getName() +
                                 " kills " + target.describe() + "\n")
            truncsize = roomObj.getInventoryTruncSize()
            for item in target.getInventory():
                if roomObj.addToInventory(item, maxSize=truncsize):
                    self.roomMsg(roomObj, item.describe() +
                                 " falls to the floor\n")
                else:
                    self.roomMsg(roomObj, item.describe() +
                                 "falls to the floor and rolls away")

            # dole out experience
            self.allocateExp(charObj, roomObj, target)

            # determine if skill is increased
            if charObj.getLevel() >= target.getLevel():
                damageType = charObj.getEquippedWeaponDamageType()
                charObj.rollToBumpSkillForLevel(damageType)

            # destroy creature
            roomObj.removeFromInventory(target)
        else:
            target.takeDamage(damage)

    def creaturesAttack(self, roomObj):
        ''' Creatures turn to engage and attack players '''
        for creatureObj in roomObj.getCreatureList():
            if creatureObj.isAttacking():
                self.creatureAttacksPlayer(creatureObj)
            else:
                if not creatureObj.isHostile():
                    continue
                # creature initates attack
                characterList = roomObj.getCharacterList()
                random.shuffle(characterList)  # shuffles in place, return None
                for charObj in characterList:
                    if creatureObj.initiateAttack(charObj):
                        self.charMsg(charObj, creatureObj.describe() +
                                     " attacks you!\n")
                        self.othersInRoomMsg(charObj, roomObj,
                                             creatureObj.describe() +
                                             " attacks " + charObj.getName() +
                                             "\n")
                        self.creatureAttacksPlayer(creatureObj, charObj)
                        break
        return(None)

    def creatureAttacksPlayer(self, creatureObj, charObj=None):
        ''' single creature attacks a player '''
        logPrefix = "combat.creatureAttacksPlayer: "
        if not charObj:
            charObj = creatureObj.getCurrentlyAttacking()

        dLog(logPrefix + creatureObj.describe() + " is attacking " +
             charObj.getName(), self._instanceDebug)

        if not charObj:
            return(False)

        # toDa: right now, creatures are sticky, but they should adhere to
        # attackLast
        if charObj != creatureObj.getCurrentlyAttacking():
            creatureObj.setCurrentlyAttacking(charObj)       # initiate attack

        if not creatureObj.canAttack():
            dLog(logPrefix + creatureObj.getName() + " can't attack " +
                 charObj.getName(), self._instanceDebug)
            return(False)

        secs = random.randint(self._secsBetweenAttacks,
                              self._secsBetweenAttacks + 1)
        creatureObj.setSecondsUntilNextAttack(secs)
        creatureObj.setLastAttack()

        if not creatureObj.hitsCharacter(charObj):  # if creature doesn't hit
            self.charMsg(charObj, creatureObj.describe() + " misses you!")
            # notify other players in the room

        # calculate attack damage
        damage = self.attackDamage(creatureObj, charObj)

        dLog(logPrefix + creatureObj.getName() + " hits " + charObj.getName() +
             " for " + str(damage) + " damage", self._instanceDebug)

        if damage:
            if charObj.damageIsLethal(damage):
                dLog(logPrefix + "player takes lethal damage",
                     self._instanceDebug)
                if creatureObj.kidnaps():
                    self.kidnap()
                else:
                    if not charObj.isDm():
                        # Transfer players inventory to room
                        for item in charObj.getInventory():
                            if charObj.getRoom().addToInventory(item):
                                charObj.removeFromInventory(item)

            # notify
            self.charMsg(charObj, creatureObj.describe() + " hits you for " +
                         str(damage) + " damage.\n")
            charObj.takeDamage(damage)
        return(None)

    def unAttack(self, roomObj, charObj):
        ''' When a player leaves the room, creatures that are still in
            in the room need to unattack that player '''
        for creatureObj in roomObj.getCreatureList():
            if creatureObj.getCurrentlyAttacking() == charObj:
                creatureObj.setCurrentlyAttacking = None
