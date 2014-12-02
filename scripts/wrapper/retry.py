#!/usr/bin/env python3

import argparse
import subprocess
import sys
from time import sleep


def main():
    parser = argparse.ArgumentParser(description='Run a command multiple times')
    parser.add_argument('-r', '--retries', dest='retries', type=int, default=3,
                        help='How many times to retry')
    parser.add_argument('-d', '--delay', dest='delay', type=float, default=3.0,
                        help='How many seconds to wait for retries')
    parser.add_argument('cmd', metavar='command', nargs='+',
                        help='The command to run')

    args = parser.parse_args()

    for i in range(args.retries):
        if i > 0:
            print("Reinvoke '%s' (%d/%d) after sleeping %s seconds" %
                  (args.cmd, i, args.retries, args.delay))
            sleep(args.delay)
        rc = call_cmd(args.cmd)
        if rc == 0:
            break
        # retry in case of failure with known error condition
    return rc


def call_cmd(cmd):
    with subprocess.Popen(cmd) as proc:
        proc.wait()
        rc = proc.returncode
    return rc

if __name__ == '__main__':
    sys.exit(main())
