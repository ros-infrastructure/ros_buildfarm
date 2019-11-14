# Copyright 2014-2016 Open Source Robotics Foundation, Inc.
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

from __future__ import print_function

from collections import namedtuple
import os
import subprocess
import sys

from ros_buildfarm import __version__
from ros_buildfarm.common import find_executable

FALLBACK_REPOSITORY_URL = \
    'https://github.com/ros-infrastructure/ros_buildfarm.git'


def get_repository():
    msg1 = 'The git repository %s is different than the %s'
    msg2 = 'You might want to update the %s to ensure that your forked ' + \
        'version continues to work correctly when being used outside of a ' + \
        'git working copy (e.g. after being installed or from a tarball)'

    # get repository url from git or fallback to hard coded value
    basepath = os.path.dirname(os.path.dirname(__file__))
    url = _get_git_repository_remote_origin(basepath)
    if url is None:
        url = FALLBACK_REPOSITORY_URL

    prefix_mapping = {
        'git@github.com:': 'https://github.com/',
    }
    for k, v in prefix_mapping.items():
        if url.startswith(k):
            url = v + url[len(k):]

    if url != FALLBACK_REPOSITORY_URL:
        print(msg1 %
              ("url '%s'" % url, "fallback url '%s' defined in '%s'" %
               (FALLBACK_REPOSITORY_URL, os.path.abspath(__file__))),
              file=sys.stderr)
        print(msg2 % 'fallback url', file=sys.stderr)

    # get repository version from git, PR branch or fallback to version string
    version = _get_git_repository_version(basepath)
    version_number, repository_version = _get_version_parts()
    pr_branch = os.environ.get('ROS_BUILDFARM_PULL_REQUEST_BRANCH')
    if version is None:
        if pr_branch is not None:
            version = pr_branch
        elif repository_version is not None:
            version = repository_version
        else:
            version = version_number
    elif version not in [version_number, repository_version]:
        print(msg1 %
              ("version '%s'" % version,
               "Python package version '%s'" % __version__), file=sys.stderr)
        print(msg2 % 'Python package version', file=sys.stderr)

    return namedtuple('Repository', 'url version')(url, version)


def _get_git_repository_remote_origin(path):
    # check that path is a git working copy
    if not os.path.exists(os.path.join(path, '.git')):
        return None

    git = find_executable('git')
    if git:
        url = subprocess.check_output(
            [git, 'config', 'remote.origin.url'], cwd=path)
        return url.decode().rstrip()

    # extract url of remote origin from git config file
    with open(os.path.join(path, '.git', 'config'), 'r') as h:
        lines = h.read().splitlines()
    section = '[remote "origin"]'
    if section not in lines:
        return None
    section_index = lines.index(section)

    index = section_index + 1
    while index < len(lines):
        line = lines[index]
        if line.startswith('['):
            return None
        line = line.lstrip()
        line_parts = line.split(' = ', 1)
        if line_parts[0] == 'url':
            return line_parts[1]
        index += 1
    return None


def _get_git_repository_version(path):
    # check that path is a git working copy
    if not os.path.exists(os.path.join(path, '.git')):
        return None

    git = find_executable('git')
    if not git:
        return None

    # check for local modifications
    try:
        any_modifications = subprocess.check_output(
            [git, 'status', '--short'], cwd=path)
    except subprocess.CalledProcessError:
        return None
    if any_modifications:
        print("Your git workspace contains local modifications. They won't " +
              'propagate to the actual jobs when not available from the git ' +
              'repository.', file=sys.stderr)

    # check if working copy is on a branch
    # (does not apply when a specific tag is checked out)
    url = subprocess.check_output(
        [git, 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=path)
    url = url.decode().rstrip()
    if url != 'HEAD':
        # get plain branch name on Jenkins
        prefix = 'heads/origin/'
        if url.startswith(prefix):
            url = url[len(prefix):]
        return url

    # check if working copy is on a tag
    try:
        with open(os.devnull, 'w') as h:
            tags = subprocess.check_output(
                [git, 'describe', '--exact-match', '--tags'],
                cwd=path, stderr=h)
        return tags.decode().splitlines()[0]
    except subprocess.CalledProcessError:
        pass

    # if the HEAD is detached the only way to retrieve the branch is
    # looking for the environment variable set by Jenkins
    env_var = 'GIT_BRANCH'
    if env_var in os.environ:
        git_branch = os.environ[env_var]
        prefix = 'origin/'
        if git_branch.startswith(prefix):
            return git_branch[len(prefix):]

    # use current hash
    return get_hash(path)


def get_hash(path):
    # check that path is a git working copy
    if not os.path.exists(os.path.join(path, '.git')):
        return None

    git = find_executable('git')
    if not git:
        return None

    hash_ = subprocess.check_output(
        [git, 'rev-parse', 'HEAD'], cwd=path)
    return hash_.decode().rstrip()


def _get_version_parts():
    version_parts = __version__.split('-', 1)
    if len(version_parts) == 2:
        return version_parts
    return version_parts[0], None
