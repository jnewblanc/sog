''' threads.py - server side client and async thread classes
    * ClientThread - uses existing (or spins up) lobby/game instance
    * AsyncThread - uses existing (or spins up) game instance
    * Note: threads must be started before use'''

from datetime import datetime
import socket
import threading
import time

import account
from common.attributes import AttributeHelper
from common.ioLib import ServerIo
from common.general import logger
import common.globals
import game
import lobby


class ClientBase(ServerIo, AttributeHelper):
    ''' SuperClass for ClientThread
        * Contains everything the clientThread needs, except for network and
          threading specific features.  This way, tests can use ClientBase
          without needing to set up networking and client/server threads
        * Account Login is skipped and account is set to default account, which
          makes testing easier.  This behavior is expected to be overwritten
          by subClass, where we want real logins.
        * Main loop is modified for testing and is expcted to be overwritten
          by subClass
    '''
    def __init__(self):
        ServerIo.__init__(self)
        self.lobbyObj = lobby.Lobby()     # create/use single lobby instance
        self.gameObj = game.Game()        # create/use the single game instance
        self.acctObj = None
        self.charObj = None
        self._area = 'server'

        self._debugServer = False          # Turn on/off debug logging
        self._startdate = datetime.now()

        if self._debugServer:
            logger.info(str(self) + " New ClientThread")

    def __str__(self):
        ''' Str - often used as a prefix for logging '''
        return(__class__.__name__)

    def getId(self):
        return(1)

    def setDebug(self, debugBool=True):
        self._debugServer = bool(debugBool)

    def acctLogin(self):
        ''' Login - return true if successful
            * Auto Account Login
            * intended to be overwritten in subClass
        '''
        self.acctObj.email = 'default@example.com'
        self.password = 'default'
        self._displayName = 'defaultUser'
        return(True)

    def mainLoop(self):
        ''' Main loop of program
            * intended to be overwritten in subClass
        '''
        self.lobbyObj.joinLobby(self, self._test)
        if (self.acctObj):
            self.acctObj.logout()
        self.acctObj = None

    def serverLoop(self):
        ''' This is the main entry point into the app
            * intended to be overwritten in subClass
        '''
        logger.info(str(self) + " serverLoop started")
        try:
            while True:                             # Server loop
                self.welcome("Sog Server\n")
                self.acctObj = account.Account(self)
                if self.acctLogin():
                    self.mainLoop()
                else:
                    logger.warning(str(self) + ' Authentication failed')
                    self.acctObj = None
                    if not self.isRunning():
                        break                # exit loop to terminate
                    time.sleep(1)
        finally:
            logger.info(str(self) + "serverLoop complete")
        return(None)

        def setArea(self, area):
            self._area = area

        def getArea(self):
            if self._area:
                return(str(self._area))
            return(None)

        def isArea(self, area=''):
            if self._area:
                if self._area == area:
                    return(True)
            return(False)

    def getCmdPrompt(self):
        if self.isArea("game"):
            sp = '<'
            ep = '>'
            if self.charObj:
                promptsize = self.charObj.getPromptSize()
            elif self.acctObj:
                promptsize = self.acctObj.getPromptSize()
            else:
                promptsize = 'full'
        elif self.isArea("lobby"):
            sp = '['
            ep = ']'
            promptsize = self.acctObj.getPromptSize()
        else:
            sp = '('
            ep = ')'
            promptsize = 'full'

        if promptsize == 'brief':
            promptStr = ep + ' '
        else:
            promptStr = sp + self.getArea() + ep + ' '
        return(promptStr)

    def getConnectionList(self):
        ''' All connections to the game
            * intended to be overwritten in subClass, which uses client/server
        '''
        return([])

    def broadcast(self, data, header=None):
        ''' output a message to all users '''
        sentCount = 0
        logger.debug("broadcast - " + str(data))

        if data[-1] != '\n':        # Add newline if needed
            data += '\n'

        if not header:
            header = (self.txtBanner('Broadcast message from ' +
                      self.acctObj.getEmail()) + '\n> ')
        for client in self.getConnectionList():
            if client.id != self.id:
                client.spoolOut(header + data)
                sentCount += 1

        if sentCount:
            return(True)

        header = (self.txtBanner("No valid target for message." +
                  "  Sending to yourself") + "\n> ")
        self.spoolOut(header + data)     # send to myself

        return(False)

    def directMessage(self, data, who, header=None):
        ''' output a message to specific user '''
        sentCount = 0
        logger.debug("broadcast - " + str(data) + " - " + str(who))

        if data[-1] != '\n':        # Add newline if needed
            data += '\n'

        # toDo: this should be a name search, instead of a number from 'who'
        if self.isNum(who):
            if not header:
                header = (self.txtBanner('Private message from ' +
                          self.acctObj.getEmail()) + '\n> ')
            for client in self.getConnectionList():
                if client.id == int(who):
                    client.spoolOut(header + data)
                    sentCount += 1

        if sentCount:
            return(True)

        header = (self.txtBanner("No valid target for message." +
                  "  Sending to yourself") + "\n> ")
        self.spoolOut(header + data)     # send to myself

        return(False)


class ClientThread(threading.Thread, ClientBase):
    ''' Main client thread of the server
        * All non network, non-thread features should be part of the
          ClientBase superClass'''
    def __init__(self, socket, address, id):
        threading.Thread.__init__(self, daemon=True, target=self.serverLoop)
        ClientBase.__init__(self)
        self.socket = socket
        self.address = address
        self.id = id
        self._running = True
        self.identifier = "CT" + str(id) + str(address)

    def __str__(self):
        ''' Connection/Thread ID Str - often used as a prefix for logging '''
        return self.identifier

    # main program
    def serverLoop(self):
        ''' This is the main entry point into the app '''
        logger.info(str(self) + " Client connection established")
        try:
            while True:                             # Server loop
                self.welcome("Sog Server\n")
                self.acctObj = account.Account(self)
                if self.acctLogin():
                    self.mainLoop()
                else:
                    if not self.isRunning():
                        break                # exit loop to terminate
                    time.sleep(1)
            self.terminateClientConnection()
        finally:
            self.terminateClientConnection()
        return(None)

    def acctLogin(self):
        ''' Login - return true if successful '''
        loggedIn = False
        if self.acctObj.login():
            loggedIn = True
        else:
            logger.warning(str(self) + ' Authentication failed')
            self.acctObj = None

        if loggedIn:
            return(True)
        return(False)

    def mainLoop(self):
        ''' Main loop of program
            * Launch lobby loop
            * Logout of account if lobby loop is exited '''
        self.lobbyObj.joinLobby(self)
        if (self.acctObj):
            self.acctObj.logout()
        self.acctObj = None

    def isRunning(self):
        if not self._running:
            return(False)
        return(True)

    def getSock(self):
        return(self.socket)

    def getId(self):
        return(self.id)

    def getConnectionList(self):
        return(common.globals.connections)

    def removeConnectionFromList(self):
        if self in self.getConnectionList():
            logger.info(str(self) + " Client connection terminated")
            common.globals.connections.remove(self)
            common.globals.totalConnections -= 1

    def terminateClientConnection(self):
        ''' terminate the connection and clean up loose ends '''
        if self._running:
            self.removeConnectionFromList()
            self._running = False
            self.lobbyObj = None
            self.gameObj = None
            self.acctObj = None
            self.charObj = None

            try:
                self.socket.sendall(str.encode(common.globals.TERM_STR))
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except OSError:
                if self._debugServer:
                    logger.debug("Server term - Couldn't close " +
                                 "non-existent socket")
        return(None)


class AsyncThread(threading.Thread):
    ''' a separate worker thread for handling asyncronous tasks '''
    def __init__(self):
        self.gameObj = game.Game()   # create/use the single game instance
        self._debugAsync = False
        threading.Thread.__init__(self, daemon=True, target=self._asyncLoop)
        self._startdate = datetime.now()
        self._stopFlag = False

    def _asyncLoop(self):
        ''' Call the _asyncTasks method of the single game instance.
            * Thread control and tasks are handled in the game instance. '''
        if self._debugAsync:
            logger.debug(str(self) + 'AsyncThread._asyncMain')
        logger.info("Thread started - async worker")
        while not self._stopFlag:
            self.gameObj.asyncTasks()
            time.sleep(1)

    def halt(self):
        self._stopFlag = True
