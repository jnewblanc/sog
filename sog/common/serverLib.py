#!/usr/bin/env python
""" SoG server library module
   * server - runs the server loop, including exception handler
   * helper functions for starting/stopping threads
   * Threads are instanciated from threads.ClientThread
"""

# import selectors
import socket
import sys
import time

import common.globals
import common.serverLib
from common.general import Terminator, logger
from threads import ClientThread, AsyncThread
import game


def server(email=""):
    asyncThread = None
    logger.info("-------------------------------------------------------")
    logger.info("Server Start - {} - Listening on {}:{}".format(
        sys.argv[0], common.globals.HOST, common.globals.PORT))

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serverHandle:

            serverHandle.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            serverHandle.bind((common.globals.HOST, common.globals.PORT))

            while True:

                if not threadIsRunning(asyncThread):
                    asyncThread = createAndStartAsyncThread()

                serverHandle.listen(1)
                serverHandle.settimeout(60)

                try:
                    clientsock, clientAddress = serverHandle.accept()

                    newthread = ClientThread(
                        clientsock, clientAddress, common.globals.totalConnections
                    )
                    common.globals.connections.append(newthread)
                    common.globals.totalConnections += 1
                    common.globals.connections[newthread.getId()].start()
                except OSError:
                    # This seems to happen when timeout occurs, but isn't fatal
                    logger.warning("socket accept() failed - timeout?")

                time.sleep(1)

            exitProg()

    except Terminator:
        haltAsyncThread(game.Game(), asyncThread)
        haltClientThreads()
        exitProg()


def haltAsyncThread(gameObj, asyncThread):
    if asyncThread:
        logger.info("Halting asyncThread")
        asyncThread.halt()
        asyncThread.join()


def haltClientThreads():
    for num, client in enumerate(common.globals.connections):
        logger.info("Halting ClientThread " + str(num))
        client.terminateClientConnection()
        client.join()


def createAndStartAsyncThread():
    asyncThread = AsyncThread()
    if asyncThread:
        logger.info("Starting AsyncThread")
        asyncThread.start()
        return asyncThread


def threadIsRunning(threadHandle):
    if not threadHandle:
        return(False)
    if threadHandle.is_alive():
        return(True)
    return(False)


def exitProg(statusCode=0):
    """ Cleanup and Exit program """
    logger.info("Server Exit - " + sys.argv[0])

    # exit server
    try:
        sys.exit(statusCode)
    except SystemExit:
        pass
