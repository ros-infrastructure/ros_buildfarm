# Copyright 2020 Open Source Robotics Foundation, Inc.
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

from .common import package_format_mapping
from .debian_repo import get_debian_repo_index
from .rpm_repo import get_ros_rpm_repo_index


def get_package_repo_data(repository_baseurl, targets, cache_dir):
    get_index_methods = {
        'deb': get_debian_repo_index,
        'rpm': get_ros_rpm_repo_index,
    }

    data = {}
    for target in targets:
        package_format = package_format_mapping[target.os_name]
        get_index_method = get_index_methods[package_format]
        index = get_index_method(
            repository_baseurl, target, cache_dir)
        data[target] = index
    return data
