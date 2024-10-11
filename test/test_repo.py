# Copyright 2024 Open Source Robotics Foundation, Inc.
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

import pytest
from ros_buildfarm.common import PlatformPackageDescriptor
from ros_buildfarm.common import Target
from ros_buildfarm.package_repo import get_package_repo_data

mock_deb_index_path = os.path.join(os.path.dirname(__file__), 'mock_deb_index')
mock_rpm_index_path = os.path.join(os.path.dirname(__file__), 'mock_rpm_index')


@pytest.mark.parametrize('target,mock_index_path', [
    (Target('rhel', '9', 'x86_64'), mock_rpm_index_path),
    (Target('ubuntu', 'noble', 'amd64'), mock_deb_index_path),
])
def test_get_repo_data(tmpdir, target, mock_index_path):
    mock_index_url = 'file://' + mock_index_path
    data = get_package_repo_data(mock_index_url, (target,), str(tmpdir))

    assert target in data
    target_data = data[target]

    expected = PlatformPackageDescriptor('1.2.3-1', 'pkg-with-prov')
    assert expected == target_data.get('pkg-with-prov')
    assert expected == target_data.get('pkg-with-prov-a')
    assert expected == target_data.get('pkg-with-prov-b')

    expected = PlatformPackageDescriptor(None, 'pkg-with-prov')
    assert expected == target_data.get('pkg-with-prov-no-ver')
