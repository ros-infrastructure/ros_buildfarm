#!/usr/bin/env python3

import subprocess
import sys
from time import sleep


def main(argv=sys.argv[1:]):
    max_tries = 10
    for i in range(max_tries):
        if i > 0:
            print("Reinvoke 'apt-get' (%d/%d) after sleeping %s seconds" %
                  (i, max_tries, i))
            sleep(i)
        rc, known_error_conditions = call_apt_get_update(argv)
        if rc == 0:
            break
        if not known_error_conditions:
            break
        # retry in case of failure with known error condition
        print('', file=sys.stderr)
        print('Invocation failed due to: %s' %
              ', '.join(known_error_conditions), file=sys.stderr)
        print('', file=sys.stderr)
    return rc


def call_apt_get_update(argv):
    known_error_strings = ['Hash Sum mismatch']
    known_error_conditions = []

    cmd = ['apt-get'] + argv
    with subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            line = line.decode()
            sys.stdout.write(line)
            for known_error_string in known_error_strings:
                if known_error_string in line:
                    known_error_conditions.append(known_error_string)
        proc.wait()
        rc = proc.returncode
    return rc, known_error_conditions

if __name__ == '__main__':
    sys.exit(main())
