''' attack functions '''

import random

from character import Character
from common.general import dLog, getRandomItemFromList
from magic import SpellList, getSpellDamageType
# from common.general import logger


class Combat():

    # _instanceDebug = True

    attackDict = {
        'attack': {
            'desc': "a standard attack",
            'damagepctBonus': 0,
            'tohit': 0,
            'dodge': 0,
            'slashAdj': 0,
            'bludgeonAdj': 0,
            'pierceAdj': 0,
            'vulnerableAlways': False,
            'vulnerableOnMiss': False,
        },
        'backstab': {
            'desc': "a standard attack",
            'damagepctBonus': 50,
            'tohit': 0,
            'dodge': 0,
            'slashAdj': 0,
            'bludgeonAdj': 0,
            'pierceAdj': 10,
            'vulnerableAlways': False,
            'vulnerableOnMiss': True,
        },
        'block': {
            'desc': "a standard attack",
            'damagepctBonus': -30,
            'tohit': 0,
            'dodge': 20,
            'slashAdj': 0,
            'bludgeonAdj': 10,
            'pierceAdj': 0,
            'vulnerableAlways': False,
            'vulnerableOnMiss': False,
        },
        'circle': {
            'desc': "step around to slow an attack - no damage - delays atck",
            'damagepctBonus': -100,
            'tohit': 20,
            'dodge': 0,
            'slashAdj': 0,
            'bludgeonAdj': 0,
            'pierceAdj': 0,
            'vulnerableAlways': False,
            'vulnerableOnMiss': False,
        },
        'feint': {
            'desc': "a deceptive or pretended blow",
            'damagepctBonus': -30,
            'tohit': 0,
            'dodge': 30,
            'slashAdj': 0,
            'bludgeonAdj': 0,
            'pierceAdj': 0,
            'vulnerableAlways': False,
            'vulnerableOnMiss': False,
        },
        'hit': {
            'desc': "a precise strike which lands more often",
            'damagepctBonus': -10,
            'tohit': 20,
            'dodge': -10,
            'slashAdj': 0,
            'bludgeonAdj': 0,
            'pierceAdj': 0,
            'vulnerableAlways': False,
            'vulnerableOnMiss': False,
        },
        'kill': {
            'desc': "an agressive attack",
            'damagepctBonus': 10,
            'tohit': 10,
            'dodge': -20,
            'slashAdj': 0,
            'bludgeonAdj': 10,
            'pierceAdj': 0,
            'vulnerableAlways': False,
            'vulnerableOnMiss': False,
        },
        'lunge': {
            'desc': "a precise drive forward that leaves you vulnerable",
            'damagepctBonus': 20,
            'tohit': 40,
            'dodge': -70,
            'slashAdj': 0,
            'bludgeonAdj': 0,
            'pierceAdj': 10,
            'vulnerableAlways': False,
            'vulnerableOnMiss': True,
        },
        'parry': {
            'desc': "ward off attack with a counter move",
            'damagepctBonus': -40,
            'tohit': 20,
            'dodge': 20,
            'slashAdj': 0,
            'bludgeonAdj': 0,
            'pierceAdj': 0,
            'vulnerableAlways': False,
            'vulnerableOnMiss': False,
        },
        'slay': {
            'desc': "a mighty DM only attack",
            'damagepctBonus': 99999,
            'tohit': 99999,
            'dodge': 99999,
            'slashAdj': 0,
            'bludgeonAdj': 0,
            'pierceAdj': 0,
            'vulnerableAlways': False,
            'vulnerableOnMiss': False,
        },
        'strike': {
            'desc': "a slightly agressive attack",
            'damagepctBonus': 10,
            'tohit': -10,
            'dodge': 0,
            'slashAdj': 10,
            'bludgeonAdj': 0,
            'pierceAdj': 0,
            'vulnerableAlways': False,
            'vulnerableOnMiss': False,
        },
        'thrust': {
            'desc': "a fierce stab",
            'damagepctBonus': 20,
            'tohit': 100,
            'dodge': -10,
            'slashAdj': 10,
            'bludgeonAdj': 0,
            'pierceAdj': 20,
            'vulnerableAlways': False,
            'vulnerableOnMiss': False,
        },
        'spell': {
            'desc': "used to calc toHit and Dodge - damage is ignored here",
            'damagepctBonus': 0,
            'tohit': 25,
            'dodge': 0,
            'slashAdj': 0,
            'bludgeonAdj': 0,
            'pierceAdj': 0,
            'vulnerableAlways': False,
            'vulnerableOnMiss': False,
        }
    }

    CombatAttacks = attackDict.keys()

    _jailRoomNum = 280
    _kidnapRoomNum = 184

    _charSecsBetweenAttacks = 5    # time a player need to wait between attacks

    # Base numbers.  Creature attack rate scales up/down by percentage attr
    _creatureMinSecsBetweenAttacks = 10  # min time for creature atk cooldown
    _creatureMaxSecsBetweenAttacks = 25  # max time for creature atk cooldown

    def getAttackDict(self):
        return(self.attackDict)

    def getToHit(self, attackCmd):
        if attackCmd in self.CombatAttacks:
            return(self.attackDict[attackCmd]['tohit'])
        elif attackCmd in SpellList:
            return(self.attackDict['spell']['tohit'])
        else:
            return(self.attackDict['attack']['tohit'])

    def attackHit(self, attackerObj, defenderObj, attackCmd='attack'):
        ''' Determine if an attack hits '''
        logPrefix = "combat.attackHit: "

        dLog(logPrefix + "Calculating attackHit for " +
             attackerObj.describe() + " attacking " + defenderObj.describe() +
             " with cmd " + attackCmd + "...", self._instanceDebug)

        # right off the bat, with no calcs, there's a 25% chance of a hit,
        # which means that 25% is the lowest hit chance
        hitRoll = random.randint(1, 4)
        if random.randint(1, 4) == 1:
            dLog(logPrefix + "  25% hit chance triggered",
                 self._instanceDebug)
            return(True)

        hitPercentage = 50  # base percent

        # level bonus/penalty = %5 per level
        levelAdj = (attackerObj.getLevel() - defenderObj.getLevel()) * 5
        hitPercentage += levelAdj
        dLog(logPrefix + "  " + str(levelAdj) + "% level adj",
             self._instanceDebug)

        # dex bonus/penalty = +/- %3 per dex above/below 12
        if isinstance(attackerObj, Character):
            dexAdj = (attackerObj.getDexterity() - 12) * 3
            hitPercentage += dexAdj
            dLog(logPrefix + "  " + str(dexAdj) + "% dex adj",
                 self._instanceDebug)

        # hidden bonus
        if attackerObj.isHidden():
            hitPercentage += 10
            dLog(logPrefix + "  10% hidden adj", self._instanceDebug)

        # attack command bonus/penalty
        attackCmdAdj = self.getToHit(attackCmd)
        hitPercentage += attackCmdAdj
        dLog(logPrefix + "  " + str(attackCmdAdj) + "% cmd adj",
             self._instanceDebug)

        if attackCmd in SpellList:
            # magic skill
            offenseAdj = attackerObj.getSkillPercentage("magic")
            hitPercentage += offenseAdj
            dLog(logPrefix + "  " + str(attackCmdAdj) + "% magic skill adj",
                 self._instanceDebug)
        else:
            # weapon bonus/penalty + skill
            offenseAdj = attackerObj.getEquippedWeaponToHit()
            hitPercentage += offenseAdj
            dLog(logPrefix + "  " + str(attackCmdAdj) + "% weapon/skill adj",
                 self._instanceDebug)

        # armor bonus/penalty
        defenceAdj = defenderObj.getCumulativeDodge()
        hitPercentage -= defenceAdj
        dLog(logPrefix + "  " + str(defenceAdj) + "% defence adj",
             self._instanceDebug)

        hitRoll = random.randint(1, 100)

        dLog(logPrefix + "  " + str(hitPercentage) + "% total hit percent " +
             "needs to be less than random roll " + str(hitRoll),
             self._instanceDebug)

        if (hitRoll >= hitPercentage):
            dLog(logPrefix + "HIT", self._instanceDebug)
            return(True)
        dLog(logPrefix + "MISS", self._instanceDebug)
        return(False)

    def misses(self, attacker, target, attackCmd='attack'):
        ''' Determine if an attack misses '''
        return(not (self.attackHit(attacker, target, attackCmd)))

    def calcDmgPct(self, attackerObj, opponentObj, attackCmd='attack'):
        ''' Calculate damage percentage '''
        logPrefix = "combat.calcDmgPct: "
        damagePercent = 100

        dLog(logPrefix + "Calculating DmgPct for " +
             attackerObj.describe() + " attacking " + opponentObj.describe() +
             " with cmd " + attackCmd + "...", self._instanceDebug)

        dLog(logPrefix + "  " + str(damagePercent) + "% starting point",
             self._instanceDebug)

        if isinstance(attackerObj, Character):
            # if char is chaotic and monster is lawful, then bonus
            if ((attackerObj.getAlignment() == 'chaotic' and
                 opponentObj.getAlignment() == 'good')):
                damagePercent += 10
                dLog(logPrefix + "  10% alignment bonus", self._instanceDebug)
            elif ((attackerObj.getAlignment() == 'lawful' and
                   opponentObj.getAlignment() == 'evil')):
                damagePercent += 10
                dLog(logPrefix + "  10% alignment bonus", self._instanceDebug)

            # skill bonus
            skillPercent = attackerObj.getEquippedSkillPercentage()
            damagePercent += skillPercent
            dLog(logPrefix + "  " + str(skillPercent) + "% skill bonus",
                 self._instanceDebug)

            # strength bonus/penalty
            strengthPercent = int((attackerObj.getStrength() - 12) / 3) * 10
            damagePercent += strengthPercent
            dLog(logPrefix + "  " + str(strengthPercent) + "% strength adj",
                 self._instanceDebug)

        # significantly less damage dealt to unseen opponents
        if opponentObj.isHidden() or opponentObj.isInvisible():
            damagePercent -= 40
            dLog(logPrefix + "  " + "-40% hidden target penalty",
                 self._instanceDebug)

        # backstab bonus/penalty - risk = reward
        if attackCmd == 'backstab':
            if attackerObj.isHidden():
                cmdPercent = self.attackDict[attackCmd]['damagepctBonus']
            else:
                cmdPercent = -(self.attackDict[attackCmd]['damagepctBonus'])
        elif attackCmd in self.attackDict.keys():
            # specialized attacks
            cmdPercent = self.attackDict[attackCmd]['damagepctBonus']
        else:
            # standard attack
            cmdPercent = self.attackDict['attack']['damagepctBonus']

        damagePercent += cmdPercent
        dLog(logPrefix + "  " + str(cmdPercent) + "% attack cmd bonus",
             self._instanceDebug)

        dLog(logPrefix + str(damagePercent) + "% total damage percent",
             self._instanceDebug)
        return(damagePercent)

    def checkForCrit(self, cpercent=2):
        if random.randint(1, 100) <= cpercent:
            return(True)
        return(False)

    def checkForDD(self, target, ddpercent=6):
        if target.isVulnerable():
            target.setVulnerable(False)
            return(True)
        if random.randint(1, 100) <= ddpercent:
            return(True)
        return(False)

    def applyCritOrDD(self, damage, target, notify=[]):
        logPrefix = "applyCritOrDD: "
        buf = ''

        if self.checkForCrit():
            buf = "Critical Damage!\n"
            damage = max(1, damage) * 3   # critical hit
            dLog(logPrefix + "critical damage (*3)", self._instanceDebug)
        elif self.checkForDD(target):
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

        dLog(logPrefix + "Calculating attackDamage for " +
             attackerObj.describe() + " attacking " + opponentObj.describe() +
             " with cmd " + attackCmd + "...", self._instanceDebug)

        weaponDamage = attackerObj.getEquippedWeaponDamage()

        damagePercent = int(self.calcDmgPct(attackerObj, opponentObj,
                                            attackCmd=attackCmd) / 100)

        damage = weaponDamage * damagePercent

        dLog(logPrefix + "weapon damage(" + str(weaponDamage) +
             ") * damagePercent(" + str(damagePercent) + ") = preAcDamage(" +
             str(damage) + ')', self._instanceDebug)

        damage = opponentObj.acDamageReduction(damage)

        # check for crit or double damage
        damage = self.applyCritOrDD(damage, opponentObj,
                                    [attackerObj, opponentObj])

        damage = int(damage)
        dLog(logPrefix + "Total damage(" + str(damage) + ")",
             self._instanceDebug)
        return(damage)

    def stopPlayerAtk(self):
        return(True)

    def stopOtherAtk(self):
        return(True)

    def whiskAwayInsteadOfDeath(self, charObj, roomNum=184):
        ''' Instead of death:
        * Player is teleported to room
        * death and death inducing ailments are prevented
        * Future??? monster will placed in the room connected to
          the door (i.e. room 7).
        '''
        msg = ''

        if roomNum == self._kidnapRoomNum:
            msg = ("Everything goes black...  As you start to come around, " +
                   "you find yourself in\nan awkward, and dangerous " +
                   "predicament.  You opt to remain perfectly still\n" +
                   "until you can assess the situation")

        if roomNum == self._jailRoomNum:
            msg = ("You are hauled off to jail.\n")

        self.charMsg(self.charObj, msg)
        charObj.setNearDeathExperience()
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

    def attackCreature(self, charObj, target, attackCmd='attack',
                       spellObj=None):
        logPrefix = "Game attackCreature: "
        roomObj = charObj.getRoom()
        # self._instanceDebug = False

        isSpell = False
        if attackCmd in SpellList:
            isSpell = True
        elif attackCmd not in self.attackDict.keys():
            attackCmd = 'attack'

        if not target:
            dLog(logPrefix + "no target", self._instanceDebug)
            return(False)

        if roomObj.isSafe():
            self.charMsg(charObj, "A unknown force prevents combat here.\n")
            dLog(logPrefix + roomObj.getItemId() + " is safe",
                 self._instanceDebug)
            return(False)

        if target.isUnKillable():
            self.charMsg(charObj, "Aw.  Don't hurt the poor " +
                         target.describe(article='') + '\n')
            dLog(logPrefix + target.describe() + " is unkillable",
                 self._instanceDebug)
            return(False)

        if not charObj.canAttack():
            dLog(logPrefix + charObj.getItemId() + "cant attack",
                 self._instanceDebug)
            return(False)

        charObj.setHidden(False)
        charObj.setSecondsUntilNextAttack(self._charSecsBetweenAttacks)
        charObj.setLastAttack(attackCmd)

        if not isSpell:
            attackVuln = self.attackDict[attackCmd]['vulnerableAlways']
            charObj.setVulnerable(attackVuln)

        dLog(logPrefix + charObj.getName() + " attacks " + target.getName() +
             " with " + attackCmd, self._instanceDebug)

        # creature attacks player * player becomes locked on to creature
        self.engageTarget(charObj, target)

        if attackCmd != 'slay' and self.misses(charObj, target, attackCmd):
            self.charMsg(charObj, "You miss.\n")
            damage = 0
            if not isSpell:
                attackVuln = self.attackDict[attackCmd]['vulnerableOnMiss']
                charObj.setVulnerable(attackVuln)
        elif attackCmd != 'slay' and charObj.fumbles():
            self.charMsg(charObj, "Fumble!  You trip and need a moment to " +
                         " recover.\n")
            self.othersInRoomMsg(charObj, roomObj, charObj.getName() +
                                 " stumbles.\n")
            damage = 0
        else:
            if isSpell:
                damage = spellObj.getDamage()
            else:
                # reduce weapon charge counter
                charObj.decreaseChargeOfEquippedWeapon()
                # calculate attack damage
                damage = self.attackDamage(charObj, target, attackCmd)

            self.applyDamage(charObj, charObj, target, damage,
                             attackCmd=attackCmd)
        # end attackCreature

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
        # end creaturesAttack

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

        secs = random.randint(self._creatureMinSecsBetweenAttacks,
                              self._creatureMaxSecsBetweenAttacks)
        dLog(logPrefix + "setting creature secs to  " + str(secs),
             self._instanceDebug)

        creatureObj.setSecondsUntilNextAttack(secs)
        creatureObj.setLastAttack()

        if self.misses(creatureObj, charObj):  # if creature doesn't hit
            self.charMsg(charObj, creatureObj.describe() + " misses you!\n")
            # notify other players in the room
            damage = 0
            # see if we need to bump the dodge percentage
            if creatureObj.getLevel() >= charObj.getLevel():
                charObj.rollToBumpSkillForLevel('_dodge', percentChance=3)
        elif creatureObj.fumbles():
            self.charMsg(charObj, creatureObj.describe() + " fumbles!\n")
            damage = 0
        else:
            # calculate attack damage
            damage = self.attackDamage(creatureObj, charObj)

        # reduce charges of armor/shield protection
        charObj.decreaseChargeOfEquippedProtection()

        self.applyDamage(charObj, creatureObj, charObj, damage,
                         attackCmd='attack')
        return(None)
        # end creatureAttacksPlayer

    def applyDamage(self, charObj, attacker, target, damage, attackCmd):
        ''' apply damage to target or player '''
        logPrefix = "combat.applyDamage: "
        if damage:
            # Parse attackers/targets to get a set of attack/target words
            atkDict = self.getattackMsgDict(charObj, attacker, target,
                                            attackCmd)

            # Display the message about the hit
            self.charMsg(charObj, self.getHitMsg(atkDict, damage))

        if target.damageIsLethal(damage):
            debugMsg = (atkDict['attackerName'] +
                        ' does lethal damage to ' + atkDict['targetSubject'])
            dLog(logPrefix + debugMsg, self._instanceDebug)

        if isinstance(target, Character):
            self.applyPlayerDamage(charObj, attacker, damage)
        else:
            self.applyCreatureDamage(charObj, target, damage, attackCmd)

    def getattackMsgDict(self, charObj, attacker, target, attackCmd):
        ''' returns a dict of attacker and target strings '''
        msgDict = {}
        msgDict['msgPrefix'] = ''
        if attacker == charObj:   # You
            msgDict['attackerSubject'] = "You"
            msgDict['attackerName'] = attacker.describe()
            msgDict['attackerVerb'] = "hit"
            if attackCmd in SpellList:
                msgDict['msgPrefix'] = "Phouf! "
                msgDict['attackerVerb'] = "blast"
            elif charObj.getEquippedWeapon().getName() == 'fist':
                # It's important that we clearly identify weaponless attacks
                msgDict['msgPrefix'] = "Pow!  "
                msgDict['attackerVerb'] = "punch"
        else:  # Creature or another player
            msgDict['attackerSubject'] = attacker.describe()
            msgDict['attackerName'] = attacker.describe()
            msgDict['attackerVerb'] = "hits"

        if target == charObj:  # You
            msgDict['targetSubject'] = "you"
            msgDict['targetName'] = target.describe()
        else:  # Creature or another player
            msgDict['targetSubject'] = target.describe()
            msgDict['targetName'] = target.describe()
        return(msgDict)

    def getHitMsg(self, atkDict, damage):
        ''' return the hit message based on the attacker and target '''
        logPrefix = "combat.hitMsg: "

        msg = (atkDict['msgPrefix'] + atkDict['attackerSubject'] + ' ' +
               atkDict['attackerVerb'] + ' ' + atkDict['targetSubject'] +
               ' for ' + str(damage) + " damage.\n")

        # Construct separate message where all subjects are identified by name
        debugMsg = (atkDict['attackerName'] + ' hits ' +
                    atkDict['targetName'] + ' for ' +
                    str(damage) + ' damage')
        dLog(logPrefix + debugMsg, self._instanceDebug)

        return(msg)

    def applyCreatureDamage(self, charObj, target, damage, attackCmd='attack'):
        ''' applys damage/death to a creature when a player hits it '''
        roomObj = charObj.getRoom()

        if target.damageIsLethal(damage):
            self.charMsg(charObj, "You killed " +
                         target.describe(article='the') + "\n")
            self.othersInRoomMsg(charObj, roomObj, charObj.getName() +
                                 " kills " + target.describe() + "\n")
            target.transferInventoryToRoom(roomObj, self.roomMsg)

            # dole out experience
            self.allocateExp(charObj, roomObj, target)

            # determine if skill is increased
            if charObj.getLevel() >= target.getLevel():
                if attackCmd in SpellList:
                    damageType = getSpellDamageType()
                else:
                    damageType = charObj.getEquippedWeaponDamageType()
                charObj.rollToBumpSkillForLevel(damageType)

            # update player kill stats
            charObj.updateKillCount(target)

            # destroy creature
            roomObj.removeFromInventory(target)
        else:
            target.takeDamage(damage)
            if target.flees(target):
                self.roomMsg(roomObj, target.describe() + " flees.\n")
                # destroy creature
                roomObj.removeFromInventory(target)
        # end applyCreatureDamage

    def applyPlayerDamage(self, charObj, attacker, damage):
        ''' apply player damage from a creature or player '''

        if charObj.damageIsLethal(damage):
            if attacker.kidnaps():
                self.whiskAwayInsteadOfDeath()
            elif attacker.sendsToJail():
                self.whiskAwayInsteadOfDeath(charObj,
                                             roomNum=self._kidnapRoomNum)
            else:
                if not charObj.isDm():
                    charObj.transferInventoryToRoom(charObj.getRoom(),
                                                    self.roomMsg,
                                                    persist=True,
                                                    verbose=True)
            # death is handled in charObj.takeDamage

        charObj.takeDamage(damage)

        self.panicIfNeeded(charObj)

        # end applyPlayerDamage

    def unAttack(self, roomObj, charObj):
        ''' When a player leaves the room, creatures that are still in
            in the room need to unattack that player '''
        for creatureObj in roomObj.getCreatureList():
            if creatureObj.getCurrentlyAttacking() == charObj:
                creatureObj.setCurrentlyAttacking = None

    def engageTarget(self, charObj, target):
        ''' Character locks on to creature and creature begins to defend
            * If both are already fighting each other, do nothing.  '''
        logPrefix = "engageTarget: "

        if target.getCurrentlyAttacking() != charObj:
            if not isinstance(target, Character):
                # creature begins to attack player
                if target.attacksBack():
                    target.setLastAttack()
                    secs = int(random.randint(
                        self._creatureMinSecsBetweenAttacks,
                        self._creatureMaxSecsBetweenAttacks) / 2)
                    target.setSecondsUntilNextAttack(secs)
                    target.setCurrentlyAttacking(charObj)
                    dLog(logPrefix + target.describe() + " engages " +
                         charObj.describe(), self._instanceDebug)

        # attacker becomes locked on to target
        if charObj.getCurrentlyAttacking() != target:
            charObj.setCurrentlyAttacking(target)
            dLog(logPrefix + charObj.describe() + " engages " +
                 target.describe(), self._instanceDebug)
            self.othersInRoomMsg(charObj, charObj.getRoom(),
                                 charObj.getName() + " attacks " +
                                 target.describe() + "\n")

    def circle(self, charObj, target, attackCmd='attack'):
        ''' delays a defender's first strike and engages creature
            * chance of success based on attack toHit
            * In terms of timing, counts as an attack
            * engages creature regardless of success
            * player isn't informed if circle was successful or not
        '''
        if self.attackHit(charObj, target, attackCmd):
            target.setSecondsUntilNextAttack(charObj.getCircleSecs())
            charObj.setLastAttack()

        self.engageTarget(charObj, target)

        return(None)

    def panicIfNeeded(self, charObj):
        ''' If character has less than X percent health remaining, run away '''
        dLog('panicIfNeeded: ' + str(charObj.getHitPointPercent()) + " <? 10",
             True)
        if charObj.getHitPoints() < 30 and charObj.getHitPointPercent() <= 10:
            self.charMsg(charObj, "Panic!  ")
            self.run(charObj)
            return(True)
        return(False)

    def run(self, charObj):
        ''' Drop weapon and escape to an adjoining room '''
        roomNumList = []
        roomNumList += list(charObj.getRoom().getAllAdjacentRooms())

        if len(roomNumList) == 0:
            self.charMsg(charObj, "You try to run, but " +
                         "there are no escape routes.\n")
            return(False)

        escapeRoom = getRandomItemFromList(roomNumList)

        # drop weapon
        if not charObj.isAttackingWithFist():
            charObj.discardsEquippedWeapon()
            cMsg = 'You drop your weapon and run!'
            (article, possessive, predicate) = charObj.getArticle('self')
            oMsg = (charObj.getName() + ' drops ' + possessive +
                    ' weapon and runs away!')
        else:
            cMsg = 'You run away!'
            oMsg = (charObj.getName() + ' runs away!')

        self.charMsg(charObj, cMsg + '\n')
        self.othersInRoomMsg(charObj, charObj.getRoom(), oMsg + "\n")

        self.joinRoom(escapeRoom, charObj)
        self.charMsg(charObj, charObj.getRoom().display(charObj))
