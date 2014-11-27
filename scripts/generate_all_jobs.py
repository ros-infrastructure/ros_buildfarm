#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys


from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.config import get_index
from ros_buildfarm.config import get_release_build_files
from ros_buildfarm.config import get_source_build_files
from ros_buildfarm.jenkins import connect


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Generate all jobs on Jenkins')
    add_argument_config_url(parser)
    parser.add_argument(
        '--ros-distro-names',
        nargs='*',
        metavar='ROS_DISTRO_NAME',
        default=[],
        help='The list of ROS distribution names if not generating all')
    args = parser.parse_args(argv)

    config = get_index(args.config_url)
    ros_distro_names = config.distributions.keys()

    invalid_ros_distro_name = [
        n for n in args.ros_distro_names if n not in ros_distro_names]
    if invalid_ros_distro_name:
        parser.error(
            'The following ROS distribution names are not part of the ' +
            'buildfarm index: ' + ', '.join(sorted(invalid_ros_distro_name)))

    # try to connect to Jenkins master
    connect(config.jenkins_url)

    generate_dashboard_job(args.config_url)

    selected_ros_distro_names = [
        n for n in ros_distro_names
        if not args.ros_distro_names or n in args.ros_distro_names]

    for ros_distro_name in sorted(selected_ros_distro_names):
        print(ros_distro_name)

        generate_rosdistro_cache_job(args.config_url, ros_distro_name)

        release_build_files = get_release_build_files(config, ros_distro_name)
        for release_build_name in release_build_files.keys():
            generate_release_status_page_job(
                args.config_url, ros_distro_name, release_build_name)
            generate_release_maintenance_jobs(
                args.config_url, ros_distro_name, release_build_name)

        source_build_files = get_source_build_files(config, ros_distro_name)
        for source_build_name in source_build_files.keys():
            generate_devel_maintenance_jobs(
                args.config_url, ros_distro_name, source_build_name)

        generate_repos_status_page_jobs(
            args.config_url, config, ros_distro_name)


def generate_dashboard_job(config_url):
    cmd = [
        'misc/generate_dashboard_job.py',
        config_url,
    ]
    _check_call(cmd)


def generate_rosdistro_cache_job(config_url, ros_distro_name):
    cmd = [
        'misc/generate_rosdistro_cache_job.py',
        config_url,
        ros_distro_name,
    ]
    _check_call(cmd)


def generate_release_status_page_job(
        config_url, ros_distro_name, release_build_name):
    cmd = [
        'status/generate_release_status_page_job.py',
        config_url,
        ros_distro_name,
        release_build_name,
    ]
    _check_call(cmd)


def generate_repos_status_page_jobs(
        config_url, config, ros_distro_name):
    # collect all target repositories (building) and their targets
    # from all release build files
    target_repositories = {}
    release_build_files = get_release_build_files(config, ros_distro_name)
    for release_build_file in release_build_files.values():
        target_repository = release_build_file.target_repository
        if target_repository not in target_repositories:
            target_repositories[target_repository] = []
        # TODO support other OS names
        if 'ubuntu' in release_build_file.targets:
            targets = release_build_file.targets['ubuntu']
            for os_code_name in sorted(targets.keys()):
                target = '%s:source' % os_code_name
                if target not in target_repositories[target_repository]:
                    target_repositories[target_repository].append(target)
                for arch in sorted(targets[os_code_name].keys()):
                    target = '%s:%s' % (os_code_name, arch)
                    if target not in target_repositories[target_repository]:
                        target_repositories[target_repository].append(target)

    # generate a repos status page for each unique building repo
    # using all targets listed in any release build file with that target repo
    for i, target_repository in enumerate(sorted(target_repositories.keys())):
        if not target_repository.endswith('/building'):
            print("Skipped target repository '%s' " % target_repository +
                  " because it does not end with '/building'", file=sys.stderr)
            continue

        os_code_name_and_arch_tuples = target_repositories[target_repository]

        # derive testing and main urls from building url
        base_url = os.path.dirname(target_repository)
        testing_url = os.path.join(base_url, 'testing')
        main_url = os.path.join(base_url, 'main')

        output_name = '%s_repos' % ros_distro_name
        if i > 0:
            output_name += str(i + 1)
        generate_repos_status_page_job(
            config_url,
            [target_repository, testing_url, main_url],
            os_code_name_and_arch_tuples,
            output_name)


def generate_repos_status_page_job(
        config_url, debian_repository_urls, os_code_name_and_arch_tuples,
        output_name):
    cmd = [
        'status/generate_repos_status_page_job.py',
        config_url
    ]
    cmd += debian_repository_urls
    cmd += ['--os-code-name-and-arch-tuples'] + os_code_name_and_arch_tuples
    cmd += ['--output-name', output_name]
    _check_call(cmd)


def generate_release_maintenance_jobs(
        config_url, ros_distro_name, release_build_name):
    cmd = [
        'release/generate_release_maintenance_jobs.py',
        config_url,
        ros_distro_name,
        release_build_name,
    ]
    _check_call(cmd)


def generate_devel_maintenance_jobs(
        config_url, ros_distro_name, release_build_name):
    cmd = [
        'devel/generate_devel_maintenance_jobs.py',
        config_url,
        ros_distro_name,
        release_build_name,
    ]
    _check_call(cmd)


def _check_call(cmd):
    print('')
    print("Invoking '%s'" % ' '.join(cmd))
    print('')
    basepath = os.path.dirname(__file__)
    cmd[0] = os.path.join(basepath, cmd[0])
    subprocess.check_call(cmd)
    print('')


if __name__ == '__main__':
    main()
