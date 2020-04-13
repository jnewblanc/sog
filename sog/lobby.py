''' lobby class '''
# lobby class is set up to be a single instance

import logging


class _Lobby():
    ''' lobby class '''
    def __init__(self):
        self.instance = "Instance at %d" % self.__hash__()
        self.userList = []
        return(None)

    def processCommand(self, svrObj):    # noqa: C901
        ''' Process lobby commands '''

        cmdargs = svrObj.getInputStr().split(' ')
        cmd = cmdargs[0]

        if svrObj.acctObj not in self.userList:
            self.userList.append(svrObj.acctObj)

        logging.debug("LOBBY cmd = " + cmd)

        buf = ''

        if svrObj.acctObj.isAdmin():
            if self.processAdminCommand(svrObj, cmdargs):
                return(True)

        if cmd == '':
            pass
        elif cmd == 'brief':
            svrObj.acctObj.setPromptSize("brief")
        elif cmd == 'broadcast':
            prompt = "What is the message? "
            msgBuf = svrObj.promptForInput(prompt, '')
            if svrObj.broadcast(msgBuf):
                buf += 'Sent\n'
        elif cmd == 'exit' or cmd == "quit":
            self.userList.remove(svrObj.acctObj)
            buf += 'Leaving Lobby...\n'
            svrObj.spoolOut(buf)
            return(False)
        elif cmd == 'full':
            svrObj.acctObj.setPromptSize("full")
        elif cmd == 'help':
            buf += ('play  - play the SoG game\n'
                    'who   - show players logged in to the lobby\n' +
                    'info  - get account information\n' +
                    'brief - set lobby prompt to brief mode\n' +
                    'full  - set lobby promp to full mode\n' +
                    'msg - send a private message to one player\n' +
                    'broadcast - send a message to all players\n' +
                    'quit  - log out of lobby\n')
        elif cmd == 'info':
            buf += svrObj.acctObj.getInfo()
        elif cmd == 'msg':
            self.sendMsg(svrObj)
        elif cmd == 'play' or cmd == 'game' or cmd == 'g':
            svrObj.setArea('game')  # Set this to trigger logout
            buf += "Entering game\n"
        elif cmd == 'prompt':
            svrObj.acctObj.setPromptSize('')
        elif cmd == 'setdisplayname':
            svrObj.acctObj.setDisplayName(svrObj.acctObj.promptForDisplayName())  # noqa: E501
        elif cmd == 'who':
            buf += self.showLogins()
        else:
            buf += "Unknown Command: " + cmd + '\n'

        logging.debug("LOBBY buf = " + buf)
        svrObj.spoolOut(buf)
        svrObj.acctObj.save(logStr=__class__.__name__)
        return(True)

    def sendMsg(self, svrObj):
        prompt = "You may send a message to one the the folowing users."
        prompt += self.showLogins()
        prompt += "Who do you want to send a message to? "
        inNum = svrObj.promptForNumberInput(prompt, len(self.userList))
        userObj = self.userList[inNum]
        prompt = "What is the message? "
        msgBuf = svrObj.promptForInput(prompt, '')
        if userObj.svrObj.spoolOut(msgBuf):
            buf = 'Sent\n'
        return(buf)

    def processAdminCommand(self, svrObj, cmdargs):
        ''' Process lobby commands for Admins '''
        buf = ''
        cmd = cmdargs[0]

        if cmd == 'addcharacterondisk':
            charNamesFromDisk = svrObj.acctObj.getCharactersOnDisk()
            if len(charNamesFromDisk) > 0:
                prompt = "Characters on Disk:\n  "
                prompt += "\n  ".join(charNamesFromDisk)
                prompt += "\nEnter character name or press [enter] to exit: "
                inStr = svrObj.promptForInput(prompt)
                if inStr in charNamesFromDisk:
                    svrObj.acctObj.addCharacterToAccount(inStr)
                    buf += inStr + " added to characterList\n"
                else:
                    buf += "Could not add " + inStr + " to characterList"
            return(True)
        elif cmd == 'addcharactertoaccount':
            name = svrObj.promptForInput("Char Name: ")
            svrObj.acctObj.addCharacterToAccount(name)
            return(True)
        elif cmd == 'deletecharacterfromaccount':
            name = svrObj.promptForInput("Char Name: ")
            svrObj.acctObj.removeCharacterFromAccount(name)
            return(True)

        svrObj.spoolOut(buf)
        return(False)

    def showLogins(self):
        ''' show an enumerated list of players '''
        buf = "Players:\n"
        for num, player in enumerate(self.userList):
            buf += '  (' + str(num) + ") " + player.getName() + "\n"
        return(buf)


# instanciate the _Lobby class
_lobby = _Lobby()


def Lobby():
    ''' return a reference to the single, existing _lobby instance
        Thus, when we try to instanciate Lobby, we are just returning
        a ref to the existing Lobby '''

    return(_lobby)
