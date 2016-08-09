#!/usr/bin/env python3

import subprocess
import sys
from time import sleep


def main(argv=sys.argv[1:]):
    max_tries = 10
    known_error_strings = [
        'Connection timed out',
    ]

    command = argv[0]
    if command == 'clone':
        rc, _, _ = call_git_repeatedly(
            argv, known_error_strings, max_tries)
        return rc
    else:
        assert "Command '%s' not implemented" % command


def call_git_repeatedly(argv, known_error_strings, max_tries):
    command = argv[0]
    for i in range(1, max_tries + 1):
        if i > 1:
            sleep_time = 5 + 2 * i
            print("Reinvoke 'git %s' (%d/%d) after sleeping %s seconds" %
                  (command, i, max_tries, sleep_time))
            sleep(sleep_time)
        rc, known_error_conditions = call_git(argv, known_error_strings)
        if rc == 0 or not known_error_conditions:
            break
        print('')
        print('Invocation failed due to the following known error conditions: '
              ', '.join(known_error_conditions))
        print('')
        # retry in case of failure with known error condition
    return rc, known_error_conditions, i


def call_git(argv, known_error_strings):
    known_error_conditions = []

    cmd = ['git'] + argv
    print("Invoking '%s'" % ' '.join(cmd))
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        line = line.decode()
        sys.stdout.write(line)
        for known_error_string in known_error_strings:
            if known_error_string in line:
                if known_error_string not in known_error_conditions:
                    known_error_conditions.append(known_error_string)
    proc.wait()
    rc = proc.returncode
    return rc, known_error_conditions


if __name__ == '__main__':
    sys.exit(main())
