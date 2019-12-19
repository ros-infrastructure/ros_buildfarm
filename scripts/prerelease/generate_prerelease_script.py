#!/usr/bin/env python

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

import argparse
from copy import deepcopy
import os
import stat
import sys

from em import BANGPATH_OPT
from em import Hook
from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_build_tool
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_custom_rosdep_update_options
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_output_dir
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.config import get_index as get_config_index
from ros_buildfarm.config import get_release_build_files
from ros_buildfarm.config import get_source_build_files
from ros_buildfarm.devel_job import configure_devel_job
from ros_buildfarm.prerelease import add_overlay_arguments
from ros_buildfarm.templates import expand_template
from rosdistro import get_distribution_cache
from rosdistro import get_index
from rosdistro.repository_specification import RepositorySpecification


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate a 'prerelease' script")
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'source')
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)
    add_argument_build_tool(parser)
    add_argument_custom_rosdep_update_options(parser)
    add_argument_output_dir(parser, required=True)

    group = parser.add_argument_group(
        'Repositories in underlay workspace',
        description='The repositories in the underlay workspace will be ' +
                    'built and installed as well as built and tested. ' +
                    'Dependencies will be provided by binary packages.')
    group.add_argument(
        'source_repos',
        nargs='*',
        default=[],
        metavar='REPO_NAME',
        help="A name of a 'repository' from the distribution file")
    group.add_argument(
        '--custom-branch',
        nargs='*',
        type=_repository_name_and_branch,
        default=[],
        metavar='REPO_NAME:BRANCH_OR_TAG_NAME',
        help="A name of a 'repository' from the distribution file followed " +
             'by a colon and a branch / tag name')
    group.add_argument(
        '--custom-repo',
        nargs='*',
        type=_repository_name_and_type_and_url_and_branch,
        default=[],
        metavar='REPO_NAME:REPO_TYPE:REPO_URL:BRANCH_OR_TAG_NAME',
        help='The name, type, url and branch / tag name of a repository, '
             'e.g. "common_tutorials:git:https://github.com/ros/common_tutorials:pullrequest-1"')

    add_overlay_arguments(parser)

    args = parser.parse_args(argv)

    print('Fetching buildfarm configuration...')
    config = get_config_index(args.config_url)
    build_files = get_source_build_files(config, args.rosdistro_name)
    build_file = build_files[args.source_build_name]

    print('Fetching rosdistro cache...')
    # Targets defined by source build file are subset of targets
    # defined by release build files. To increase the number of supported
    # pre-release targets, we combine all targets defined by all release
    # build files and use that when configuring the devel job.
    release_build_files = get_release_build_files(config, args.rosdistro_name)
    release_targets_combined = {}
    if release_build_files:
        release_targets_combined[args.os_name] = {}
        for build_name, rel_obj in release_build_files.items():
            if args.os_name not in rel_obj.targets:
                continue
            for dist_name, targets in rel_obj.targets[args.os_name].items():
                if dist_name not in release_targets_combined[args.os_name]:
                    release_targets_combined[args.os_name][dist_name] = {}
                release_targets_combined[args.os_name][dist_name].update(targets)

    index = get_index(config.rosdistro_index_url)
    dist_cache = get_distribution_cache(index, args.rosdistro_name)
    dist_file = dist_cache.distribution_file

    # determine source repositories for underlay workspace
    repositories = {}
    for repo_name in args.source_repos:
        if repo_name in repositories:
            print("The repository '%s' appears multiple times" % repo_name,
                  file=sys.stderr)
            return 1
        try:
            repositories[repo_name] = \
                dist_file.repositories[repo_name].source_repository
        except KeyError:
            print(("The repository '%s' was not found in the distribution " +
                   "file") % repo_name, file=sys.stderr)
            return 1
        if not repositories[repo_name]:
            print(("The repository '%s' has no source entry in the " +
                   "distribution file") % repo_name, file=sys.stderr)
            return 1

    for repo_name, custom_version in args.custom_branch:
        if repo_name in repositories:
            print("The repository '%s' appears multiple times" % repo_name,
                  file=sys.stderr)
            return 1
        try:
            source_repo = dist_file.repositories[repo_name].source_repository
        except KeyError:
            print(("The repository '%s' was not found in the distribution " +
                   "file") % repo_name, file=sys.stderr)
            return 1
        if not source_repo:
            print(("The repository '%s' has no source entry in the " +
                   "distribution file") % repo_name, file=sys.stderr)
            return 1
        source_repo = deepcopy(source_repo)
        source_repo.version = custom_version
        repositories[repo_name] = source_repo

    for repo_name, repo_type, repo_url, version in args.custom_repo:
        if repo_name in repositories and repositories[repo_name]:
            print("custom_repos option overriding '%s' to pull via '%s' "
                  "from '%s' with version '%s'. " %
                  (repo_name, repo_type, repo_url, version),
                  file=sys.stderr)
        source_repo = RepositorySpecification(
            repo_name, {
                'type': repo_type,
                'url': repo_url,
                'version': version,
            })
        repositories[repo_name] = source_repo

    scms = [(repositories[k], 'ws/src/%s' % k)
            for k in sorted(repositories.keys())]

    # collect all template snippets of specific types
    class IncludeHook(Hook):

        def __init__(self):
            Hook.__init__(self)
            self.scripts = []

        def beforeInclude(self, *_, **kwargs):
            template_path = kwargs['file'].name
            if template_path.endswith('/snippet/builder_shell.xml.em'):
                script = kwargs['locals']['script']
                # reuse existing ros_buildfarm folder if it exists
                if 'Clone ros_buildfarm' in script:
                    lines = script.splitlines()
                    lines.insert(0, 'if [ ! -d "ros_buildfarm" ]; then')
                    lines += [
                        'else',
                        'echo "Using existing ros_buildfarm folder"',
                        'fi',
                    ]
                    script = '\n'.join(lines)
                if args.build_tool and ' --build-tool ' in script:
                    script = script.replace(
                        ' --build-tool catkin_make_isolated',
                        ' --build-tool ' + args.build_tool)
                self.scripts.append(script)

    hook = IncludeHook()
    from ros_buildfarm import templates
    templates.template_hooks = [hook]

    # use any source repo to pass to devel job template
    if index.distributions[args.rosdistro_name].get('distribution_type', 'ros1') == 'ros1':
        package_name = 'catkin'
    elif index.distributions[args.rosdistro_name].get('distribution_type', 'ros1') == 'ros2':
        package_name = 'ros_workspace'
    else:
        assert False, 'Unsupported ROS version ' + \
            str(index.distributions[args.rosdistro_name].get('distribution_type', None))
    source_repository = deepcopy(
        dist_file.repositories[package_name].source_repository)
    if not source_repository:
        print(("The repository '%s' does not have a source entry in the distribution " +
               'file. We cannot generate a prerelease without a source entry.') % package_name,
              file=sys.stderr)
        return 1
    source_repository.name = 'prerelease'
    print('Evaluating job templates...')
    configure_devel_job(
        args.config_url, args.rosdistro_name, args.source_build_name,
        None, args.os_name, args.os_code_name, args.arch,
        config=config, build_file=build_file,
        index=index, dist_file=dist_file, dist_cache=dist_cache,
        jenkins=False, views=False,
        source_repository=source_repository,
        build_targets=release_targets_combined)

    templates.template_hooks = None

    # derive scripts for overlay workspace from underlay
    overlay_scripts = []
    for script in hook.scripts:
        # skip cloning of ros_buildfarm repository
        if 'git clone' in script and '.git ros_buildfarm' in script:
            continue
        # skip build-and-install step
        if 'build and install' in script:
            continue

        # add prerelease overlay flag
        run_devel_job = '/run_devel_job.py'
        if run_devel_job in script:
            script = script.replace(
                run_devel_job, run_devel_job + ' --prerelease-overlay')

        # replace mounted workspace volume with overlay and underlay
        # used by:
        # - create_devel_task_generator.py needs to find packages in both
        # the underlay as well as the overlay workspace
        # - build_and_test.py needs to source the environment of
        # the underlay before building the overlay
        mount_volume = '-v $WORKSPACE/ws:/tmp/ws'
        if mount_volume in script:
            script = script.replace(
                mount_volume, mount_volume + ':ro ' + '-v $WORKSPACE/' +
                'ws_overlay:/tmp/ws2')

        # relocate all docker files
        docker_path = '$WORKSPACE/docker_'
        if docker_path in script:
            script = script.replace(
                docker_path, docker_path + 'overlay_')

        # rename all docker images
        name_suffix = '_prerelease'
        if name_suffix in script:
            script = script.replace(
                name_suffix, name_suffix + '_overlay')

        overlay_scripts.append(script)

    from ros_buildfarm import __file__ as ros_buildfarm_file
    data = deepcopy(args.__dict__)
    data.update({
        'scms': scms,
        'scripts': hook.scripts,
        'overlay_scripts': overlay_scripts,
        'rosdep_update_options': args.custom_rosdep_update_options,
        'ros_buildfarm_python_path': os.path.dirname(
            os.path.dirname(os.path.abspath(ros_buildfarm_file))),
        'python_executable': sys.executable,
        'prerelease_script_path': os.path.dirname(os.path.abspath(__file__)),
        'build_tool': args.build_tool or build_file.build_tool})

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # generate multiple scripts
    for script_name in [
            'prerelease',
            'prerelease_build_overlay',
            'prerelease_build_underlay',
            'prerelease_clone_overlay',
            'prerelease_clone_underlay']:
        content = expand_template(
            'prerelease/%s_script.sh.em' % script_name, data,
            options={BANGPATH_OPT: False})
        script_file = os.path.join(args.output_dir, script_name + '.sh')
        with open(script_file, 'w') as h:
            h.write(content)
        os.chmod(script_file, os.stat(script_file).st_mode | stat.S_IEXEC)

    print('')
    print('Generated prerelease script - to execute it run:')
    if os.path.abspath(args.output_dir) != os.path.abspath(os.curdir):
        print('  cd %s' % args.output_dir)
    print('  ./prerelease.sh')


def _repository_name_and_branch(arg):
    if arg.count(':') != 1:
        msg = "'%s' is not a repository name and a branch / tag name " + \
              "separated by a colon" % arg
        raise argparse.ArgumentTypeError(msg)
    return arg.split(':')


def _repository_name_and_type_and_url_and_branch(arg):
    if arg.count(':') < 4:
        msg = ("'%s' is not a name, repository type, url and branch / tag " +
               "name separated by colons") % arg
        raise argparse.ArgumentTypeError(msg)
    first_index = arg.index(':')
    second_index = arg.index(':', first_index + 1)
    last_index = arg.rindex(':')
    return \
        arg[:first_index], \
        arg[first_index + 1:second_index], \
        arg[second_index + 1: last_index], \
        arg[last_index + 1:]


if __name__ == '__main__':
    sys.exit(main())
