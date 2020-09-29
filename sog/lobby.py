""" lobby class """
# lobby class is set up to be a single instance

import cmd
from character import Character

from common.general import logger, dLog


class _Lobby:
    """ Single instance of the lobby class, shared by all users
        (see instanciation magic at the bottom of the file)"""

    _instanceDebug = False

    def __init__(self):
        self.instance = "Instance at %d" % self.__hash__()
        self.userList = []
        return None

    def joinLobby(self, client, testFlag=False):
        """ Handle shared lobby instance and start up the command loop """
        if not client.acctObj:
            return False

        if client.acctObj not in self.userList:
            self.userList.append(client.acctObj)

        lobbyCmd = LobbyCmd(client)  # each user gets their own cmd shell
        try:
            lobbyCmd.cmdloop()  # start the lobby cmdloop
        finally:
            if client.acctObj in self.userList:
                self.userList.remove(client.acctObj)

    def sendMsg(self, client):
        prompt = "You may send a message to one the the folowing users."
        prompt += self.showLogins()
        prompt += "Who do you want to send a message to? "
        inNum = client.promptForNumberInput(prompt, len(self.userList))
        userObj = self.userList[inNum]
        prompt = "What is the message? "
        msgBuf = client.promptForInput(prompt, "")
        if userObj.client.spoolOut(msgBuf + "\n"):
            client.spoolOut("Sent\n")

    def showLogins(self):
        """ show an enumerated list of users """
        buf = "Users:\n"
        for num, user in enumerate(self.userList):
            buf += "  (" + str(num) + ") " + user.getName() + "\n"
        return buf

    def debug(self):
        return self._instanceDebug


class LobbyCmd(cmd.Cmd):
    def __init__(self, client=None):
        self.client = client
        self.lobbyObj = client.lobbyObj
        self.acctObj = client.acctObj
        self._lastinput = ""

    def getCmdPrompt(self):
        sp = "["
        ep = "]"
        promptsize = self.acctObj.getPromptSize()

        if promptsize == "brief":
            promptStr = ep + " "
        else:
            promptStr = sp + "lobby" + ep + " "
        return promptStr

    def cmdloop(self):
        """ cmd method override - Lobby cmd loop
            requires user to be authenticated """
        stop = False
        line = ""
        self.preloop()
        while not stop:
            if self.client.promptForCommand(self.getCmdPrompt()):  # send/rcv
                line = self.client.getInputStr()
                self._lastinput = line
                dLog("LOBBY cmd = " + line, self.lobbyObj.debug())
                self.precmd(line)
                stop = self.onecmd(line)
                self.postcmd(stop, line)
            else:
                stop = True
        self.postloop()

    def default(self, line):
        """ cmd method override """
        logger.warn("*** Invalid lobby command: %s\n" % line)
        self.client.spoolOut("Invalid Command\n")

    def do_addcharacterondisk(self, line):
        """ admin - add missing character (on disk) to account """
        if not self.acctObj.isAdmin():
            self.client.spoolOut("This command is for admins only.\n")
            return False

        charNamesFromDisk = self.acctObj.getCharactersOnDisk()
        if len(charNamesFromDisk) > 0:
            prompt = "Characters on Disk:\n  "
            prompt += "\n  ".join(charNamesFromDisk)
            prompt += "\nEnter character name or press [enter] to exit: "
            inStr = self.client.promptForInput(prompt)
            buf = ""
            if inStr in charNamesFromDisk:
                self.acctObj.addCharacterToAccount(inStr)
                buf += inStr + " added to characterList\n"
                self.acctObj.save(logStr=__class__.__name__)
            else:
                buf += "Could not add " + inStr + " to characterList"
            self.client.spoolOut(buf)
        return False

    def do_addcharactertoaccount(self, line):
        """ admin - add missing character to account """
        if not self.acctObj.isAdmin():
            self.client.spoolOut("This command is for admins only.\n")
            return False

        name = self.client.promptForInput("Char Name: ")
        self.acctObj.addCharacterToAccount(name)
        self.acctObj.save(logStr=__class__.__name__)
        return False

    def do_brief(self, line):
        """ set lobby prompt to brief mode """
        self.acctObj.setPromptSize("brief")

    def do_broadcast(self, line):
        """ admin - send a message to all users """
        if not self.acctObj.isAdmin():
            self.client.spoolOut("This command is for admins only.\n")
            return False

        prompt = "What is the message? "
        msgBuf = self.client.promptForInput(prompt, "")
        if self.client.broadcast(msgBuf):
            self.client.spoolOut("Sent\n")

    def do_cmdline(self, line):
        """ admin - test - placeholder """
        buf = ""
        cmdargs = self.client.getInputStr().split(" ")
        cmd = cmdargs[0]
        self.client.spoolOut(buf + cmd)

    def do_deletecharacterfromaccount(self, line):
        """ admin - deletes character from account """
        if not self.acctObj.isAdmin():
            self.client.spoolOut("This command is for admins only.\n")
            return False

        name = self.client.promptForInput("Char Name: ")
        self.acctObj.removeCharacterFromAccount(name)
        return False

    def do_exit(self, line):
        """ exit the lobby and logoff """
        self.client.spoolOut("Leaving Lobby...\n")
        return True

    def do_quit(self, line):
        return self.do_exit(line)

    def do_full(self, line):
        """ set the lobby prompt to "full" mode """
        self.acctObj.setPromptSize("full")

    def do_help(self, line):
        HELP_FORMAT = "  {:10} - {}\n"
        buf = ''.join([
            HELP_FORMAT.format("play", "play the SoG game"),
            HELP_FORMAT.format("who", "show players logged in to the lobby"),
            HELP_FORMAT.format("info", "display your account information"),
            HELP_FORMAT.format("msg", "send a private message to one player"),
            HELP_FORMAT.format("broadcast", "send a message to all players"),
            HELP_FORMAT.format("brief/full", "toggle lobby prompt"),
            HELP_FORMAT.format("quit", "log out of lobby")
        ])
        self.client.spoolOut(buf)

    def do_info(self, line):
        """ display account info """
        self.client.spoolOut(self.acctObj.getInfo())

    def do_msg(self, line):
        """ send a message to another user """
        self.lobbyObj.sendMsg(self.client)

    def do_game(self, line):
        """ play the game """
        self.client.charObj = Character(self.client, self.acctObj.getId())
        if self.client.charObj.login():
            self.client.gameObj.joinGame(self.client)
        else:
            self.client.charObj = None
            msg = "Could not login to game"
            logger.warning(msg)
            self.client.spoolOut("Error: " + msg + "\n")
            self.acctObj.save(logStr=__class__.__name__)
        return False

    def do_g(self, line):
        return self.do_game(line)

    def do_play(self, line):
        return self.do_game(line)

    def do_prompt(self, line):
        """ change the lobby prompt """
        self.acctObj.setPromptSize("")
        self.acctObj.save(logStr=__class__.__name__)

    def do_setdisplayname(self, line):
        """ change the account display name """
        self.acctObj.setDisplayName(self.acctObj.promptForDisplayName())  # noqa: E501
        self.acctObj.save(logStr=__class__.__name__)

    def do_who(self, line):
        """ show users that are logged in """
        self.client.spoolOut(self.lobbyObj.showLogins())


# instanciate the _Lobby class
_lobby = _Lobby()


def Lobby():
    """ return a reference to the single, existing _lobby instance
        Thus, when we try to instanciate Lobby, we are just returning
        a ref to the existing Lobby """

    return _lobby
