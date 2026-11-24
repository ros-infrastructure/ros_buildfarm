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

import platform

import pytest
from ros_buildfarm.common import get_system_architecture


@pytest.mark.parametrize('machine,expected', [
    ('x86_64', 'amd64'),
    ('AMD64', 'amd64'),
    ('i386', 'i386'),
    ('aarch64', 'armv8'),
])
def test_get_system_architecture(monkeypatch, machine, expected):
    monkeypatch.setattr(platform, 'machine', lambda: machine)
    assert get_system_architecture() == expected


def test_get_system_architecture_unknown(monkeypatch):
    monkeypatch.setattr(platform, 'machine', lambda: 'riscv64')
    with pytest.raises(RuntimeError):
        get_system_architecture()
