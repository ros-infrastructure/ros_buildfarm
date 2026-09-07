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


def _get_cargo_metadata(sources_dir):
    # '--no-deps' restricts this to the manifests in the workspace and skips
    # resolving the dependency graph, so it needs neither a lock file nor
    # network access
    cmd = [
        'cargo', 'metadata', '--no-deps', '--offline', '--format-version', '1']
    print("Invoking '%s' in '%s'" % (' '.join(cmd), sources_dir))
    return json.loads(subprocess.check_output(cmd, cwd=sources_dir).decode())


def _get_non_crates_io_dependencies(metadata):
    CRATES_IO_SOURCE = 'registry+https://github.com/rust-lang/crates.io-index'

    # the manifests are enough to cover the whole graph: crates.io refuses to
    # publish a crate depending on a git repository or on another registry, so
    # no crates.io crate can pull one in transitively
    dependencies = []
    for package in metadata['packages']:
        for dependency in package['dependencies']:
            # a path dependency within the workspace carries no source
            if dependency['source'] in (None, CRATES_IO_SOURCE):
                continue
            dependencies.append((dependency['name'], dependency['source']))
    return dependencies


def _get_ros_crates(metadata):
    # crates supplied by other ROS packages, which are not published to
    # crates.io and are resolved from the ROS registry when the package builds
    crates = []
    for package in metadata['packages']:
        package_metadata = package.get('metadata') or {}
        crates += (package_metadata.get('ros') or {}).get('crates', [])
    return crates


def _remove_ros_crates(sources_dir, crates):
    # ROS crates are assumed to be declared in '[dependencies]', which is what
    # 'cargo remove' operates on. It fails when the crate is not there, so a
    # typo in the manifest metadata is reported instead of silently ignored
    for crate in crates:
        cmd = ['cargo', 'remove', crate]
        print("Invoking '%s' in '%s'" % (' '.join(cmd), sources_dir))
        subprocess.check_call(cmd, cwd=sources_dir)


def vendor_cargo_crates(sources_dir, vendor_dir):
    manifest_path = os.path.join(sources_dir, 'Cargo.toml')
    if not os.path.exists(manifest_path):
        print("No 'Cargo.toml' in '%s', skipping cargo crate vendoring" %
              sources_dir)
        return

    metadata = _get_cargo_metadata(sources_dir)

    # crates from git repositories or from registries other than crates.io do
    # not go through a crates.io release and can change or disappear without
    # notice, refuse to ship them in the source package. Checked before
    # vendoring so that none of them is fetched in the first place
    external_deps = _get_non_crates_io_dependencies(metadata)
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
    if os.path.exists(lock_path):
        cmd.append('--locked')
    cmd.append(os.path.join(*vendor_dir))

    # cargo cannot vendor a crate which is not published to crates.io, so the
    # ones other ROS packages supply are taken out of the manifest for the
    # duration of the vendoring
    with open(manifest_path, 'r') as h:
        manifest_backup = h.read()
    lock_backup = None
    if os.path.exists(lock_path):
        with open(lock_path, 'r') as h:
            lock_backup = h.read()

    try:
        _remove_ros_crates(sources_dir, _get_ros_crates(metadata))
        print("Invoking '%s' in '%s'" % (' '.join(cmd), sources_dir))
        vendor_config = subprocess.check_output(cmd, cwd=sources_dir).decode()
        # the source replacement configuration which the build recipe needs to
        # use to build against the vendored crates, the recipe hardcodes it
        # since it only ever describes crates.io as long as the check passed
        print(vendor_config)
    finally:
        # whatever cargo left behind is a modification of the upstream part of
        # the source tree, which dpkg-source refuses to represent as a quilt
        # patch, the vendored crates are the pinned dependency set instead
        with open(manifest_path, 'w') as h:
            h.write(manifest_backup)
        if lock_backup is not None:
            with open(lock_path, 'w') as h:
                h.write(lock_backup)
        elif os.path.exists(lock_path):
            os.remove(lock_path)
