''' i/o spool class '''

# import importlib
from common.general import Terminator, logger
import common.network
import queue
import re
import sys


class Spooler():
    ''' Superclass for I/O spooling '''
    def __init__(self):
        self._inputStr = ''                # user input buffer
        self._outputSpool = queue.Queue()  # output buffer
        self._debugIO = False              # Turn on/off debug logging
        self._maxPromptRetries = 10         # of times an input is retried

    def spoolOut(self, txt):
        ''' Append to output buffer '''
        self._outputSpool.put(str(txt))

    def getInputStr(self):
        ''' Get command from input buffer '''
        return(self._inputStr)

    def setInputStr(self, iStr):
        ''' Set the inputStr, replacing whatever was there before '''
        self._inputStr = str(iStr)

    def popOutSpool(self):
        ''' Return string with entirety of outpool spool.
            Output spool is emptied '''
        data = ''
        while not self._outputSpool.empty():
            data += self._outputSpool.get()
        return(data)

    def outputSpoolContains(self, str1):
        ''' returns True if given string is in the output spool
            * since the queue doesn't have a way to peek at it, we end up
              emptying and replacing the queue.
              * This is inefficient, but since the use case is rare and the
                queue is always small, we don't care.  Maybe someday we'll
                switch to a better queuing mechanism '''
        found = False
        newQueue = queue.Queue()
        while not self._outputSpool.empty():
            data = self._outputSpool.get()
            if re.match(str1, data):
                found = True
            newQueue.put(data)
        self._outputSpool = newQueue

        if found:
            return(True)
        return(False)

    def getMaxPromptRetries(self):
        return(self._maxPromptRetries)

    def promptForInput(self, promptStr, regex='', requirementsTxt=''):
        ''' prompt for string input - return str or empty if none '''
        for x in range(1, self.getMaxPromptRetries()):
            # logger.debug("PromptForInput try " + str(x))
            self.spoolOut(promptStr)
            oneStr = ''
            if self._sendAndReceive():
                oneStr = self.getInputStr()
            else:
                logger.debug("S&R returned False")

            if oneStr == '' or not self.isRunning():
                return('')
            elif regex == '' or re.match(regex, oneStr):
                return(oneStr)
            else:
                self.spoolOut(requirementsTxt)

        return('')

    # many of our menus are number driven, so use generic helper function.
    def promptForNumberInput(self, promptStr, maxNum=999999, minNum=0,
                             requirementsTxt=''):
        ''' prompt for number input and return integer - -1 = failed '''
        if requirementsTxt == '':
            requirementsTxt = ('Please select a number between ' +
                               str(minNum) + ' and ' + str(maxNum) + '\n')
        while True:
            self.spoolOut(promptStr)
            self._sendAndReceive()
            numStr = self.getInputStr()

            if re.match("^[0-9]+$", str(numStr)):
                if (int(numStr) >= minNum and int(numStr) <= maxNum):
                    return(int(numStr))
            elif numStr == '':
                return(-1)
            self.spoolOut(requirementsTxt)
        return(-1)

    def promptForYN(self, promptStr):
        ''' prompt for yes/no input - return True or False '''
        while True:
            self.spoolOut(promptStr + ' [y/N]: ')
            self._sendAndReceive()
            oneStr = self.getInputStr()
            if oneStr == 'y' or oneStr == 'Y':
                return(True)
            if oneStr == 'n' or oneStr == 'N':
                return(False)
        return(False)

    def promptForCommand(self, promptStr=''):
        ''' Prompt user for command '''
        if promptStr == '':
            promptStr = self.getCmdPrompt()

        self.spoolOut(promptStr)
        if self._sendAndReceive():
            return(True)
        return(False)

    def getCmdPrompt(self):
        ''' Default command prompt - expected to be overridden '''
        return("Input : ")

    def broadcast(self, data, who="all", header=None):
        ''' spool broadcast message
              * This is the simple terminal I/O version of the method
              * Originally written for the server, which has more complex
                functionality (i.e. broadcast to specific targets), but
                we wanted this to overrideable so that it can be used outside
                of the server (i.e. so things don't break when testing without
                sockets)
        '''
        if data[-1] != '\n':        # Add newline if needed
            data += '\n'
        if not header:
            header = "--- broadcast to " + str(who) + ": " + str(data)

        self.spoolOut(header + data)
        return(True)

    def welcome(self, welcomeMsg=''):
        ''' Welcome banner '''

        self.spoolOut(welcomeMsg)

        # pyfiglet_spec = importlib.util.find_spec("pyfiglet")
        #
        # if welcomeMsg == '':
        #     self.spoolOut(self.txtBanner("Welcome") + "\n")
        # else:
        #     self.spoolOut(welcomeMsg)
        #
        # if pyfiglet_spec:
        #     welcomeMsg = pyfiglet.figlet_format(welcomeMsg,    # noqa: F821
        #                                         font="slant")
        return(None)

    def txtBanner(self, msg, bChar='-'):
        ''' return a string containing a banner.
            Default is like this:
               ----- mymessage -----
        '''
        return(self.txtLine(lineChar=bChar, lineSize=5) + msg +
               self.txtLine(lineChar=bChar, lineSize=5))

    def txtLine(self, lineChar='-', lineSize=80):
        ''' return a string containing a line
            line size and character are customizable
            Default is like this:
               ----------------------------------------------------------------
        '''
        return(lineChar * lineSize)


class LocalIo(Spooler):
    ''' Superclass for client I/O spooling
        * _sendAndReceive is server specific.  Keep it separate so we can
          replace it when running tests'''
    def __init__(self):
        super().__init__()

    def _sendAndReceive(self):
        ''' Send data as output and recieve input
            This is the simple "terminal" case for send/receive, but it
            can be overwritten for client/server or for automated testing '''
        clientdata = ''
        dataToSend = self.popOutSpool()  # get data from spool

        print(dataToSend, end='')        # show data
        try:
            clientdata = input('')           # accept input
        except (KeyboardInterrupt, TypeError, AttributeError,
                KeyError, RecursionError, NameError):
            sys.exit(1)

        self.setInputStr(clientdata)     # store input

        return(True)


class TestIo(Spooler):
    ''' Superclass for client I/O spooling
        * _sendAndReceive is server specific.  Keep it separate so we can
          replace it when running tests'''
    def __init__(self):
        super().__init__()
        self._inputCmds = []
        self._cmdCounter = 0
        self._outputStr = ''

    def setInputs(self, inputList):
        self._inputCmds.append(inputList)

    def getOutput(self):
        return(self._outputStr)

    def _sendAndReceive(self):
        ''' Send data as output and recieve input
            This is the simple "terminal" case for send/receive, but it
            can be overwritten for client/server or for automated testing '''
        # Simulate output
        # pop output off the spool and storing it where we can retrieve it
        self._outputStr = self.popOutSpool()
        logger.info('testIo.sr output = ' + self._outputStr)

        # Simulate input by using the next unused input command in _inputCmds
        if self._cmdCounter < len(self._inputCmds):
            cmd = self._inputCmds[self._cmdCounter]
        else:
            cmd = 'exit'
        self._cmdCounter += 1
        self.setInputStr(cmd)     # store input
        logger.info('testIo.sr input = ' + self.cmd)

        return(True)


class ServerIo(Spooler):
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
                    logger.debug("Server received NO_OP from client")
            elif clientdata == common.network.TERM_STR:  # client shut down
                if self._debugServer:
                    logger.debug("Server received TERM_STR from client")
                self.terminateClientConnection()
                return(False)
            elif clientdata == common.network.STOP_STR:  # server shut down
                if self._debugServer:
                    logger.debug("Server received STOP_STR from client")
                self.terminateClientConnection()
                raise Terminator
                return(False)
            self.setInputStr(clientdata)
        else:
            logger.debug(str(self) + ' No clientdata returned')
            return(False)
        return(True)
