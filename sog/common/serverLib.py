#!/usr/bin/env python
''' SoG server library module
   * server - runs the server loop, including exception handler, and log setup
   * helper functions for starting/stopping threads
'''

import logging
from pathlib import Path
# import selectors
import socket
import sys
import time

import common.network
from common.paths import LOGDIR
import common.serverLib
from common.general import Terminator
from threads import ClientThread, AsyncThread
import game


def server(email=''):
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

    asyncThread = createAndStartAsyncThread()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serverHandle:

            serverHandle.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            serverHandle.bind((common.network.HOST, common.network.PORT))

            while True:
                serverHandle.listen(1)
                serverHandle.settimeout(60)

                try:
                    clientsock, clientAddress = serverHandle.accept()

                    newthread = ClientThread(clientsock, clientAddress,
                                             common.network.totalConnections)
                    common.network.connections.append(newthread)
                    common.network.totalConnections += 1
                    common.network.connections[newthread.getId()].start()
                except OSError:
                    # This seems to happen when timeout occurs, but isn't fatal
                    logging.warning("socket accept() failed - timeout?")

                time.sleep(1)

            exitProg()

    except Terminator:
        haltAsyncThread(game.Game(), asyncThread)
        haltClientThreads()
        exitProg()


def haltAsyncThread(gameObj, asyncThread):
    if asyncThread:
        logging.info("Halting asyncThread")
        asyncThread.halt()
        asyncThread.join()


def haltClientThreads():
    for num, client in enumerate(common.network.connections):
        logging.info("Halting ClientThread " + str(num))
        client.terminateClientConnection()
        client.join()


def createAndStartAsyncThread():
    asyncThread = AsyncThread()
    if asyncThread:
        asyncThread.start()
        return(asyncThread)


def exitProg(statusCode=0):
    ''' Cleanup and Exit program '''
    logging.info("Server Exit - " + sys.argv[0])

    # exit server
    try:
        sys.exit(statusCode)
    except SystemExit:
        pass
