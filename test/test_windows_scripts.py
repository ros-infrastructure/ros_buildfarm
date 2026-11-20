# Copyright 2025 Open Source Robotics Foundation, Inc.
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
import subprocess

import pytest
from ros_buildfarm import workspace
from ros_buildfarm.common import get_user_id
from ros_buildfarm.scripts.devel import build_and_test


@pytest.fixture
def workspace_root(tmp_path):
    (tmp_path / 'src').mkdir()
    return str(tmp_path)


@pytest.fixture
def recorded_calls(monkeypatch):
    calls = []

    def fake_call(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return 0

    monkeypatch.setattr(subprocess, 'call', fake_call)
    return calls


def test_get_user_id_windows(monkeypatch):
    monkeypatch.setattr(os, 'name', 'nt')
    assert get_user_id() is None


def test_get_user_id_posix(monkeypatch):
    monkeypatch.setattr(os, 'name', 'posix')
    monkeypatch.setattr(os, 'getuid', lambda: 1000, raising=False)
    assert get_user_id() == 1000


def test_get_user_id_posix_rejects_root(monkeypatch):
    monkeypatch.setattr(os, 'name', 'posix')
    monkeypatch.setattr(os, 'getuid', lambda: 0, raising=False)
    with pytest.raises(AssertionError):
        get_user_id()


def test_call_build_tool_windows(monkeypatch, workspace_root, recorded_calls):
    monkeypatch.setattr(os, 'name', 'nt')
    caller_env = {'FOO': 'bar'}
    workspace.call_build_tool(
        'colcon', 'rolling', workspace_root, env=caller_env)

    cmd, kwargs = recorded_calls[0]
    assert cmd.startswith('colcon ')
    assert kwargs['env']['PYTHONIOENCODING'] == 'utf_8'
    assert kwargs['env']['PYTHONUNBUFFERED'] == '1'
    assert kwargs['env']['FOO'] == 'bar'
    # the environment of the caller is not modified
    assert caller_env == {'FOO': 'bar'}


def test_call_build_tool_windows_without_env(
    monkeypatch, workspace_root, recorded_calls
):
    monkeypatch.setattr(os, 'name', 'nt')
    monkeypatch.setenv('FOO', 'bar')
    workspace.call_build_tool('colcon', 'rolling', workspace_root)

    env = recorded_calls[0][1]['env']
    assert env['FOO'] == 'bar'
    assert env['PYTHONIOENCODING'] == 'utf_8'


def test_call_build_tool_windows_rejects_parent_result_spaces(
    monkeypatch, workspace_root, recorded_calls
):
    monkeypatch.setattr(os, 'name', 'nt')
    with pytest.raises(AssertionError):
        workspace.call_build_tool(
            'colcon', 'rolling', workspace_root,
            parent_result_spaces=['/some/underlay'])
    assert not recorded_calls


def test_call_build_tool_posix(monkeypatch, tmp_path, workspace_root, recorded_calls):
    monkeypatch.setattr(os, 'name', 'posix')
    underlay = tmp_path / 'underlay'
    underlay.mkdir()
    (underlay / 'setup.sh').write_text('')
    caller_env = {'FOO': 'bar'}
    workspace.call_build_tool(
        'colcon', 'rolling', workspace_root,
        parent_result_spaces=[str(underlay)], env=caller_env)

    cmd, kwargs = recorded_calls[0]
    # the variables are a prefix of the command, the setup file is sourced
    assert cmd.startswith(
        '. %s && PYTHONIOENCODING=utf_8 PYTHONUNBUFFERED=1 colcon ' %
        os.path.join(str(underlay), 'setup.sh'))
    assert kwargs['env'] == {'FOO': 'bar'}


@pytest.mark.parametrize('build_tool', ['colcon', 'catkin_make_isolated'])
def test_build_and_test_parent_result_spaces(
    monkeypatch, workspace_root, build_tool
):
    results = {}

    def fake_call_build_tool(*args, **kwargs):
        results['parent_result_spaces'] = kwargs['parent_result_spaces']
        return 0

    monkeypatch.setattr(build_and_test, 'call_build_tool', fake_call_build_tool)
    argv = [
        '--rosdistro-name', 'rolling', '--ros-version', '2',
        '--build-tool', build_tool, '--workspace-root', workspace_root]

    # the last call is the one that runs the tests
    monkeypatch.setattr(os, 'name', 'nt')
    assert build_and_test.main(argv) == 0
    assert results['parent_result_spaces'] is None

    monkeypatch.setattr(os, 'name', 'posix')
    assert build_and_test.main(argv) == 0
    expected = ['/opt/ros/rolling']
    if build_tool == 'catkin_make_isolated':
        expected.append(os.path.join(workspace_root, 'devel_isolated'))
    assert results['parent_result_spaces'] == expected
