#!/usr/bin/env python
""" SoG server - Entry point """
# import selectors
from signal import signal, SIGINT, SIGTERM

from common.general import sig_handler
from common.serverLib import server

# -------------
if __name__ == "__main__":
    # Tie the signals to the sighandlers
    signal(SIGINT, sig_handler)  # run on SIGINT
    signal(SIGTERM, sig_handler)  # run on SIGITERM
    print("Running. Press CTRL-C to exit.  (might wait for a connection)")

    # Run the server
    server()
