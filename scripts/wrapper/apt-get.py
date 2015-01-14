#!/usr/bin/env python3

import subprocess
import sys
from time import sleep


def main(argv=sys.argv[1:]):
    max_tries = 10
    known_error_strings = ['E: Failed to fetch', 'Hash Sum mismatch']

    command = argv[0]
    if command == 'update':
        rc, _, _ = call_apt_get_repeatedly(
            argv, known_error_strings, max_tries)
        return rc
    elif command == 'update-and-install':
        return call_apt_get_update_and_install(
            argv[1:], known_error_strings, max_tries)
    else:
        assert "Command '%s' not implemented" % command


def call_apt_get_update_and_install(
        install_argv, known_error_strings, max_tries_per_command):
    update_tries = 0
    install_tries = 0
    command = 'update'
    while update_tries < max_tries_per_command and \
            install_tries < max_tries_per_command:
        if command == 'update':
            rc, _, update_tries = call_apt_get_repeatedly(
                [command], known_error_strings,
                max_tries_per_command, offset=update_tries)
            if rc != 0:
                # abort if update was unsuccessful even after retries
                break
            # move on to the install command if update was successful
            command = 'install'

        if command == 'install':
            known_error_strings_redo_update = [
                'Size mismatch', 'maybe run apt-get update']
            rc, known_error_conditions, install_tries = \
                call_apt_get_repeatedly(
                    [command] + install_argv,
                    known_error_strings + known_error_strings_redo_update,
                    install_tries + 1, offset=install_tries)
            if rc == 0 or not known_error_conditions:
                # abort if install was successful
                # or failed with an unknown errror condition
                break
            if set(known_error_conditions) & \
                    set(known_error_strings_redo_update):
                # restart with update command
                print(("'apt-get %s' failed and likely requires 'apt-get " +
                       "update' to run again") % command)
                command = 'update'
            # else try install again

    return rc


def call_apt_get_repeatedly(argv, known_error_strings, max_tries, offset=0):
    command = argv[0]
    for i in range(1 + offset, max_tries + 1):
        if i > 1:
            print("Reinvoke 'apt-get %s' (%d/%d) after sleeping %s seconds" %
                  (command, i, max_tries, i - 1))
            sleep(i)
        rc, known_error_conditions = call_apt_get(argv, known_error_strings)
        if rc == 0 or not known_error_conditions:
            break
        print('')
        print('Invocation failed due to: %s' %
              ', '.join(known_error_conditions))
        print('')
        # retry in case of failure with known error condition
    return rc, known_error_conditions, i


def call_apt_get(argv, known_error_strings):
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
                    if known_error_string not in known_error_conditions:
                        known_error_conditions.append(known_error_string)
        proc.wait()
        rc = proc.returncode
    return rc, known_error_conditions


if __name__ == '__main__':
    sys.exit(main())
