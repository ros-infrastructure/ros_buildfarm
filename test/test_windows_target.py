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

from types import SimpleNamespace

import pytest
from ros_buildfarm.common import JobValidationError
from ros_buildfarm.common import package_format_mapping
from ros_buildfarm.config.release_build_file import ReleaseBuildFile
from ros_buildfarm.config.source_build_file import SourceBuildFile


def test_windows_package_format_is_conda():
    assert package_format_mapping['windows'] == 'conda'


def test_build_file_ignores_windows_target():
    data = {
        'type': 'release-build',
        'version': 2,
        'targets': {
            'ubuntu': {'noble': {'amd64': {}}},
            'windows': {'ltsc2025': {'amd64': {}}},
        },
        'target_repository': 'http://repo.example.com/ubuntu',
        'upload_credential_id': 'upload-credential',
    }
    build_file = ReleaseBuildFile('default', data)
    assert list(build_file.targets) == ['ubuntu']
    assert [t.os_name for t in build_file.unsupported_targets] == ['windows']


def test_windows_only_build_file_has_no_targets():
    data = {
        'type': 'source-build',
        'version': 2,
        'build_tool': 'colcon',
        'targets': {'windows': {'ltsc2025': {'amd64': {}}}},
    }
    build_file = SourceBuildFile('windows', data)
    assert build_file.targets == {}


def test_devel_job_rejects_windows_target():
    pytest.importorskip('catkin_pkg')
    pytest.importorskip('rosdistro')
    from ros_buildfarm.devel_job import configure_devel_job

    with pytest.raises(JobValidationError):
        configure_devel_job(
            None, 'rolling', 'windows', None, 'windows', 'ltsc2025', 'amd64',
            config=object(), build_file=SimpleNamespace(targets={}),
            index=object(), dist_file=SimpleNamespace(repositories={}),
            jenkins=False, views=False)
