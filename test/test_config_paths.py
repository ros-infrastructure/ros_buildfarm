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

from pathlib import Path

from ros_buildfarm.config import load_yaml


def test_load_yaml_relative_to_cwd(tmp_path, monkeypatch):
    # The directory name contains a space on purpose.
    cwd = tmp_path / 'dir with space'
    (cwd / 'cfg' / 'sub').mkdir(parents=True)
    (cwd / 'cfg' / 'index.yaml').write_text(
        'a: 1\n'
        'included: !include sub/included.yaml\n'
        'link: !relative_url sub/included.yaml\n')
    (cwd / 'cfg' / 'sub' / 'included.yaml').write_text('b: 2\n')
    monkeypatch.chdir(str(cwd))

    data = load_yaml('cfg/index.yaml')

    assert data['a'] == 1
    assert data['included'] == {'b': 2}
    assert data['link'] == (Path.cwd() / 'cfg' / 'sub' / 'included.yaml').as_uri()
