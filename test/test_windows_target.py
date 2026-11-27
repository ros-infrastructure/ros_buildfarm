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
from ros_buildfarm.common import get_os_template_suffix
from ros_buildfarm.common import package_format_mapping
from ros_buildfarm.config.ci_build_file import CIBuildFile
from ros_buildfarm.config.doc_build_file import DocBuildFile
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


@pytest.mark.parametrize('build_file_class,data', [
    (CIBuildFile, {'type': 'ci-build', 'version': 1}),
    (DocBuildFile, {
        'type': 'doc-build',
        'version': 2,
        'upload_credential_id': 'upload-credential',
    }),
])
def test_ci_and_doc_build_files_ignore_windows_target(build_file_class, data):
    data = dict(data, targets={
        'ubuntu': {'noble': {'amd64': {}}},
        'windows': {'ltsc2025': {'amd64': {}}},
    })
    build_file = build_file_class('default', data)
    assert list(build_file.targets) == ['ubuntu']
    assert [t.os_name for t in build_file.unsupported_targets] == ['windows']


def test_source_build_file_keeps_windows_target():
    data = {
        'type': 'source-build',
        'version': 2,
        'build_tool': 'colcon',
        'targets': {'windows': {'ltsc2025': {'amd64': {}}}},
    }
    build_file = SourceBuildFile('windows', data)
    assert build_file.targets == {'windows': {'ltsc2025': {'amd64': {}}}}
    assert build_file.unsupported_targets == []


def test_devel_job_accepts_windows_target():
    pytest.importorskip('catkin_pkg')
    pytest.importorskip('rosdistro')
    from ros_buildfarm.devel_job import configure_devel_job
    from rosdistro.source_repository_specification import \
        SourceRepositorySpecification

    build_file = SourceBuildFile('windows', {
        'type': 'source-build',
        'version': 2,
        'build_tool': 'colcon',
        'targets': {'windows': {'ltsc2025': {'amd64': {}}}},
    })
    source_repository = SourceRepositorySpecification('ament_package', {
        'type': 'git',
        'url': 'https://github.com/ament/ament_package.git',
        'version': 'rolling',
    })
    job_name, _ = configure_devel_job(
        None, 'rolling', 'windows', 'ament_package',
        'windows', 'ltsc2025', 'amd64',
        config=SimpleNamespace(
            rosdistro_index_url='http://example.com/index.yaml',
            git_ssh_credential_id=None),
        build_file=build_file,
        index=SimpleNamespace(
            distributions={'rolling': {'distribution_type': 'ros2'}}),
        dist_file=SimpleNamespace(repositories={
            'ament_package': SimpleNamespace(
                source_repository=source_repository),
        }),
        jenkins=False, views=False)
    assert job_name == 'Rdev_windows__ament_package__windows_ltsc2025_amd64'


def test_os_template_suffix():
    assert get_os_template_suffix('windows') == '_windows'
    assert get_os_template_suffix('ubuntu') == ''
