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
from signal import signal, SIGINT, SIGTERM
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
import lobby
import game

connections = []
totalConnections = 0


class Terminator(Exception):
    """ Custom exception to trigger termination of all threads & main. """
    pass


class ClientThread(threading.Thread, IoLib, AttributeHelper):
    def __init__(self, socket, address, id):
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

        if self._debugServer:
            logging.info(str(self) + " New ClientThread")

    def __str__(self):
        ''' Connection/Thread ID Str - often used as a prefix for logging '''
        return self.identifier

    # main program
    def serverMain(self):
        ''' This is the main entry point into the app '''
        logging.info(str(self) + " Client connection established")
        try:
            while True:                             # Server loop
                self.welcome("Sog Server\n")
                self.acctObj = account.Account(self)
                if self.acctObj.login():
                    self.lobbyObj.joinLobby(self)
                    if (self.acctObj):
                        self.acctObj.logout()
                    self.acctObj = None
                else:
                    logging.warning(str(self) + ' Authentication failed')
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
                raise Terminator
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
        logging.debug("broadcast - " + str(data))

        if data[-1] != '\n':        # Add newline if needed
            data += '\n'

        if not header:
            header = (self.txtBanner('Broadcast message from ' +
                      self.acctObj.getEmail()) + '\n> ')
        for client in connections:
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
        logging.debug("broadcast - " + str(data) + " - " + str(who))

        if data[-1] != '\n':        # Add newline if needed
            data += '\n'

        # toDo: this should be a name search, instead of a number from 'who'
        if self.isNum(who):
            if not header:
                header = (self.txtBanner('Private message from ' +
                          self.acctObj.getEmail()) + '\n> ')
            for client in connections:
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
        threading.Thread.__init__(self, daemon=True, target=self._asyncMain)

    def _asyncMain(self):
        ''' Call the _asyncTasks method of the single game instance.
            * Thread control and tasks are handled in the game instance. '''
        if self._debugAsync:
            logging.debug(str(self) + 'AsyncThread._asyncMain')
        self.gameObj._asyncTasks()


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

    asyncThread = AsyncThread()
    asyncThread.start()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serverHandle:

            serverHandle.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            serverHandle.bind((HOST, PORT))

            while True:
                serverHandle.listen(1)
                serverHandle.settimeout(60)

                try:
                    clientsock, clientAddress = serverHandle.accept()

                    newthread = ClientThread(clientsock, clientAddress,
                                             totalConnections)
                    connections.append(newthread)
                    totalConnections += 1
                    connections[newthread.getId()].start()
                except OSError:
                    # This seems to happen when timeout occurs, but isn't fatal
                    logging.warning("socket accept() failed - timeout?")

                time.sleep(1)

            exitProg()

    except Terminator:
        logging.info("Terminator: Halting asyncThread")
        gameObj = game.Game()
        gameObj.haltAsyncThread()
        asyncThread.join()

        # Halt client threads
        for num, client in enumerate(connections):
            logging.info("Terminator: Halting ClientThread " + str(num))
            client.terminateClientConnection()
            client.join()

        exitProg()


def sig_handler(signal_received, frame):
    print('SIGINT, SIGTERM, or CTRL-C detected. Exiting gracefully')
    raise Terminator


def exitProg(statusCode=0):
    ''' Cleanup and Exit program '''
    logging.info("Server Exit - " + sys.argv[0])

    # exit main
    try:
        sys.exit(statusCode)
    except SystemExit:
        pass


# -------------
if __name__ == '__main__':
    signal(SIGINT, sig_handler)  # run function when SIGINT is recieved
    signal(SIGTERM, sig_handler)  # run function when SIGITERM is recieved
    print('Running. Press CTRL-C to exit.  (might wait for a connection)')

    main()
