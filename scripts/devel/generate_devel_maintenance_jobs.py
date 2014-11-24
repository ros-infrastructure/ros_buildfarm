#!/usr/bin/env python3

import argparse
from datetime import datetime
import os
import sys

from rosdistro import get_index
from rosdistro import get_source_build_files

from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.common import \
    get_apt_mirrors_and_script_generating_key_files
from ros_buildfarm.common import get_devel_view_name
from ros_buildfarm.git import get_ros_buildfarm_url
from ros_buildfarm.jenkins import configure_job
from ros_buildfarm.jenkins import configure_view
from ros_buildfarm.jenkins import connect
from ros_buildfarm.jenkins import JENKINS_MANAGEMENT_VIEW
from ros_buildfarm.jenkins_credentials import get_relative_credential_path
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate the 'devel' management jobs on Jenkins")
    add_argument_rosdistro_index_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'source')
    args = parser.parse_args(argv)

    index = get_index(args.rosdistro_index_url)
    build_files = get_source_build_files(index, args.rosdistro_name)
    build_file = build_files[args.source_build_name]

    jenkins = connect(build_file.jenkins_url)
    view = configure_view(jenkins, JENKINS_MANAGEMENT_VIEW)
    group_name = get_devel_view_name(
        args.rosdistro_name, args.source_build_name)

    configure_reconfigure_jobs_job(jenkins, view, group_name, args, build_file)
    configure_trigger_jobs_job(jenkins, view, group_name, build_file)


def configure_reconfigure_jobs_job(
        jenkins, view, group_name, args, build_file):
    job_config = get_reconfigure_jobs_job_config(args, build_file)
    job_name = '%s_%s' % (group_name, 'reconfigure-jobs')
    configure_job(jenkins, job_name, job_config, view=view)


def get_reconfigure_jobs_job_config(args, build_file):
    template_name = 'devel/devel_reconfigure-jobs_job.xml.em'
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
        'source_build_name': args.source_build_name,
        'apt_mirror_args': apt_mirror_args,

        'ros_buildfarm_url': get_ros_buildfarm_url(),

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


def configure_trigger_jobs_job(
        jenkins, view, group_name, build_file):
    job_config = get_trigger_jobs_job_config(group_name, build_file)
    job_name = '%s_%s' % (group_name, 'trigger-jobs')
    configure_job(jenkins, job_name, job_config, view=view)


def get_trigger_jobs_job_config(group_name, build_file):
    template_name = 'devel/devel_trigger-jobs_job.xml.em'
    now = datetime.utcnow()
    now_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    job_data = {
        'template_name': template_name,
        'now_str': now_str,

        'project_name_pattern': '%s__.*' % group_name,

        'recipients': build_file.notify_emails,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


if __name__ == '__main__':
    main()
