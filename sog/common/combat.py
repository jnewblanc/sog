''' attack functions '''

# import logging
import random

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

    def attackHit(self, charObj, monstObj):
        ''' Determine if an attack hits '''
        hitRoll = random.randint(1, 20)
        baseToHit = charObj.level - monstObj.level + 10
        factor = 0
        if (hitRoll > baseToHit + factor):
            return(True)
        return(False)

    def calcDmgPct(self, charObj, opponentObj, attackCmd='attack'):
        logPrefix = "calcDmgPct: "
        damagePercent = 100

        # if char is chaotic and monster is lawful, then bonus
        if ((charObj.getAlignment() == 'chaotic' and
             opponentObj.getAlignment() == 'good')):
            damagePercent += 10
            dLog(logPrefix + "10% alignment bonus", self._instanceDebug)
        elif ((charObj.getAlignment() == 'lawful' and
               opponentObj.getAlignment() == 'evil')):
            damagePercent += 10
            dLog(logPrefix + "10% alignment bonus", self._instanceDebug)

        # significantly less damage dealt to unseen creatures
        if opponentObj.isHidden() or opponentObj.isInvisible():
            damagePercent -= 40
            dLog(logPrefix + "-40% hidden target penalty", self._instanceDebug)

        # backstab bonus/penalty - risk = reward
        if attackCmd == 'backstab':
            if charObj.isHidden():
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

        # skill bonus
        skillPercent = charObj.getEquippedSkillPercentage()
        damagePercent += skillPercent
        dLog(logPrefix + str(skillPercent) + "% skill bonus",
             self._instanceDebug)

        # strength bonus/penalty
        strengthPercent = int((charObj.getStrength() - 12) / 3) * 10
        damagePercent += strengthPercent
        dLog(logPrefix + str(strengthPercent) + "% strength adj",
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

    def attackDamage(self, charObj, opponentObj, attackCmd='attack'):
        ''' determine the amount of damage dealt by an attack '''
        logPrefix = "attackDamage: "

        weaponDamage = charObj.getEquippedWeaponDamage()

        damagePercent = int(self.calcDmgPct(charObj, opponentObj,
                                            attackCmd=attackCmd) / 100)
        damage = weaponDamage * damagePercent
        dLog(logPrefix + "weapon damage(" + str(weaponDamage) +
             ") * damagePercent(" + str(damagePercent) + ") = " + str(damage),
             self._instanceDebug)

        # First level characters get a bonus to make getting started a little
        # less painful
        if charObj.getLevel() == 1:
            damage += 1
            dLog(logPrefix + "+1 damage, 1st level bonus", self._instanceDebug)

        # check for crit or double damage
        if self.checkForCrit():
            charObj.svrObj.spoolOut("Double Damage\n")
            damage = max(1, damage) * 3   # critical hit
            dLog(logPrefix + "critical damage (*3)", self._instanceDebug)
        elif self.checkForDD():
            charObj.svrObj.spoolOut("Citical Hit\n")
            damage = max(1, damage) * 2   # double damage
            dLog(logPrefix + "double damage (*2)", self._instanceDebug)

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

    def creatureAttack(self, roomObj):
        ''' Creature attack on a player '''
        for creatureObj in roomObj.getCreatureList():
            if creatureObj.isAttacking():
                creatureObj.attack(creatureObj.getCurrentlyAttacking())
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
                        # notify other players in the room
                        creatureObj.attack(charObj)
                        break
        return(None)

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

    def attackCreature(self, charObj, target, attackCmd='attack'):
        logPrefix = "Game attackCreature: "
        roomObj = charObj.getRoom()

        if not target:
            return(False)

        if not charObj.canAttack():
            return(False)

        charObj.setHidden(False)
        charObj.setSecondsUntilNextAttack(3)
        charObj.setLastAttack()

        dLog(logPrefix + charObj.getName() + " attacks " + target.getName() +
             " with " + attackCmd, self._instanceDebug)

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

        if target.diesFromDamage(damage):
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
