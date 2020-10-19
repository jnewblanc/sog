""" parse logs to get elapsed time of client sessions """

import datetime
import os
import re
import sys


def usage(msg='', error_code=1):
    """ Output the usage + any other message provided and then exit """
    if msg != '':
        print(msg)
    print("Usage: {} <logfile>".format(__file__))
    exit(error_code)


def get_logfilename(filename=""):
    """ return full path to a logfile and verify existence
        Typically we'd pass in the command line arg (ie argv[1]) """

    # If the given filename exists, return it.  No need to do any other processing
    if os.path.isfile(filename):
        return(filename)

    # figure out some paths and defaults
    scriptdir = os.path.dirname(os.path.realpath(__file__))
    default_logpath = os.path.abspath(scriptdir + '/../logs')
    default_filename = os.path.abspath(default_logpath + '/server.log')

    # use default filename if no filename is given
    if filename == '':
        filename = default_filename

    # if filename doesn't exist, try prepending the logdir
    if not os.path.isfile(filename):
        old_filename = filename
        if '/' not in filename:
            filename = os.path.abspath(default_logpath + '/' + filename)

    # return filename if it exists, otherwise thrown an error and exit
    if os.path.isfile(filename):
        return(filename)
    else:
        usage("ERROR: Can not find logfile at {} or {}".format(
            old_filename, filename), 1)


def sub_date(datestr1, datestr2):
    """ Return a date string which represents the difference between days """
    datefmt = "%m/%d/%y %H:%M:%S"

    try:
        datedelta = (datetime.datetime.strptime(datestr2, datefmt) -
                     datetime.datetime.strptime(datestr1, datefmt))
        datestr = str(datedelta)
    except (TypeError, ValueError):
        datestr = "unknown"

    return datestr


def get_id(ip='unknown', id='unknown'):
    """ returns a properly formatted id """
    return("{}-{}".format(ip, id))


def initialize_session_obj():
    """ creates a session object, initializes it, and returns it """
    session = {}
    session["startdate"] = '00/00/00 00:00:00'
    session["enddate"] = '00/00/00 00:00:00'
    session["account"] = 'unknown'

    return session


def read_log(infile):
    r""" Returns a dict containing session info that was obtained from reading
        a logfile.  Resulting object is as follows:
            # sessions[id] = {startdate, enddate, account}

        Example log lines

        04/30/20 18:51:29 INFO Server Exit - C:\Users\Jason\work\sog\sog\server.py
        04/30/20 18:55:34 INFO Server Start - C:\Users\Jason\work\sog\sog\server.py
        04/30/20 18:55:34 INFO Thread started - async worker
        04/30/20 18:55:37 INFO CT0('127.0.0.1', 10399) Client connection established
        04/30/20 18:55:39 INFO CT0('127.0.0.1', 10399) Account login successful - com@gadgetshead.com   # noqa: E501
        05/04/20 03:00:39 INFO CT0('127.0.0.1', 6496) Client connection terminated
        05/04/20 03:00:39 DEBUG CT0('127.0.0.1', 6496) No clientdata returned
        05/04/20 03:00:39 WARNING CT0('127.0.0.1', 6496) Authentication failed
        05/03/20 00:59:08 INFO CT0('127.0.0.1', 27228) Logout com@gadgetshead.com
        """

    # precompiled rexex
    clientstart_regex = re.compile("([^ ]+ [^ ]+) INFO CT[0-9]+\('([^']+)', ([0-9]+)\) Client connection established")  # noqa: E501, W605
    clientend_regex = re.compile("([^ ]+ [^ ]+) INFO CT[0-9]+\('([^']+)', ([0-9]+)\) Client connection terminated")     # noqa: E501, W605
    accountstart_regex = re.compile("([^ ]+ [^ ]+) INFO CT[0-9]+\('([^']+)', ([0-9]+)\) Account login successful - (.*)$")  # noqa: E501, W605
    # accountend_regex = re.compile(r"INFO CT.*Logout")
    # authfailed_regex = re.compile(r"INFO CT.*Authentication failed")

    sessions = {}

    with open(logfile, 'r') as infile:
        for line in infile:
            if clientstart_regex.search(line):
                startdate, oneip, oneid = clientstart_regex.match(line).groups()
                id = get_id(oneip, oneid)
                sessions[id] = initialize_session_obj()
                sessions[id]["startdate"] = startdate
            elif clientend_regex.search(line):
                enddate, oneip, oneid = clientend_regex.match(line).groups()
                id = get_id(oneip, oneid)
                sessions[id]["enddate"] = enddate
            elif accountstart_regex.search(line):
                onedate, oneip, oneid, acct = accountstart_regex.match(line).groups()
                id = get_id(oneip, oneid)
                sessions[id]["account"] = acct
    return sessions


def show_output(sessions={}):
    """ display output based on the sessions object """
    for id, session in sessions.items():
        startdate = session['startdate']
        enddate = session['enddate']
        elapsed = sub_date(startdate, enddate)

        outstr = "{} - S:{} - E:{} - A:{} - T:{}"
        print(outstr.format(id, startdate, enddate, session['account'], elapsed))


#########################
if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Show usage if command line arg isn't present
        usage('', 0)
    logfile = get_logfilename(sys.argv[1])
    sessions = read_log(logfile)
    show_output(sessions)
