#!/usr/bin/env python
''' SoG server

 Entry point
   * runs as a server
   * Handles account creation/authentication
   * Hands you off to the lobby, which is a single instance
 '''

import logging
from pathlib import Path
# import selectors
from signal import signal, SIGINT
import socket
import sys
import threading
import time

import account
from common.attributes import AttributeHelper
from common.ioLib import IoLib
from common.network import HOST, PORT, BYTES_TO_TRANSFER
from common.network import NOOP_STR, TERM_STR, STOP_STR
from common.paths import LOGDIR
import character
import lobby
import game

connections = []
totalConnections = 0


class ServerThread(threading.Thread, IoLib, AttributeHelper):
    def __init__(self, socket, address, id):
        threading.Thread.__init__(self)
        IoLib.__init__(self)
        self.socket = socket
        self.address = address
        self.id = id
        self._running = True

        self.lobbyObj = lobby.Lobby()     # create single lobby instance
        self.gameObj = game.Game()             # create single game instance
        self.acctObj = None
        self.charObj = None
        self.identifier = "SVR" + str(id) + str(address)

        self._area = "lobby"               # place user in the lobby
        self._debugServer = False          # Turn on/off debug logging

        if self._debugServer:
            logging.info(str(self) + " New connection")

    def __str__(self):
        ''' Connection/Thread ID Str - often used as a prefix for logging '''
        return self.identifier

    def loggedInLoop(self, acctObj):
        ''' Main active loop, once user is logged in. '''
        if not acctObj:
            return(False)

        self.setArea("lobby")

        while True:
            if self.promptForCommand():  # send/receive outpt/input
                # logging.debug("Area: ", self.getArea())
                if self.isArea('lobby'):
                    if not self.lobbyObj.processCommand(self):
                        return(False)
                if self.isArea('game'):
                    if not self.charObj:      # login as character
                        self.charObj = character.Character(self, self.acctObj.getId())  # noqa: E501
                        if self.charObj.login():
                            self.gameObj.joinGame(self)
                        else:
                            self.charObj = None
                            msg = "Error: Could not login to game"
                            logging.warning(msg)
                            self.spoolOut(msg + '\n')
                            self.setArea("lobby")
                    else:                 # Process game commands
                        if not self.gameObj.processCommand(self):
                            self.setArea("lobby")
                if self.isArea('exit') or not self.isRunning():
                    break                  # exit loop to logout
            else:
                break
        return(False)

    # main program
    def run(self):
        ''' This is the main entry point into the app '''
        logging.info(str(self) + " Client connection established")
        try:
            while True:                             # Server loop
                self.welcome("Sog Server\n")
                self.acctObj = account.Account(self)
                if self.acctObj.login():
                    self.loggedInLoop(self.acctObj)
                    if (self.acctObj):
                        self.acctObj.logout()
                    self.acctObj = None
                else:
                    logging.debug(str(self) + ' Authentication failed')
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

    def _sendAndReceive(self):
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
                    logging.debug(str(self) + " SENDING:\n" + dataToSend)
                self.socket.sendall(str.encode(dataToSend))
                if self._debugServer:
                    logging.debug(str(self) + " SEND: Data Sent")
            except (ConnectionResetError, ConnectionAbortedError):
                self.terminateClientConnection()
                return(False)
            except IOError:
                pass

            try:
                if self._debugServer:
                    logging.debug(str(self) + " REC: Waiting for input")
                clientdata = self.socket.recv(BYTES_TO_TRANSFER)
                if self._debugServer:
                    logging.debug(str(self) + " REC: " +
                                  str(clientdata.decode("utf-8")))
            except (ConnectionResetError, ConnectionAbortedError):
                self.terminateClientConnection()
                return(False)
            except IOError:
                pass
        else:
            logging.debug(str(self) + ' No socket to receive input from')
            return(False)

        if clientdata:
            clientdata = str(clientdata.decode("utf-8"))
            if clientdata == NOOP_STR:  # special case for empty sends
                clientdata = ""
                if self._debugServer:
                    logging.debug("Server recieved NO_OP from client")
            elif clientdata == TERM_STR:  # client is shutting down
                if self._debugServer:
                    logging.debug("Server recieved TERM_STR from client")
                self.terminateClientConnection()
                return(False)
            elif clientdata == STOP_STR:  # client requested server shut down
                if self._debugServer:
                    logging.debug("Server recieved STOP_STR from client")
                self.terminateClientConnection()
                exitProg()
                return(False)
            self.setInputStr(clientdata)
        else:
            logging.debug(str(self) + ' No clientdata returned')
            return(False)
        return(True)

    def terminateClientConnection(self):
        ''' terminate the connection and clean up loose ends '''
        global totalConnections

        if self._running:
            if self in connections:
                logging.info(str(self) + " Client connection terminated")
                connections.remove(self)
                totalConnections = totalConnections - 1
            self._running = False
            self.setArea("lobby")
            self.lobbyObj = None
            self.gameObj = None
            self.acctObj = None
            self.charObj = None

            try:
                self.socket.sendall(str.encode(TERM_STR))  # Notify Client
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except OSError:
                if self._debugServer:
                    logging.debug("Server term - Couldn't close " +
                                  "non-existent socket")
        return(None)

    def broadcast(self, data, who="all", header=None):
        ''' output a message to all users '''
        sentCount = 0
        logging.debug("broadcast - " + str(data) + " - " + str(who))
        if data[-1] != '\n':        # Add newline if needed
            data += '\n'
        if who == 'all':            # broadcast to all other clients
            if not header:
                header = (self.txtBanner('Broadcast message from ' +
                          self.acctObj.getEmail()) + '\n> ')
            for client in connections:
                if client.id != self.id:
                    client.spoolOut(header + data)
                    sentCount += 1
        elif who == 'game':           # broadcast to all other players in game
            if not header:
                header = (self.txtBanner('Broadcast message from ' +
                          self.acctObj.getEmail(), bChar='=') + '\n> ')
            for onechar in self.gameObj.getCharacterList():
                onechar.svrObj.spoolOut(header + data)
                sentCount += 1
        elif self.isNum(who):       # send only to specified client
            if not header:
                header = (self.txtBanner('Private message from ' +
                          self.acctObj.getEmail()) + '\n> ')
            for client in connections:
                if client.id == int(who):
                    client.spoolOut(header + data)
                    sentCount += 1
        else:
            header = (self.txtBanner("No valid target for message." +
                      "  Sending to yourself") + "\n> ")
            self.spoolOut(header + data)     # send to myself

        if sentCount:
            return(True)
        return(False)

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

    def setDebug(self, debugBool=True):
        self._debugServer = bool(debugBool)


def main(email=''):
    global totalConnections

    # Set up logging
    logpath = Path(LOGDIR)
    logpath.mkdir(parents=True, exist_ok=True)
    FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
    logging.basicConfig(filename=(LOGDIR + '/system.log'),
                        level=logging.DEBUG,
                        format=FORMAT, datefmt='%m/%d/%y %H:%M:%S')
    logging.info("-------------------------------------------------------")
    logging.info("Server Start - " + sys.argv[0])
    print("Logs: " + LOGDIR + '\\system.log')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serverHandle:

        serverHandle.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serverHandle.bind((HOST, PORT))

        while True:
            serverHandle.listen(1)
            serverHandle.settimeout(60)

            try:
                clientsock, clientAddress = serverHandle.accept()
            except OSError:
                logging.error("Nobody listening - socket accept() failed")
                break

            newthread = ServerThread(clientsock, clientAddress,
                                     totalConnections)
            connections.append(newthread)
            logging.info(str(newthread) + " Thread started")
            totalConnections += 1
            connections[newthread.getId()].start()

    exitProg()


def sig_handler(signal_received, frame):
    print('SIGINT or CTRL-C detected. Exiting gracefully')

    exitProg()


def exitProg(statusCode=0):
    ''' Cleanup and Exit program '''
    logging.info("Server Exit - " + sys.argv[0])
    try:
        sys.exit(statusCode)
    except SystemExit:
        pass


# -------------
if __name__ == '__main__':
    signal(SIGINT, sig_handler)  # run function when SIGINT is recieved
    print('Running. Press CTRL-C to exit.  (might wait for a connection)')

    main()
