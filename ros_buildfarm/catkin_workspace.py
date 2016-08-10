# Copyright 2014-2016 Open Source Robotics Foundation, Inc.
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

import os
import shutil
import subprocess


def ensure_workspace_exists(workspace_root):
    # ensure that workspace exists
    assert os.path.exists(workspace_root), \
        "Workspace root '%s' does not exist" % workspace_root
    source_space = os.path.join(workspace_root, 'src')
    assert os.path.exists(source_space), \
        "Source space '%s' does not exist" % source_space


def clean_workspace(workspace_root):
    # clean up build, devel and install spaces
    build_space = os.path.join(workspace_root, 'build_isolated')
    if os.path.exists(build_space):
        shutil.rmtree(build_space)
    devel_space = os.path.join(workspace_root, 'devel_isolated')
    if os.path.exists(devel_space):
        shutil.rmtree(devel_space)
    install_space = os.path.join(workspace_root, 'install_isolated')
    if os.path.exists(install_space):
        shutil.rmtree(install_space)
    test_results_dir = os.path.join(workspace_root, 'test_results')
    if os.path.exists(test_results_dir):
        shutil.rmtree(test_results_dir)


def call_catkin_make_isolated(
        rosdistro_name, workspace_root, args, parent_result_spaces=None):
    # command to run
    script_name = 'catkin_make_isolated'
    # use script from source space if available
    source_space = os.path.join(workspace_root, 'src')
    script_from_source = os.path.join(
        source_space, 'catkin', 'bin', script_name)
    if os.path.exists(script_from_source):
        script_name = script_from_source
    cmd = ' '.join(
        ['PYTHONIOENCODING=utf_8', 'PYTHONUNBUFFERED=1', script_name] + args)

    # prepend setup files if available
    if parent_result_spaces is None:
        parent_result_spaces = ['/opt/ros/%s' % rosdistro_name]
    for parent_result_space in reversed(parent_result_spaces):
        setup_file = os.path.join(parent_result_space, 'setup.sh')
        if os.path.exists(setup_file):
            cmd = '. %s && %s' % (setup_file, cmd)

    print("Invoking '%s' in '%s'" % (cmd, workspace_root))
    return subprocess.call(cmd, cwd=workspace_root, shell=True)
