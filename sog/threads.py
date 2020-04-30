#!/usr/bin/env python
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
from common.ioLib import IoLib
from common.general import Terminator, logger
import common.network
import game
import lobby


class ClientThread(threading.Thread, IoLib, AttributeHelper):
    def __init__(self, socket, address, id, clientThreadInitCallBack=None):
        threading.Thread.__init__(self, daemon=True, target=self.serverMain)
        IoLib.__init__(self)
        self.socket = socket
        self.address = address
        self.id = id
        self._running = True

        self.lobbyObj = lobby.Lobby()     # create/use single lobby instance
        self.gameObj = game.Game()        # create/use the single game instance
        self.acctObj = None
        self.charObj = None
        self.identifier = "CT" + str(id) + str(address)
        self._area = 'server'

        self._debugServer = False          # Turn on/off debug logging
        self._startdate = datetime.now()

        # This is a hook that allows tests to set some vars
        self._test = False
        if clientThreadInitCallBack:
            self._testCallback = clientThreadInitCallBack
            self._test = True

        if self._debugServer:
            logger.info(str(self) + " New ClientThread")

    def __str__(self):
        ''' Connection/Thread ID Str - often used as a prefix for logging '''
        return self.identifier

    # main program
    def serverMain(self):
        ''' This is the main entry point into the app '''
        logger.info(str(self) + " Client connection established")
        try:
            while True:                             # Server loop
                self.welcome("Sog Server\n")
                self.acctObj = account.Account(self)
                enterLobby = False
                if self._test:
                    # This is a hook that allows tests to create the acctObj
                    self._testCallback(self)
                    enterLobby = True
                else:
                    if self.acctObj.login():
                        enterLobby = True
                if enterLobby:
                    self.lobbyObj.joinLobby(self, self._test)
                    if (self.acctObj):
                        self.acctObj.logout()
                    self.acctObj = None
                else:
                    logger.warning(str(self) + ' Authentication failed')
                    self.acctObj = None
                    if not self.isRunning():
                        break                # exit loop to terminate
                    time.sleep(1)
            self.terminateClientConnection()
        finally:
            self.terminateClientConnection()
        return(None)

    def isRunning(self):
        if not self._running:
            return(False)
        return(True)

    def getSock(self):
        return(self.socket)

    def getId(self):
        return(self.id)

    def _sendAndReceive(self):     # noqa: C901
        ''' All client Input and output function go through here
              * Override IOspool for client/server communication
              * send and recieve is connected in a single transaction
              * Data to be sent comes from the outputSpool queue
              * Data Recieveed goed into the inputStr var '''
        clientdata = ''
        dataToSend = self.popOutSpool()

        if self.socket:
            try:
                # send the data
                if self._debugServer:
                    logger.debug(str(self) + " SENDING:\n" + dataToSend)
                self.socket.sendall(str.encode(dataToSend))
                if self._debugServer:
                    logger.debug(str(self) + " SEND: Data Sent")
            except (ConnectionResetError, ConnectionAbortedError):
                self.terminateClientConnection()
                return(False)
            except IOError:
                pass

            try:
                if self._debugServer:
                    logger.debug(str(self) + " REC: Waiting for input")
                clientdata = self.socket.recv(common.network.BYTES_TO_TRANSFER)
                if self._debugServer:
                    logger.debug(str(self) + " REC: " +
                                 str(clientdata.decode("utf-8")))
            except (ConnectionResetError, ConnectionAbortedError):
                self.terminateClientConnection()
                return(False)
            except IOError:
                pass
        else:
            logger.debug(str(self) + ' No socket to receive input from')
            return(False)

        if clientdata:
            clientdata = str(clientdata.decode("utf-8"))
            if clientdata == common.network.NOOP_STR:  # empty sends
                clientdata = ""
                if self._debugServer:
                    logger.debug("Server recieved NO_OP from client")
            elif clientdata == common.network.TERM_STR:  # client shut down
                if self._debugServer:
                    logger.debug("Server recieved TERM_STR from client")
                self.terminateClientConnection()
                return(False)
            elif clientdata == common.network.STOP_STR:  # server shut down
                if self._debugServer:
                    logger.debug("Server recieved STOP_STR from client")
                self.terminateClientConnection()
                raise Terminator
                return(False)
            self.setInputStr(clientdata)
        else:
            logger.debug(str(self) + ' No clientdata returned')
            return(False)
        return(True)

    def terminateClientConnection(self):
        ''' terminate the connection and clean up loose ends '''
        if self._running:
            if self in common.network.connections:
                logger.info(str(self) + " Client connection terminated")
                common.network.connections.remove(self)
                common.network.totalConnections -= 1
            self._running = False
            self.lobbyObj = None
            self.gameObj = None
            self.acctObj = None
            self.charObj = None

            try:
                self.socket.sendall(str.encode(common.network.TERM_STR))
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except OSError:
                if self._debugServer:
                    logger.debug("Server term - Couldn't close " +
                                 "non-existent socket")
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

    def broadcast(self, data, header=None):
        ''' output a message to all users '''
        sentCount = 0
        logger.debug("broadcast - " + str(data))

        if data[-1] != '\n':        # Add newline if needed
            data += '\n'

        if not header:
            header = (self.txtBanner('Broadcast message from ' +
                      self.acctObj.getEmail()) + '\n> ')
        for client in common.network.connections:
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
            for client in common.network.connections:
                if client.id == int(who):
                    client.spoolOut(header + data)
                    sentCount += 1

        if sentCount:
            return(True)

        header = (self.txtBanner("No valid target for message." +
                  "  Sending to yourself") + "\n> ")
        self.spoolOut(header + data)     # send to myself

        return(False)

    def setDebug(self, debugBool=True):
        self._debugServer = bool(debugBool)


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
