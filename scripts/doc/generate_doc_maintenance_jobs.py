#!/usr/bin/env python3

import argparse
import os
import sys

from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.common import get_doc_view_name
from ros_buildfarm.common import \
    get_repositories_and_script_generating_key_files
from ros_buildfarm.config import get_doc_build_files
from ros_buildfarm.config import get_index
from ros_buildfarm.config.doc_build_file import DOC_TYPE_ROSDOC
from ros_buildfarm.git import get_repository
from ros_buildfarm.jenkins import configure_job
from ros_buildfarm.jenkins import configure_management_view
from ros_buildfarm.jenkins import connect
from ros_buildfarm.jenkins_credentials import get_relative_credential_path
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate the 'doc' management jobs on Jenkins")
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'doc')
    args = parser.parse_args(argv)

    config = get_index(args.config_url)
    build_files = get_doc_build_files(config, args.rosdistro_name)
    build_file = build_files[args.doc_build_name]

    if build_file.documentation_type != DOC_TYPE_ROSDOC:
        print(("The doc build file '%s' has the wrong documentation type to " +
               "be used with this script") % args.doc_build_name,
              file=sys.stderr)
        return 1

    jenkins = connect(config.jenkins_url)
    configure_management_view(jenkins)
    group_name = get_doc_view_name(
        args.rosdistro_name, args.doc_build_name)

    configure_reconfigure_jobs_job(
        jenkins, group_name, args, config, build_file)
    configure_trigger_jobs_job(jenkins, group_name, build_file)


def configure_reconfigure_jobs_job(
        jenkins, group_name, args, config, build_file):
    job_config = get_reconfigure_jobs_job_config(args, config, build_file)
    job_name = '%s_%s' % (group_name, 'reconfigure-jobs')
    configure_job(jenkins, job_name, job_config)


def get_reconfigure_jobs_job_config(args, config, build_file):
    template_name = 'doc/doc_reconfigure-jobs_job.xml.em'

    repository_args, script_generating_key_files = \
        get_repositories_and_script_generating_key_files(config=config)

    job_data = {
        'script_generating_key_files': script_generating_key_files,

        'config_url': args.config_url,
        'rosdistro_name': args.rosdistro_name,
        'doc_build_name': args.doc_build_name,
        'repository_args': repository_args,

        'ros_buildfarm_repository': get_repository(),

        'credentials_src': os.path.join(
            '~', os.path.dirname(get_relative_credential_path())),
        'credentials_dst': os.path.join(
            '/home/buildfarm',
            os.path.dirname(get_relative_credential_path())),

        'recipients': build_file.notify_emails,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


def configure_trigger_jobs_job(
        jenkins, group_name, build_file):
    job_config = get_trigger_jobs_job_config(group_name, build_file)
    job_name = '%s_%s' % (group_name, 'trigger-jobs')
    configure_job(jenkins, job_name, job_config)


def get_trigger_jobs_job_config(group_name, build_file):
    template_name = 'snippet/trigger-jobs_job.xml.em'
    job_data = {
        'has_force_parameter': True,
        'project_name_pattern': '%s__.*' % group_name,
        'recipients': build_file.notify_emails,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


if __name__ == '__main__':
    main()
