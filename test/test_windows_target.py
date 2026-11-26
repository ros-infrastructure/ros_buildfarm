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

import pytest
from ros_buildfarm.common import package_format_mapping
from ros_buildfarm.config.release_build_file import ReleaseBuildFile


def test_windows_package_format_is_conda():
    assert package_format_mapping['windows'] == 'conda'


def test_release_build_file_rejects_windows_target():
    data = {
        'type': 'release-build',
        'version': 2,
        'targets': {'windows': {'ltsc2025': {'amd64': {}}}},
        'target_repository': 'http://repo.example.com/windows',
        'upload_credential_id': 'upload-credential',
    }
    with pytest.raises(ValueError):
        ReleaseBuildFile('windows', data)
