''' ipc '''

import re


class Ipc():
    ''' interplayer communication '''

    def gameMsg(self, msg):
        ''' shown to everyone in the game '''
        for oneChar in self.getCharacterList():
            oneChar.client.spoolOut(msg)

    def directMsg(self, charName, msg):
        ''' show only to specified user '''
        recieved = False
        if not charName:
            return(False)

        for oneChar in self.getCharacterList():         # get chars in game
            if re.match(charName, oneChar.getName()):   # if name matches
                oneChar.client.spoolOut(msg)            # notify
                recieved = True
        return(recieved)

    def charMsg(self, charObj, msg):
        ''' show only to yourself '''
        recieved = False
        if charObj:
            charObj.client.spoolOut(msg)
            recieved = True
        return(recieved)

    def roomMsg(self, roomObj, msg):
        ''' shown to everyone in the room '''
        recieved = False
        if not roomObj:
            return(False)

        for oneChar in roomObj.getCharacterList():
            status = self.charMsg(oneChar, msg)
            if status:
                recieved = True    # sent to at least one recipient
        return(recieved)

    def othersInRoomMsg(self, charObj, roomObj, msg, ignore=False):
        ''' shown to others in room, but not you '''
        recieved = False
        if ignore:             # may get set to True if player is hidden
            return(False)

        for oneChar in roomObj.getCharacterList():
            if charObj:
                if oneChar == charObj:
                    continue              # skip yourself
            status = self.charMsg(oneChar, msg)
            if status:
                recieved = True    # sent to at least one recipient
        return(recieved)

    def yellMsg(self, roomObj, msg):
        ''' shown to your room and rooms in adjoining directions '''
        recieved = False
        if not roomObj:
            return(False)

        exitDict = roomObj.getExits()
        for oneRoom in self.getActiveRoomList():    # foreach active room
            if oneRoom.getId() in exitDict.keys():  # if room id is an exit
                for oneChar in oneRoom.getCharacterList():  # get chars in room
                    status = self.charMsg(oneChar, msg)
                    if status:
                        recieved = True    # sent to at least one recipient
        return(recieved)
