# Copyright 2019 Open Source Robotics Foundation, Inc.
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


def locate_packages(
    source_space, packages_select=None, packages_up_to=None,
    packages_above_depth=None, extra_args=None
):
    cmd = ['colcon', 'list', '--base-paths', source_space]
    if packages_select:
        cmd.append('--packages-select')
        cmd.extend(packages_select)
    if packages_up_to:
        cmd.append('--packages-up-to')
        cmd.extend(packages_up_to)
    if packages_above_depth:
        cmd.append('--packages-above-depth')
        cmd.extend(packages_above_depth)
    if extra_args:
        cmd.extend(extra_args)

    output = subprocess.check_output(cmd).decode()

    packages = {}
    for line in output.splitlines():
        # Format is: NAME PATH (TYPE)
        name_path = line.rsplit(None, 1)[0]
        name, path = name_path.split(None, 1)
        packages[name] = path

    return packages
