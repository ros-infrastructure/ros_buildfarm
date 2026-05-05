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

import hashlib
import os

from ros_buildfarm.scripts.ci import create_workspace_archive


class ChunkEnforcingReader:

    def __init__(self, file_handle):
        """Wrap a file handle and reject unbounded reads."""
        self._file_handle = file_handle

    def __enter__(self):
        self._file_handle.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self._file_handle.__exit__(exc_type, exc_value, traceback)

    def __getattr__(self, name):
        return getattr(self._file_handle, name)

    def read(self, size=-1):
        if size == -1:
            raise AssertionError(
                'Checksum calculation must stream the archive contents')
        return self._file_handle.read(size)


def test_create_workspace_archive_streams_checksum(monkeypatch, tmpdir):
    install_dir = tmpdir.mkdir('install')
    install_dir.join('setup.sh').write('echo sourced workspace\n')
    output_dir = tmpdir.mkdir('output')

    archive_name = 'ros2-humble-linux-jammy-amd64-ci.tar.bz2'
    archive_path = os.path.join(str(output_dir), archive_name)
    checksum_path = archive_path.replace('.tar.bz2', '-CHECKSUM')
    original_open = open

    def guarded_open(path, mode='r', *args, **kwargs):
        file_handle = original_open(path, mode, *args, **kwargs)
        if path == archive_path and mode == 'rb':
            return ChunkEnforcingReader(file_handle)
        return file_handle

    monkeypatch.setattr(
        create_workspace_archive, 'open', guarded_open, raising=False)

    rc = create_workspace_archive.main([
        'humble',
        'jammy',
        'amd64',
        '--ros-version', '2',
        '--install-dir', str(install_dir),
        '--output-dir', str(output_dir),
    ])

    assert rc == 0

    with open(archive_path, 'rb') as f:
        archive_checksum = hashlib.sha256(f.read()).hexdigest()

    with open(checksum_path, 'r') as f:
        checksum_content = f.read()

    assert checksum_content == '%s *%s\n' % (archive_checksum, archive_name)
