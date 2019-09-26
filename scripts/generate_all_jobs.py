#!/usr/bin/env python3

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

import argparse
import imp
import os
import sys

from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.config import get_ci_build_files
from ros_buildfarm.config import get_doc_build_files
from ros_buildfarm.config import get_index
from ros_buildfarm.config import get_release_build_files
from ros_buildfarm.config import get_source_build_files
from ros_buildfarm.config.doc_build_file import DOC_TYPE_MANIFEST
from ros_buildfarm.config.doc_build_file import DOC_TYPE_ROSDOC
from ros_buildfarm.jenkins import configure_view
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
    parser.add_argument(
        '--skip-rosdistro-cache-job',
        action='store_true',
        help='Skip generating the rosdistro-cache jobs')
    parser.add_argument(
        '--commit',
        action='store_true',
        help='Apply the changes to Jenkins instead of only showing them')
    args = parser.parse_args(argv)

    if args.commit:
        print('The following changes will be applied to the Jenkins server.')
    else:
        print('This is a dry run. The Jenkins configuration is not changed.')
    print('')

    config = get_index(args.config_url)
    if args.config_url.startswith('file:'):
        print(
            'WARNING: Local file system path used for configuration. ',
            'Configuration will not be accessible to jobs during execution. ',
            'Consider  using a web(http) hosted configuration repository.',
            file=sys.stderr)

    ros_distro_names = sorted(config.distributions.keys())

    invalid_ros_distro_name = [
        n for n in args.ros_distro_names if n not in ros_distro_names]
    if invalid_ros_distro_name:
        parser.error(
            'The following ROS distribution names are not part of the ' +
            'buildfarm index: ' + ', '.join(sorted(invalid_ros_distro_name)))

    # try to connect to Jenkins master
    jenkins = connect(config.jenkins_url)

    configure_view(
        jenkins, 'Queue', filter_queue=False, dry_run=not args.commit)

    generate_check_agents_job(args.config_url, dry_run=not args.commit)

    if not args.ros_distro_names:
        generate_dashboard_job(args.config_url, dry_run=not args.commit)

        for doc_build_name in sorted(config.doc_builds.keys()):
            generate_doc_independent_job(
                args.config_url, doc_build_name, dry_run=not args.commit)

    selected_ros_distro_names = [
        n for n in ros_distro_names
        if not args.ros_distro_names or n in args.ros_distro_names]

    for ros_distro_name in selected_ros_distro_names:
        print(ros_distro_name)

        if not args.skip_rosdistro_cache_job:
            generate_rosdistro_cache_job(
                args.config_url, ros_distro_name, dry_run=not args.commit)

        generate_failing_jobs_job(
            args.config_url, ros_distro_name, dry_run=not args.commit)

        release_build_files = get_release_build_files(config, ros_distro_name)
        for release_build_name in release_build_files.keys():
            generate_release_status_page_job(
                args.config_url, ros_distro_name, release_build_name,
                dry_run=not args.commit)
            generate_release_maintenance_jobs(
                args.config_url, ros_distro_name, release_build_name,
                dry_run=not args.commit)

        source_build_files = get_source_build_files(config, ros_distro_name)
        for source_build_name in source_build_files.keys():
            generate_devel_maintenance_jobs(
                args.config_url, ros_distro_name, source_build_name,
                dry_run=not args.commit)

        ci_build_files = get_ci_build_files(config, ros_distro_name)
        for ci_build_name in ci_build_files.keys():
            generate_ci_maintenance_jobs(
                args.config_url, ros_distro_name, ci_build_name,
                dry_run=not args.commit)

        doc_build_files = get_doc_build_files(config, ros_distro_name)
        for doc_build_name, doc_build_file in doc_build_files.items():
            if doc_build_file.documentation_type == DOC_TYPE_ROSDOC:
                generate_doc_maintenance_jobs(
                    args.config_url, ros_distro_name, doc_build_name,
                    dry_run=not args.commit)
            elif doc_build_file.documentation_type == DOC_TYPE_MANIFEST:
                generate_doc_metadata_job(
                    args.config_url, ros_distro_name, doc_build_name,
                    dry_run=not args.commit)
            else:
                assert False, ("Unknown documentation type '%s' in doc " +
                               "build file '%s'") % \
                    (doc_build_file.documentation_type, doc_build_name)

        generate_repos_status_page_jobs(
            args.config_url, ros_distro_name, dry_run=not args.commit)
        index = ros_distro_names.index(ros_distro_name)
        if index > 0:
            # generate compare pages for this rosdistro against all older ones
            generate_release_compare_page_job(
                args.config_url, ros_distro_name, ros_distro_names[:index],
                dry_run=not args.commit)
            generate_blocked_releases_page_job(
                args.config_url, ros_distro_name, dry_run=not args.commit)
            generate_blocked_source_entries_page_job(
                args.config_url, ros_distro_name, dry_run=not args.commit)


def generate_check_agents_job(config_url, dry_run=False):
    cmd = [
        _resolve_script('misc', 'generate_check_agents_job.py'),
        config_url,
    ]
    if dry_run:
        cmd.append('--dry-run')
    _check_call(cmd)


def generate_dashboard_job(config_url, dry_run=False):
    cmd = [
        _resolve_script('misc', 'generate_dashboard_job.py'),
        config_url,
    ]
    if dry_run:
        cmd.append('--dry-run')
    _check_call(cmd)


def generate_rosdistro_cache_job(config_url, ros_distro_name, dry_run=False):
    cmd = [
        _resolve_script('misc', 'generate_rosdistro_cache_job.py'),
        config_url,
        ros_distro_name,
    ]
    if dry_run:
        cmd.append('--dry-run')
    _check_call(cmd)


def generate_failing_jobs_job(config_url, ros_distro_name, dry_run=False):
    cmd = [
        _resolve_script('misc', 'generate_failing_jobs_job.py'),
        config_url,
        ros_distro_name,
    ]
    if dry_run:
        cmd.append('--dry-run')
    _check_call(cmd)


def generate_release_status_page_job(
        config_url, ros_distro_name, release_build_name, dry_run=False):
    cmd = [
        _resolve_script('status', 'generate_release_status_page_job.py'),
        config_url,
        ros_distro_name,
        release_build_name,
    ]
    if dry_run:
        cmd.append('--dry-run')
    _check_call(cmd)


def generate_repos_status_page_jobs(
        config_url, ros_distro_name, dry_run=False):
    cmd = [
        _resolve_script('status', 'generate_repos_status_page_job.py'),
        config_url,
        ros_distro_name,
    ]
    if dry_run:
        cmd.append('--dry-run')
    _check_call(cmd)


def generate_release_compare_page_job(
        config_url, ros_distro_name, older_ros_distro_names, dry_run=False):
    cmd = [
        _resolve_script('status', 'generate_release_compare_page_job.py'),
        config_url,
        ros_distro_name,
    ] + older_ros_distro_names
    if dry_run:
        cmd.append('--dry-run')
    _check_call(cmd)


def generate_blocked_releases_page_job(
        config_url, ros_distro_name, dry_run=False):
    cmd = [
        _resolve_script('status', 'generate_blocked_releases_page_job.py'),
        config_url,
        ros_distro_name,
    ]
    if dry_run:
        cmd.append('--dry-run')
    _check_call(cmd)


def generate_blocked_source_entries_page_job(
        config_url, ros_distro_name, dry_run=False):
    cmd = [
        _resolve_script('status', 'generate_blocked_source_entries_page_job.py'),
        config_url,
        ros_distro_name,
    ]
    if dry_run:
        cmd.append('--dry-run')
    _check_call(cmd)


def generate_release_maintenance_jobs(
        config_url, ros_distro_name, release_build_name, dry_run=False):
    cmd = [
        _resolve_script('release', 'generate_release_maintenance_jobs.py'),
        config_url,
        ros_distro_name,
        release_build_name,
    ]
    if dry_run:
        cmd.append('--dry-run')
    _check_call(cmd)


def generate_ci_maintenance_jobs(
        config_url, ros_distro_name, ci_build_name, dry_run=False):
    cmd = [
        _resolve_script('ci', 'generate_ci_maintenance_jobs.py'),
        config_url,
        ros_distro_name,
    ]
    if dry_run:
        cmd.append('--dry-run')
    _check_call(cmd)


def generate_devel_maintenance_jobs(
        config_url, ros_distro_name, source_build_name, dry_run=False):
    cmd = [
        _resolve_script('devel', 'generate_devel_maintenance_jobs.py'),
        config_url,
        ros_distro_name,
        source_build_name,
    ]
    if dry_run:
        cmd.append('--dry-run')
    _check_call(cmd)


def generate_doc_maintenance_jobs(
        config_url, ros_distro_name, doc_build_name, dry_run=False):
    cmd = [
        _resolve_script('doc', 'generate_doc_maintenance_jobs.py'),
        config_url,
        ros_distro_name,
        doc_build_name,
    ]
    if dry_run:
        cmd.append('--dry-run')
    _check_call(cmd)


def generate_doc_independent_job(
        config_url, doc_build_name, dry_run=False):
    cmd = [
        _resolve_script('doc', 'generate_doc_independent_job.py'),
        config_url,
        doc_build_name,
    ]
    if dry_run:
        cmd.append('--dry-run')
    _check_call(cmd)


def generate_doc_metadata_job(
        config_url, ros_distro_name, doc_build_name, dry_run=False):
    cmd = [
        _resolve_script('doc', 'generate_doc_metadata_job.py'),
        config_url,
        ros_distro_name,
        doc_build_name,
    ]
    if dry_run:
        cmd.append('--dry-run')
    _check_call(cmd)


def _resolve_script(subfolder, filename):
    basepath = os.path.abspath(os.path.dirname(__file__))
    subfolder_path = os.path.join(basepath, subfolder, filename)
    if os.path.exists(subfolder_path):
        return subfolder_path
    sibling_path = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(sibling_path):
        return sibling_path
    assert False, "Could not find script '%s' from subfolder '%s'" % \
        (filename, subfolder)


def _check_call(cmd):
    print('')
    print("Invoking '%s'" % ' '.join(cmd))
    print('')
    basepath = os.path.dirname(__file__)
    cmd[0] = os.path.join(basepath, cmd[0])
    module = imp.load_source('script', cmd[0])
    rc = module.main(cmd[1:])
    if rc:
        sys.exit(rc)
    print('')


if __name__ == '__main__':
    main()
