# Copyright 2014-2018 Open Source Robotics Foundation, Inc.
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

from ros_buildfarm.workspace import call_build_tool
# keep symbols for backward compatibility
from ros_buildfarm.workspace import clean_workspace  # noqa: F401
from ros_buildfarm.workspace import ensure_workspace_exists  # noqa: F401


def call_catkin_make_isolated(
    rosdistro_name, workspace_root, args, parent_result_spaces=None, env=None
):
    args = list(args)
    kwargs = {
        'parent_result_spaces': parent_result_spaces,
        'env': env,
    }
    if '--force-cmake' in args:
        kwargs['force_cmake'] = True
        args.remove('--force-cmake')
    if '--install' in args:
        kwargs['install'] = True
        args.remove('--install')
    if '--catkin-make-args' in args:
        kwargs['make_args'] = args[args.index('--catkin-make-args') + 1:]
        args = args[:args.index('--catkin-make-args')]
    if '--cmake-args' in args:
        kwargs['cmake_args'] = args[args.index('--cmake-args') + 1:]
        args = args[:args.index('--cmake-args')]
    assert not args, \
        'Not all arguments have been handled by the simple heuristic'

    return call_build_tool(
        'catkin_make_isolated', rosdistro_name, workspace_root, **kwargs)
