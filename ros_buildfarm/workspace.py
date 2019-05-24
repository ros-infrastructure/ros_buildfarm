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


def call_build_tool(
    build_tool, rosdistro_name, workspace_root, cmake_args=None,
    force_cmake=False, cmake_clean_cache=False, install=False, make_args=None,
    args=None, parent_result_spaces=None, env=None, colcon_verb='build'
):
    # command to run
    assert build_tool in ('catkin_make_isolated', 'colcon')
    script_name = build_tool

    # use script from source space if available
    if build_tool == 'catkin_make_isolated':
        source_space = os.path.join(workspace_root, 'src')
        script_from_source = os.path.join(
            source_space, 'catkin', 'bin', script_name)
        if os.path.exists(script_from_source):
            script_name = script_from_source

    cmd = ['PYTHONIOENCODING=utf_8', 'PYTHONUNBUFFERED=1', script_name]

    if build_tool == 'colcon':
        cmd.append(colcon_verb)
        # match directory naming of catkin_make_isolated
        if colcon_verb in ('build', 'test'):
            cmd += ['--build-base', 'build_isolated']
            cmd += ['--install-base', 'install_isolated']
            cmd += ['--test-result-base', 'test_results']

        # output cohesion per package to avoid interleaving
        if colcon_verb == 'build':
            cmd += [
                '--event-handlers', 'console_cohesion+']
        # process packages sequentially assuming tests from different packages
        # can't be executed in parallel
        if colcon_verb == 'test':
            cmd += [
                '--event-handlers', 'console_direct+', '--executor sequential']

    if force_cmake:
        if build_tool == 'catkin_make_isolated':
            cmd.append('--force-cmake')
        elif build_tool == 'colcon':
            cmd.append('--cmake-force-configure')

    if cmake_clean_cache:
        if build_tool == 'catkin_make_isolated':
            # since cmi doesn't have such an option manually delete the caches
            print("Emulating '--cmake-clean-cache' in '%s'" % workspace_root)
            build_space = os.path.join(workspace_root, 'build_isolated')
            if os.path.isdir(build_space):
                for name in sorted(os.listdir(build_space)):
                    pkg_build_dir = os.path.join(build_space, name)
                    if not os.path.isdir(pkg_build_dir):
                        continue
                    cache_file = os.path.join(pkg_build_dir, 'CMakeCache.txt')
                    if os.path.exists(cache_file):
                        print("- rm '%s/CMakeCache.txt'" % name)
                        os.remove(cache_file)

        elif build_tool == 'colcon':
            cmd.append('--cmake-clean-cache')

    if install and build_tool == 'catkin_make_isolated':
        cmd.append('--install')

    if cmake_args:
        cmd += ['--cmake-args'] + cmake_args

    if make_args:
        if build_tool == 'catkin_make_isolated':
            cmd += ['--catkin-make-args'] + make_args
        elif build_tool == 'colcon':
            cmd += ['--cmake-target'] + make_args

    if args:
        cmd += args

    cmd = ' '.join(cmd)

    # prepend setup files if available
    if parent_result_spaces is None:
        parent_result_spaces = ['/opt/ros/%s' % rosdistro_name]
    for parent_result_space in reversed(parent_result_spaces):
        setup_file = os.path.join(parent_result_space, 'setup.sh')
        if os.path.exists(setup_file):
            cmd = '. %s && %s' % (setup_file, cmd)
            if os.path.isfile(
                os.path.join(parent_result_space, '.catkin')
            ):
                cmd = '_CATKIN_SETUP_DIR=%s %s' % (parent_result_space, cmd)
            if os.path.isfile(
                os.path.join(parent_result_space, '.colcon_install_layout')
            ):
                cmd = 'COLCON_CURRENT_PREFIX=%s %s' % (parent_result_space, cmd)

    print("Invoking '%s' in '%s'" % (cmd, workspace_root))
    return subprocess.call(
        cmd, cwd=workspace_root, shell=True, stderr=subprocess.STDOUT, env=env)
