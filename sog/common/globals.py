""" Set up global paths """

#########
# Paths #
#########
import os

FILEDIR = os.path.dirname(os.path.abspath(__file__))
ROOTDIR = os.path.abspath(os.path.join(FILEDIR, ".."))

DATADIR = os.getenv('SOG_SERVER_DATADIR', os.path.join(ROOTDIR, ".data"))
LOGDIR = os.getenv('SOG_SERVER_LOGDIR', os.path.join(ROOTDIR, ".logs"))

# CONFIGFILE = os.path.join(ROOT_DIR, 'configuration.conf')

###########
# Network #
###########
HOST = os.getenv('SOG_SERVER_HOST', "127.0.0.1")  # hostname or IP address
PORT = int(os.getenv('SOG_SERVER_PORT', '8888'))  # The port used by the server
BYTES_TO_TRANSFER = 2048

NOOP_STR = "=-o-= NOOP =-o-="
TERM_STR = "=-o-= TERM =-o-="
STOP_STR = "=-o-= STOP =-o-="


###################
# Runtime globals #
###################

# These are shared vars that are populated at runtime
connections = []
totalConnections = 0


#################
# game settings #
#################

maxCreaturesInRoom = 6
