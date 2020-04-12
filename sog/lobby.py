''' lobby class '''
# lobby class is set up to be a single instance

import logging


class _Lobby():
    ''' lobby class '''
    def __init__(self):
        self.instance = "Instance at %d" % self.__hash__()
        self.playerList = []
        return(None)

    def processCommand(self, svrObj):
        ''' Process lobby commands '''

        cmdargs = svrObj.getInputStr().split(' ')
        cmd = cmdargs[0]

        if svrObj.acctObj not in self.playerList:
            self.playerList.append(svrObj.acctObj)

        logging.debug("LOBBY cmd = " + cmd)

        buf = ''
        if cmd == '':
            pass
        elif cmd == 'addcharacterondisk' and svrObj.acctObj.isAdmin():
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
        elif cmd == 'addcharactertoaccount' and svrObj.acctObj.isAdmin():
            name = svrObj.promptForInput("Char Name: ")
            svrObj.acctObj.addCharacterToAccount(name)
        elif cmd == 'brief':
            svrObj.acctObj.setPromptSize("brief")
        elif cmd == 'broadcast':
            prompt = "What is the message? "
            msgBuf = svrObj.promptForInput(prompt, '')
            if svrObj.broadcast(msgBuf):
                buf = 'Sent\n'
        elif cmd == 'deletecharacterfromaccount' and svrObj.acctObj.isAdmin():
            name = svrObj.promptForInput("Char Name: ")
            svrObj.acctObj.removeCharacterFromAccount(name)
        elif cmd == 'exit' or cmd == "quit":
            svrObj.broadcast(svrObj.acctObj.getName() + ' has left the lobby')
            svrObj.acctObj.setLogoutDate()
            svrObj.acctObj.save()
            self.playerList.remove(svrObj.acctObj)
            svrObj.setArea('exit')  # Set this to trigger logout
            buf = 'Leaving Lobby...\n'
        elif cmd == 'full':
            svrObj.acctObj.setPromptSize("full")
        elif cmd == 'help':
            buf = ('play  - play the SoG game\n'
                   'who   - show players logged in to the lobby\n' +
                   'info  - get account information\n' +
                   'brief - set lobby prompt to brief mode\n' +
                   'full  - set lobby promp to full mode\n' +
                   'msg - send a private message to one player\n' +
                   'broadcast - send a message to all players\n' +
                   'quit  - log out of lobby\n')
        elif cmd == 'info':
            buf = svrObj.acctObj.getInfo()
        elif cmd == 'msg':
            prompt = "You may send a message to one the the folowing users."
            prompt += self.showLogins()
            prompt += "Who do you want to send a message to? "
            inNum = svrObj.promptForNumberInput(prompt, len(self.playerList))
            prompt = "What is the message? "
            msgBuf = svrObj.promptForInput(prompt, '')
            if svrObj.broadcast(msgBuf, inNum):
                buf = 'Sent\n'
        elif cmd == 'play' or cmd == 'game' or cmd == 'g':
            svrObj.setArea('game')  # Set this to trigger logout
            buf = "Entering game\n"
        elif cmd == 'prompt':
            svrObj.acctObj.setPromptSize('')
        elif cmd == 'setdisplayname':
            svrObj.acctObj.setDisplayName(svrObj.acctObj.promptForDisplayName())  # noqa: E501
        elif cmd == 'who':
            buf = self.showLogins()
        else:
            buf = "Unknown Command: " + cmd + '\n'

        logging.debug("LOBBY buf = " + buf)
        svrObj.spoolOut(buf)
        svrObj.acctObj.save(logStr=__class__.__name__)
        return(True)

    def showLogins(self):
        ''' show an enumerated list of players '''
        buf = "Players:\n"
        for num, player in enumerate(self.playerList):
            buf += '  (' + str(num) + ") " + player.getName() + "\n"
        return(buf)


# instanciate the _Lobby class
_lobby = _Lobby()


def Lobby():
    ''' return a reference to the single, existing _lobby instance
        Thus, when we try to instanciate Lobby, we are just returning
        a ref to the existing Lobby '''

    return(_lobby)
