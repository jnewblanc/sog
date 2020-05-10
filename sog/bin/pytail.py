import colorama
import sys
import os

logfile = os.path.abspath("../.logs/" + sys.argv[1])

if not os.path.isfile(logfile):
    print('Error: logfile ' + logfile + "doesn't exist")
    sys.exit(1)

# Implement log tailer here.
# Need tried a few different packages.  Couldn't decide on one
# Would be nice to colorize with colorama
