#!/usr/bin/env python
""" SoG client

 Entry point to the SoG client
   * Create a persistent connection
   * Hand off the connection to the Client class
   * Allow username on the command line
   * Allow password on the command line (admittedly, insecure)

Related files:
   * common/clientLib
   * common/network
"""

import argparse

from common.clientLib import Client


def main():

    parser = argparse.ArgumentParser(description="Client for SoG")
    parser.add_argument("--username", type=str, help="username for auto login")
    parser.add_argument("--password", type=str, help="password for auto login")
    parser.add_argument("--host", type=str, help="ip of server")
    parser.add_argument("--port", type=str, help="port of server")
    parser.add_argument("--debug", action="store_true", help="turn debugging on")

    args = parser.parse_args()

    clientObj = Client()
    clientObj.setDebug(False)
    if args.debug:
        clientObj.setDebug(True)
    clientObj.start(args)


main()
