# Copyright 2026 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess
import sys
from time import sleep


def main(argv=sys.argv[1:]):
    max_tries = 10
    known_error_strings = [
        'Failed to download',
        'Cannot download',
        'Error: Unable to find a match',
        'Curl error',
        'Timed out',
    ]

    command = argv[0]
    if command in ['update', 'makecache']:
        rc, _, _ = call_dnf_repeatedly(
            ['makecache'] + argv[1:], known_error_strings, max_tries)
        return rc
    elif command == 'update-install-clean':
        return call_dnf_update_install_clean(
            argv[1:], known_error_strings, max_tries)
    else:
        assert False, "Command '%s' not implemented" % command


def call_dnf_update_install_clean(
        install_argv, known_error_strings, max_tries):
    tries = 0
    command = 'update'
    while tries < max_tries:
        if command == 'update':
            rc, _, tries = call_dnf_repeatedly(
                ['makecache'], known_error_strings, max_tries - tries,
                offset=tries)
            if rc != 0:
                # abort if update was unsuccessful even after retries
                break
            # move on to the install command if update was successful
            command = 'install'

        if command == 'install':
            # any call is considered a try
            tries += 1
            known_error_strings_redo_update = [
                'Error: Unable to find a match',
                'No match for argument',
            ]
            rc, known_error_conditions = call_dnf(
                [command] + install_argv,
                known_error_strings + known_error_strings_redo_update)
            if not known_error_conditions:
                if rc != 0:
                    # abort if install was unsuccessful
                    break
                # move on to the clean command if install was successful
                command = 'clean'
                continue

            # known errors are always interpreted as a non-zero rc
            if rc == 0:
                rc = 1
            # check if update needs to be rerun
            if (
                set(known_error_conditions) &
                set(known_error_strings_redo_update)
            ):
                command = 'update'
                print("'dnf install' failed and likely requires " +
                      "'dnf makecache' to run again")
                # retry with update command
                continue

            print('')
            print('Invocation failed due to the following known error '
                  'conditions: ' + ', '.join(known_error_conditions))
            print('')
            if tries < max_tries:
                sleep_time = 5
                print("Reinvoke 'dnf install' after sleeping %s seconds" %
                      sleep_time)
                sleep(sleep_time)
                # retry install command

        if command == 'clean':
            rc, _ = call_dnf(['clean', 'all'], [])
            break

    return rc


def call_dnf_repeatedly(argv, known_error_strings, max_tries, offset=0):
    command = argv[0]
    for i in range(1, max_tries + 1):
        if i > 1:
            sleep_time = 5 + 2 * (i + offset)
            print("Reinvoke 'dnf %s' (%d/%d) after sleeping %s seconds" %
                  (command, i + offset, max_tries + offset, sleep_time))
            sleep(sleep_time)
        rc, known_error_conditions = call_dnf(argv, known_error_strings)
        if not known_error_conditions:
            # break the loop and return the reported rc
            break
        # known errors are always interpreted as a non-zero rc
        if rc == 0:
            rc = 1
        print('')
        print('Invocation failed due to the following known error conditions: '
              ', '.join(known_error_conditions))
        print('')
        # retry in case of failure with known error condition
    return rc, known_error_conditions, i + offset


def call_dnf(argv, known_error_strings):
    known_error_conditions = []

    cmd = ['dnf'] + argv
    print("Invoking '%s'" % ' '.join(cmd))
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = []
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        line = line.decode()
        lines.append(line)
        sys.stdout.write(line)
        for known_error_string in known_error_strings:
            if known_error_string in line:
                if known_error_string not in known_error_conditions:
                    known_error_conditions.append(known_error_string)
    proc.wait()
    rc = proc.returncode
    if rc and not known_error_conditions:
        print('Invocation failed without any known error condition, '
              'printing all lines to debug known error detection:')
        for index, line in enumerate(lines):
            print(' ', index + 1, "'%s'" % line.rstrip('\n\r'))
        print('None of the following known errors were detected:')
        for index, known_error_string in enumerate(known_error_strings):
            print(' ', index + 1, "'%s'" % known_error_string)
    return rc, known_error_conditions


if __name__ == '__main__':
    sys.exit(main())
