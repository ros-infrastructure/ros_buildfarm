#!/usr/bin/env python3

# Copyright 2015-2016 Open Source Robotics Foundation, Inc.
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
    assert len(argv) < 2
    dockerfile = argv[0] if len(argv) == 1 else 'Dockerfile'
    sys.stdout.write("Get base image name from Dockerfile '%s': " % dockerfile)
    base_image = get_base_image_from_dockerfile(dockerfile)
    print(base_image)

    known_error_strings = [
        'Error pulling image',
        'Server error: Status 502 while fetching image layer',
    ]
    max_tries = 10
    rc, _ = call_docker_pull_repeatedly(base_image, known_error_strings, max_tries)
    return rc


def get_base_image_from_dockerfile(dockerfile):
    with open(dockerfile, 'r') as h:
        content = h.read()
    lines = content.splitlines()
    from_prefix = 'FROM '
    for line in lines:
        if line.startswith(from_prefix):
            return line[len(from_prefix):]
    assert False, \
        "Could not find a line starting with '%s' in the Dockerfile '%s'" % \
        (from_prefix, dockerfile)


def call_docker_pull_repeatedly(base_image, known_error_strings, max_tries):
    for i in range(1, max_tries + 1):
        if i > 1:
            sleep_time = 5 + 2 * i
            print("Reinvoke 'docker pull' (%d/%d) after sleeping %s seconds" %
                  (i, max_tries, sleep_time))
            sleep(sleep_time)
        rc, known_error_conditions = call_docker_pull(base_image, known_error_strings)
        if rc == 0 or not known_error_conditions:
            break
        print('')
        print('Invocation failed due to the following known error conditions: '
              ', '.join(known_error_conditions))
        print('')
        # retry in case of failure with known error condition
    return rc, known_error_conditions


def call_docker_pull(base_image, known_error_strings):
    known_error_conditions = []

    cmd = ['docker', 'pull', base_image]
    print('Check docker base image for updates: %s' % ' '.join(cmd))
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
