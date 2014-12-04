#!/usr/bin/env python3

import re
import subprocess
import sys
from time import sleep


def main(argv=sys.argv[1:]):
    max_tries = 10
    for i in range(max_tries):
        if i > 0:
            print("Reinvoke 'docker build' (%d/%d) after sleeping %s seconds" %
                  (i, max_tries, i))
            sleep(i)
        rc, known_error_conditions = call_docker_build(argv)
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


def call_docker_build(argv):
    known_error_patterns = [
        '.* An error occured while creating the container.*',
        '.* Cannot find child for .*',
        '.* Error getting container .* no such file or directory.*',
        '.* Error mounting .* no such file or directory.*',
        '.* failed to create image .* no such file or directory.*',
        '.* failed to get image parent .* no such file or directory.*',
        '.* failed to get image parent .* Unknown device.*',
        '.* lstat .* input/output error.*',
        '.* No such container: .*',
        '.* No such id: .*',
        '.* open .* no such file or directory.*',
    ]
    known_error_conditions = []

    cmd = ['docker', 'build'] + argv
    with subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            line = line.decode()
            sys.stdout.write(line)
            for known_error_pattern in known_error_patterns:
                if re.match(known_error_pattern, line):
                    known_error_conditions.append(known_error_pattern)
        proc.wait()
        rc = proc.returncode
    return rc, known_error_conditions

if __name__ == '__main__':
    sys.exit(main())
