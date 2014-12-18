#!/usr/bin/env python

from __future__ import print_function

import argparse
from copy import deepcopy
from em import BANGPATH_OPT
import os
import stat
import sys

from rosdistro import get_distribution_cache
from rosdistro import get_index
from rosdistro.repository_specification import RepositorySpecification

from ros_buildfarm import templates
from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_output_dir
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.config import get_index as get_config_index
from ros_buildfarm.config import get_source_build_files
from ros_buildfarm.devel_job import configure_devel_job
from ros_buildfarm.prerelease import add_overlay_arguments
from ros_buildfarm.templates import expand_template

# 1st workspace - set of repos
# - each repo:
#   - repo by name from distro file using the branch specified there
#   - repo by name from distro file using a specific branch
#   - repo by type / url / version
# - repos specified in a rosinstall file

# 2nd workspace - set of pkgs
# - release pkg names, resolve to their released version from the distro file, fetch sources from gbp
# - by dependency level (default: 2)
# - explicit pkg names
# - blacklist pkg names

# steps
# - create empty 1st ws
# - clone specified repos into 1st ws (doesn't require anything)
# - devel job
#   - without a specific repo
#   - but with the set of repos specified
#   - installs dependencies in the docker instance
#   - runs cmi_and_install and cmi_and_test
# - catkin_test_results on 1st workspace
#
# - clone specified pkgs into 2nd ws (doesn't require anything)
# - run build_and_install dockerfile again but override CMD
#   - pass in both workspaces
#   - instance still has deps of 1st ws
#   - clone all pkgs including the in-between pkgs from source into 2nd ws
#     (need to do this incrementally since the dependencies might have changed)
#     (requires rosdistro, catkin_pkg, etc. but runs in docker)
#   - install all missing dependencies using rosdep
#     (requires rosdep, etc. but runs in docker)
#   - invoke cmi_and_test on 2nd ws
# - catkin_test_results on 2nd workspace


def main(argv=sys.argv[1:]):
    global templates
    parser = argparse.ArgumentParser(
        description="Generate a 'prerelease' script")
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'source')
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)
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
        help='The name, type, url and branch / tag name of a repository')

    add_overlay_arguments(parser)

    args = parser.parse_args(argv)

    print('Fetching buildfarm configuration...')
    config = get_config_index(args.config_url)
    build_files = get_source_build_files(config, args.rosdistro_name)
    build_file = build_files[args.source_build_name]

    print('Fetching rosdistro cache...')
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
        source_repo = deepcopy(source_repo)
        source_repo.version = custom_version
        repositories[repo_name] = source_repo

    for repo_name, repo_type, repo_url, version in args.custom_repo:
        if repo_name in repositories:
            print("The repository '%s' appears multiple times" % repo_name,
                  file=sys.stderr)
            return 1
        source_repo = RepositorySpecification(
            repo_name, {
                'type': repo_type,
                'url': repo_url,
                'version': version,
            })
        repositories[repo_name] = source_repo

    scms = [(repositories[k], 'catkin_workspace/src/%s' % k)
            for k in sorted(repositories.keys())]

    # collect all template snippets of specific types from the devel job
    print('Evaluating job templates...')
    scripts = []

    def template_hook(template_name, data, content):
        if template_name == 'snippet/builder_shell.xml.em':
            scripts.append(data['script'])
    templates.template_hook = template_hook

    # use random source repo to pass to devel job template
    source_repository = deepcopy(list(repositories.values())[0])
    source_repository.name = 'prerelease'
    configure_devel_job(
        args.config_url, args.rosdistro_name, args.source_build_name,
        None, args.os_name, args.os_code_name, args.arch, False,
        config=config, build_file=build_file,
        index=index, dist_file=dist_file, dist_cache=dist_cache,
        jenkins=False, view=False,
        source_repository=source_repository)

    templates.template_hook = None

    # derive scripts for overlay workspace from underlay
    overlay_scripts = []
    for script in scripts:
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
        # - catkin_make_isolated_and_test.py needs to source the environment of
        # the underlay before building the overlay
        mount_volume = '-v $WORKSPACE/catkin_workspace:/tmp/catkin_workspace'
        if mount_volume in script:
            script = script.replace(
                mount_volume, mount_volume + ':ro ' + '-v $WORKSPACE/' +
                'catkin_workspace_overlay:/tmp/catkin_workspace_overlay')

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

    data = deepcopy(args.__dict__)
    data.update({
        'scms': scms,
        'scripts': scripts,
        'overlay_scripts': overlay_scripts,
        'ros_buildfarm_path': os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'python_executable': sys.executable})

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
