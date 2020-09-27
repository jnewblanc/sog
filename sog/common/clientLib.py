#!/usr/bin/env python
""" SoG client

   * runs a simple client that connect to a SoG server
   * connection is persistent

 ToDo:
   * improve connection timeout
   * offiscate/encode password input??
   *
 """

import getpass
import time
import socket
import traceback

from common.attributes import AttributeHelper
from common.globals import HOST, PORT, BYTES_TO_TRANSFER
from common.globals import NOOP_STR, TERM_STR, STOP_STR
from common.general import dateStr


class Client(AttributeHelper):
    def __init__(self):
        self.socket = None
        self.input = ""
        self.output = ""
        self.listenTimeout = 10
        self.socketTimeout = 30
        self._debugIO = False

        self._running = True
        self._receivedInput = False  # gets set the first time input is entered

    def start(self, args):
        if self.connect(args):
            print("Client: Started at {}.  ".format(dateStr("now")) +
                  "Enter [term] to perform a hard stop")
            self.dataLoop(args)
            print("Client: Finished.")
        self.disconnect()

    def receiveData(self):
        self.output = ""
        try:
            if self.getDebug():
                print("Client: REC: Waiting to receive data")
            data = self.socket.recv(BYTES_TO_TRANSFER)
            if self.getDebug():
                print("Client: REC: Data received ({})".format(len(data)))
            self.output = str(data.decode("utf-8"))
            return True
        except OSError:
            if self.getDebug():
                print("Client: OSError")
                traceback.print_last()
            return False
        return True

    def sendData(self):
        if str(self.input) == "":
            self.input = NOOP_STR
        try:
            if self.getDebug():
                print("Client: SEND: " + self.input)
            self.socket.sendall(str.encode(self.input))
            if self.getDebug():
                print("Client: SEND: Data Sent")
            self.input = ""
            return True
        except OSError:
            return False
        return True

    def disconnect(self):
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except OSError:
                pass
        self.socket = None

    def connect(self, args):
        """ Set up the connection """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self.socketTimeout)

        svrhost = args.host or HOST
        svrport = int(args.port or PORT)
        try:
            self.socket.connect((svrhost, svrport))
            if self.getDebug():
                print("Client: Connection established at {}:{}".format(
                    svrhost, svrport))
        except ConnectionRefusedError:
            print("Client: Server is refusing connections at {}:{}".format(svrhost,
                                                                           svrport))
            return False
        return True

    def dataLoop(self, args):
        """ Recieve data, get input, send data """
        while self.isRunning:
            time.sleep(1)
            if self.receiveData():
                if not self.postProcessOutput(args):
                    break
                print(self.output, end="", flush=True)
            else:
                print("Client: No data received from server")

            if self.isRunning():
                if (
                    self.output == "Enter Password: "
                    or self.output == "Verify Password: "
                    or self.output == "Enter Account Password: "
                ):
                    time.sleep(1)
                    self.input = getpass.getpass("")
                else:
                    self.input = input()
                    self._receivedInput = True

                self.preProcessInput()

            if not self.sendData():
                print("Client: Error while sending data.  Aborting")
                break

    def isRunning(self):
        return self._running

    def terminate(self, outStr):
        self.sendData()
        time.sleep(1)
        self._running = False
        print(str(outStr))

    def setDebug(self, debugBool=True):
        self._debugIO = bool(debugBool)

    def getDebug(self):
        return self._debugIO

    def preProcessInput(self):
        """ process user input before sending to the server
            * used for client side input processing """
        if self.input == "term":
            self.input = TERM_STR  # set input as final term string
            self.terminate("Client: termination by client")
        if self.input == "stopsvr":
            self.input = STOP_STR  # set input as final term string
            self.terminate("Client: termination by client")

    def postProcessOutput(self, args):
        """ process server output before displaying to the user
            * used for client side output processing and/or canned response """
        if self.output == TERM_STR:
            self.terminate("Client: termination by server")
            return False
        elif args.username and not self._receivedInput:
            self.input = args.username
            self.sendData()
            time.sleep(1)
            self.receiveData()
            print("Autofilled username")
            args.username = ""  # single use
            if args.password:
                self.input = args.password
                self.sendData()
                time.sleep(1)
                self.receiveData()
                print("Autofilled password")
                args.password = ""  # single use
        return True
