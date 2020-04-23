import logging
from pathlib import Path
import sys
from common.paths import LOGDIR


class InitTestLog():
    def __init__(self):
        logpath = Path(LOGDIR)
        logpath.mkdir(parents=True, exist_ok=True)
        FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
        logging.basicConfig(filename=(LOGDIR + '/test.log'),
                            level=logging.DEBUG,
                            format=FORMAT, datefmt='%m/%d/%y %H:%M:%S')
        logging.info("-------------------------------------------------------")
        logging.info("Test Start - " + sys.argv[0])
