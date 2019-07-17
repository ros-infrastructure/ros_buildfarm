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


def import_repositories(source_space, repository_file, target_branch):
    cmd = ['vcs', 'import', source_space, '--force', '--retry', '5', '--input', repository_file]
    subprocess.check_call(cmd)

    if target_branch:
        cmd = ['vcs', 'custom', source_space, '--git', '--args', 'checkout', '-b', '__ci_default']
        subprocess.check_call(cmd)

        cmd = ['vcs', 'custom', source_space, '--args', 'checkout',
               '-b', target_branch, '--track', 'origin/%s' % target_branch]
        subprocess.call(cmd)

        cmd = ['vcs', 'custom', source_space, '--git', '--args', 'merge', '__ci_default']
        subprocess.check_call(cmd)


def export_repositories(source_space, check=True):
    cmd = ['vcs', 'export', '--exact', source_space]
    subprocess.run(cmd, check=check)
