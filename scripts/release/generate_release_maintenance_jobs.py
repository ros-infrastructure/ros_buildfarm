#!/usr/bin/env python3

import argparse
from datetime import datetime
import os
import sys

from rosdistro import get_index
from rosdistro import get_release_build_files

from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.common import \
    get_apt_mirrors_and_script_generating_key_files
from ros_buildfarm.common import get_release_view_name
from ros_buildfarm.git import get_repository_url
from ros_buildfarm.jenkins import configure_job
from ros_buildfarm.jenkins import configure_view
from ros_buildfarm.jenkins import connect
from ros_buildfarm.jenkins import JENKINS_MANAGEMENT_VIEW
from ros_buildfarm.jenkins_credentials import get_relative_credential_path
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate the 'release' management jobs on Jenkins")
    add_argument_rosdistro_index_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'release')
    args = parser.parse_args(argv)

    index = get_index(args.rosdistro_index_url)
    build_files = get_release_build_files(index, args.rosdistro_name)
    build_file = build_files[args.release_build_name]

    reconfigure_jobs_job_config = get_reconfigure_jobs_job_config(
        args, build_file)
    trigger_jobs_job_config = get_trigger_jobs_job_config(
        args, build_file)
    import_upstream_job_config = get_import_upstream_job_config(
        args, build_file)

    jenkins = connect(build_file.jenkins_url)

    view = configure_view(jenkins, JENKINS_MANAGEMENT_VIEW)

    group_name = get_release_view_name(
        args.rosdistro_name, args.release_build_name)

    job_name = '%s_%s' % (group_name, 'reconfigure-jobs')
    configure_job(jenkins, job_name, reconfigure_jobs_job_config, view=view)

    job_name = '%s_%s' % (group_name, 'trigger-jobs')
    configure_job(jenkins, job_name, trigger_jobs_job_config, view=view)

    job_name = 'import_upstream'
    configure_job(jenkins, job_name, import_upstream_job_config, view=view)


def get_reconfigure_jobs_job_config(args, build_file):
    template_name = 'release/release_reconfigure-jobs_job.xml.em'
    return _get_job_config(args, build_file, template_name)


def get_trigger_jobs_job_config(args, build_file):
    template_name = 'release/release_trigger-jobs_job.xml.em'
    return _get_job_config(args, build_file, template_name)


def get_import_upstream_job_config(args, build_file):
    template_name = 'release/import_upstream_job.xml.em'
    return _get_job_config(args, build_file, template_name)


def _get_job_config(args, build_file, template_name):
    now = datetime.utcnow()
    now_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    conf = build_file.get_target_configuration()
    apt_mirror_args, script_generating_key_files = \
        get_apt_mirrors_and_script_generating_key_files(conf)

    job_data = {
        'template_name': template_name,
        'now_str': now_str,

        'script_generating_key_files': script_generating_key_files,

        'rosdistro_index_url': args.rosdistro_index_url,
        'rosdistro_name': args.rosdistro_name,
        'release_build_name': args.release_build_name,
        'apt_mirror_args': apt_mirror_args,

        'ros_buildfarm_url': get_repository_url('.'),

        'credentials_src': os.path.join(
            '/var/lib/jenkins',
            os.path.dirname(get_relative_credential_path())),
        'credentials_dst': os.path.join(
            '/home/buildfarm',
            os.path.dirname(get_relative_credential_path())),

        'recipients': build_file.notify_emails,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


if __name__ == '__main__':
    main()
