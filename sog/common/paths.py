''' Set up global paths '''

import os

FILEDIR = os.path.dirname(os.path.abspath(__file__))
ROOTDIR = os.path.abspath(os.path.join(FILEDIR, ".."))

DATADIR = os.path.join(ROOTDIR, ".data")
LOGDIR = os.path.join(ROOTDIR, ".logs")
# CONFIGFILE = os.path.join(ROOT_DIR, 'configuration.conf')
