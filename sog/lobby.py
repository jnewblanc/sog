''' lobby class '''
# lobby class is set up to be a single instance

import cmd
import logging
from character import Character

from common.general import dLog


class _Lobby():
    ''' Single instance of the lobby class, shared by all users
        (see instanciation magic at the bottom of the file)'''

    debugLobby = False

    def __init__(self):
        self.instance = "Instance at %d" % self.__hash__()
        self.userList = []
        return(None)

    def joinLobby(self, svrObj):
        ''' Handle shared lobby instance and start up the command loop '''
        if not svrObj.acctObj:
            return(False)

        if svrObj.acctObj not in self.userList:
            self.userList.append(svrObj.acctObj)

        lobbyCmd = LobbyCmd(svrObj)       # each user gets their own cmd shell
        try:
            lobbyCmd.cmdloop()            # start the lobby cmdloop
        finally:
            if svrObj.acctObj in self.userList:
                self.userList.remove(svrObj.acctObj)

    def sendMsg(self, svrObj):
        prompt = "You may send a message to one the the folowing users."
        prompt += self.showLogins()
        prompt += "Who do you want to send a message to? "
        inNum = svrObj.promptForNumberInput(prompt, len(self.userList))
        userObj = self.userList[inNum]
        prompt = "What is the message? "
        msgBuf = svrObj.promptForInput(prompt, '')
        if userObj.svrObj.spoolOut(msgBuf + '\n'):
            svrObj.spoolOut('Sent\n')

    def showLogins(self):
        ''' show an enumerated list of users '''
        buf = "Users:\n"
        for num, user in enumerate(self.userList):
            buf += '  (' + str(num) + ") " + user.getName() + "\n"
        return(buf)

    def debug(self):
        return(self.debugLobby)


class LobbyCmd(cmd.Cmd):
    def __init__(self, svrObj=None):
        self.svrObj = svrObj
        self.lobbyObj = svrObj.lobbyObj
        self.acctObj = svrObj.acctObj
        self._lastinput = ''

    def getCmdPrompt(self):
        sp = '['
        ep = ']'
        promptsize = self.acctObj.getPromptSize()

        if promptsize == 'brief':
            promptStr = ep + ' '
        else:
            promptStr = sp + 'lobby' + ep + ' '
        return(promptStr)

    def cmdloop(self):
        ''' Lobby cmd loop - requires user to be authenticated '''
        stop = False
        line = ""
        self.preloop()
        while not stop:
            if self.svrObj.promptForCommand(self.getCmdPrompt()):  # send/rcv
                line = self.svrObj.getInputStr()
                self._lastinput = line
                dLog("LOBBY cmd = " + line, self.lobbyObj.debug())
                self.precmd(line)
                stop = self.onecmd(line)
                self.postcmd(stop, line)
            else:
                stop = True
        self.postloop()

    def do_addcharacterondisk(self, line):
        ''' admin - add missing character (on disk) to account '''
        if not self.acctObj.isAdmin():
            self.svrObj.spoolOut('This command is for admins only.\n')
            return(False)

        charNamesFromDisk = self.acctObj.getCharactersOnDisk()
        if len(charNamesFromDisk) > 0:
            prompt = "Characters on Disk:\n  "
            prompt += "\n  ".join(charNamesFromDisk)
            prompt += "\nEnter character name or press [enter] to exit: "
            inStr = self.svrObj.promptForInput(prompt)
            buf = ''
            if inStr in charNamesFromDisk:
                self.acctObj.addCharacterToAccount(inStr)
                buf += inStr + " added to characterList\n"
                self.acctObj.save(logStr=__class__.__name__)
            else:
                buf += "Could not add " + inStr + " to characterList"
            self.svrObj.spoolOut(buf)
        return(False)

    def do_addcharactertoaccount(self, line):
        ''' admin - add missing character to account '''
        if not self.acctObj.isAdmin():
            self.svrObj.spoolOut('This command is for admins only.\n')
            return(False)

        name = self.svrObj.promptForInput("Char Name: ")
        self.acctObj.addCharacterToAccount(name)
        self.acctObj.save(logStr=__class__.__name__)
        return(False)

    def do_brief(self, line):
        ''' set lobby prompt to brief mode '''
        self.acctObj.setPromptSize("brief")

    def do_broadcast(self, line):
        ''' admin - send a message to all users '''
        if not self.acctObj.isAdmin():
            self.svrObj.spoolOut('This command is for admins only.\n')
            return(False)

        prompt = "What is the message? "
        msgBuf = self.svrObj.promptForInput(prompt, '')
        if self.svrObj.broadcast(msgBuf):
            self.svrObj.spoolOut('Sent\n')

    def do_cmdline(self, line):
        ''' admin - test - placeholder '''
        buf = ''
        cmdargs = self.svrObj.getInputStr().split(' ')
        cmd = cmdargs[0]
        self.svrObj.spoolOut(buf + cmd)

    def do_deletecharacterfromaccount(self, line):
        ''' admin - deletes character from account '''
        if not self.acctObj.isAdmin():
            self.svrObj.spoolOut('This command is for admins only.\n')
            return(False)

        name = self.svrObj.promptForInput("Char Name: ")
        self.acctObj.removeCharacterFromAccount(name)
        return(False)

    def do_exit(self, line):
        ''' exit the lobby and logoff '''
        self.svrObj.spoolOut('Leaving Lobby...\n')
        return(True)

    def do_quit(self, line):
        return(self.do_exit(line))

    def do_full(self, line):
        ''' set the lobby prompt to "full" mode '''
        self.acctObj.setPromptSize("full")

    def do_help(self, line):
        buf = ('play  - play the SoG game\n'
               'who   - show players logged in to the lobby\n' +
               'info  - get account information\n' +
               'brief - set lobby prompt to brief mode\n' +
               'full  - set lobby promp to full mode\n' +
               'msg - send a private message to one player\n' +
               'broadcast - send a message to all players\n' +
               'quit  - log out of lobby\n')
        self.svrObj.spoolOut(buf)

    def do_info(self, line):
        ''' display account info '''
        self.svrObj.spoolOut(self.acctObj.getInfo())

    def do_msg(self, line):
        ''' send a message to another user '''
        self.lobbyObj.sendMsg(self.svrObj)

    def do_game(self, line):
        ''' play the game '''
        self.svrObj.charObj = Character(self.svrObj,
                                        self.acctObj.getId())
        if self.svrObj.charObj.login():
            self.svrObj.gameObj.joinGame(self.svrObj)
        else:
            self.svrObj.charObj = None
            msg = "Error: Could not login to game"
            logging.warning(msg)
            self.svrObj.spoolOut(msg + '\n')
            self.acctObj.save(logStr=__class__.__name__)
        return(False)

    def do_g(self, line):
        return(self.do_game(line))

    def do_play(self, line):
        return(self.do_game(line))

    def do_prompt(self, line):
        ''' change the lobby prompt '''
        self.acctObj.setPromptSize('')
        self.acctObj.save(logStr=__class__.__name__)

    def do_setdisplayname(self, line):
        ''' change the account display name '''
        self.acctObj.setDisplayName(self.acctObj.promptForDisplayName())  # noqa: E501
        self.acctObj.save(logStr=__class__.__name__)

    def do_who(self, line):
        ''' show users that are logged in '''
        self.svrObj.spoolOut(self.lobbyObj.showLogins())


# instanciate the _Lobby class
_lobby = _Lobby()


def Lobby():
    ''' return a reference to the single, existing _lobby instance
        Thus, when we try to instanciate Lobby, we are just returning
        a ref to the existing Lobby '''

    return(_lobby)
