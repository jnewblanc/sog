''' ipc '''

import re
from common.general import logger


class Ipc():
    ''' interplayer communication '''

    def gameMsg(self, msg):
        ''' shown to everyone in the game '''
        received = False
        for oneChar in self.getCharacterList():
            if self.directMsg(oneChar, msg):
                received = True
        return(received)

    def directMsg(self, character, msg):
        ''' show only to specified user '''
        received = False
        if not character:
            return(False)

        if isinstance(character, str):
            for oneChar in self.getCharacterList():         # get chars in game
                if re.match(character.lower(), oneChar.getName().lower()):
                    recipient = oneChar
                    break
        else:
            recipient = character

        if recipient.client:
            recipient.client.spoolOut(msg)            # notify
            received = True
        else:
            logger.warning(
                "ipc.directMsg: recipient.client doesn't exist for " +
                recipient.describe() + ".  Skipping directMsg: " + msg)
        return(received)

    def charMsg(self, charObj, msg, allowDupMsgs=True):
        ''' show only to yourself '''
        if not charObj:
            logger.warning(
                "ipc.charMsg: charObj doesn't exist for " +
                charObj.describe() + ".  Skipping charMsg: " + msg)
            return(False)

        if not charObj.client:
            logger.warning(
                "ipc.charMsg: charObj.client doesn't exist for " +
                charObj.describe() + ".  Skipping charMsg: " + msg)
            return(False)

        if not allowDupMsgs and charObj.client.outputSpoolContains(msg):
            # skip duplicate messages
            return(True)

        charObj.client.spoolOut(msg)
        return(True)

    def roomMsg(self, roomObj, msg, allowDupMsgs=True):
        ''' shown to everyone in the room '''
        received = False
        if not roomObj:
            return(False)

        for oneChar in roomObj.getCharacterList():
            status = self.charMsg(oneChar, msg, allowDupMsgs)
            if status:
                received = True    # sent to at least one recipient
        return(received)

    def othersInRoomMsg(self, charObj, roomObj, msg, ignore=False):
        ''' shown to others in room, but not you '''
        received = False
        if ignore:             # may get set to True if player is hidden
            return(False)

        if not roomObj:
            logger.error('ipc.othersInRoomMsg: roomObj not defined.  Skipping')

        for oneChar in roomObj.getCharacterList():
            if charObj:
                if oneChar == charObj:
                    continue              # skip yourself
            status = self.charMsg(oneChar, msg)
            if status:
                received = True    # sent to at least one recipient
        return(received)

    def yellMsg(self, roomObj, msg):
        ''' shown to your room and rooms in adjoining directions '''
        received = False
        if not roomObj:
            return(False)

        roomNumbList = [roomObj.getId()]
        # Get ajacent directional rooms
        roomNumbList += list(roomObj.getExits().values())

        # Get rooms connected by a portal or door
        for obj in roomObj.getInventory():
            type = obj.getType()
            if type == "Door" or type == "Portal":
                roomNum = obj.getToWhere()
                if roomNum:
                    roomNumbList.append(roomNum)

        # filter out any non-room room numbers (i.e. roomNum = 0)
        roomNumbList = list(filter(lambda x: x != 0, set(roomNumbList)))

        logger.debug('yellMsg: ajoining rooms' + str(roomNumbList))

        # If any of the rooms are active, display message there.
        for oneRoom in self.getActiveRoomList():    # foreach active room
            if oneRoom.getId() in roomNumbList:     # if room id is an exit
                if self.roomMsg(oneRoom, msg):
                    received = True        # sent to at least one recipient
        return(received)
