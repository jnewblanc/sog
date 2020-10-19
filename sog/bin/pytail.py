import colorama
import os
import platform
import re
import subprocess
import sys
import time


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


def get_next_entry(filehandle):
    """ generator function that returns the next log entry, broken up into
        it's basic parts: date, status, content """
    line_regex = re.compile("([^ ]+ [^ ]+) ([A-Z]+) (.*)\n$")

    while True:
        linedata = filehandle.stdout.readline().decode("utf-8")
        if line_regex.search(linedata):
            yield (line_regex.match(linedata).groups())
        time.sleep(0.1)


def printColor(datestr, status, info):
    """ Display colorized output based on the status """
    # Create a dict to map status to a colorama color
    colormap = {
        'DEBUG': colorama.Fore.CYAN,
        'WARNING': colorama.Fore.YELLOW,
        'ERROR': colorama.Fore.RED
    }

    txtstr = '{} {} {}'.format(datestr, status, info)
    colorstr = '{}' + txtstr + colorama.Fore.RESET

    print(colorstr.format(colormap.get(status, '')))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Show usage if command line arg isn't present
        usage('', 0)
    logfile = get_logfilename(sys.argv[1])

    # Determin tail command based on playform
    if 'Windows' in platform.system():
        powershell = (os.getenv('SystemRoot') +
                      '/system32/WindowsPowerShell/v1.0/powershell.exe')
        tailcmd = '{} Get-Content {} -Tail 100 -Wait'.format(powershell, logfile)
    else:
        tailcmd = 'tail -f {}'.format(logfile)

    # Open filehandle to get output of tail command
    cmdhandle = subprocess.Popen(tailcmd.split(),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

    # Loop over tail output, as returned from generator
    colorama.init()

    for datestr, status, info in get_next_entry(cmdhandle):
        printColor(datestr, status, info)
