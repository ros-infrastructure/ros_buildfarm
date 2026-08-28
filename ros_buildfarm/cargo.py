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

import json
import os
import subprocess


def is_vendoring_requested(pkg):
    EXPORT_TAG = 'cargo_vendor_crates'
    VALUES = {'True': True, 'true': True, 'False': False, 'false': False}

    # vendoring is opt-in, an unrecognized value is a typo rather than a 'no'
    requested = False
    for export in pkg.exports:
        if export.tagname != EXPORT_TAG:
            continue
        value = export.content.strip()
        if value not in VALUES:
            raise RuntimeError(
                "Invalid '<%s>' value '%s' in the package manifest, expected "
                'one of: %s' % (EXPORT_TAG, value, ', '.join(sorted(VALUES))))
        requested = VALUES[value]
    return requested


def _get_non_crates_io_dependencies(sources_dir):
    CRATES_IO_SOURCE = 'registry+https://github.com/rust-lang/crates.io-index'

    # '--no-deps' restricts this to the manifests in the workspace and skips
    # resolving the dependency graph, so it needs neither a lock file nor
    # network access. The manifests are enough to cover the whole graph:
    # crates.io refuses to publish a crate depending on a git repository or on
    # another registry, so no crates.io crate can pull one in transitively
    cmd = [
        'cargo', 'metadata', '--no-deps', '--offline', '--format-version', '1']
    print("Invoking '%s' in '%s'" % (' '.join(cmd), sources_dir))
    metadata = json.loads(
        subprocess.check_output(cmd, cwd=sources_dir).decode())

    dependencies = []
    for package in metadata['packages']:
        for dependency in package['dependencies']:
            # a path dependency within the workspace carries no source
            if dependency['source'] in (None, CRATES_IO_SOURCE):
                continue
            dependencies.append((dependency['name'], dependency['source']))
    return dependencies


def vendor_cargo_crates(sources_dir, vendor_dir):
    manifest_path = os.path.join(sources_dir, 'Cargo.toml')
    if not os.path.exists(manifest_path):
        print("No 'Cargo.toml' in '%s', skipping cargo crate vendoring" %
              sources_dir)
        return

    # crates from git repositories or from registries other than crates.io do
    # not go through a crates.io release and can change or disappear without
    # notice, refuse to ship them in the source package. Checked before
    # vendoring so that none of them is fetched in the first place
    external_deps = _get_non_crates_io_dependencies(sources_dir)
    if external_deps:
        raise RuntimeError(
            'Cannot vendor cargo crates: crates.io is the only permitted '
            "crate source, but '%s' requires: %s" % (manifest_path, ', '.join(
                "'%s' from '%s'" % d for d in external_deps)))

    # 'vendor_dir' is the path components the caller wants the crates under
    cmd = ['cargo', 'vendor']

    # TODO(blast545): whether a committed lock file should be (or not) required
    # is unclear, see 'Cargo.lock policy' in the design notes. Until then
    # a package without one is vendored against a freshly resolved dependency
    # set rather than being rejected.

    lock_path = os.path.join(sources_dir, 'Cargo.lock')
    generated_lock = not os.path.exists(lock_path)
    if not generated_lock:
        cmd.append('--locked')
    cmd.append(os.path.join(*vendor_dir))
    print("Invoking '%s' in '%s'" % (' '.join(cmd), sources_dir))
    vendor_config = subprocess.check_output(cmd, cwd=sources_dir).decode()
    # the source replacement configuration which the build recipe needs to use
    # to build against the vendored crates, the recipe hardcodes it since it
    # only ever describes crates.io as long as the check above passes
    print(vendor_config)

    # a lock file cargo just resolved is a modification of the upstream part
    # of the source tree, which dpkg-source refuses to represent as a quilt
    # patch, the vendored crates are the pinned dependency set in this case
    if generated_lock:
        print("Removing the '%s' generated while vendoring" % lock_path)
        os.remove(lock_path)
