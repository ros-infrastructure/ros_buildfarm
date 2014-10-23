#!/usr/bin/env python3

import argparse
from datetime import datetime
import sys

from rosdistro import get_index
from rosdistro import get_source_build_files

from ros_buildfarm.devel_job import add_arguments_for_source_build_file
from ros_buildfarm.git import get_repository_url
from ros_buildfarm.jenkins import configure_job
from ros_buildfarm.jenkins import configure_view
from ros_buildfarm.jenkins import connect
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate the 'devel' management jobs on Jenkins")
    add_arguments_for_source_build_file(parser)
    args = parser.parse_args(argv)

    index = get_index(args.rosdistro_index_url)
    build_files = get_source_build_files(index, args.rosdistro)
    build_file = build_files[args.source_build]

    job_config = get_job_config(args, build_file)

    jenkins = connect(build_file.jenkins_url)

    view_name = '%sdev%s' % (args.rosdistro[0].upper(), args.source_build)
    view = configure_view(jenkins, view_name)

    job_name = '%s__%s' % (view_name, 'reconfigure-jobs')
    configure_job(jenkins, job_name, job_config, view=view)


def get_job_config(args, build_file):
    template_name = 'devel/devel_reconfigure-jobs_job.xml.em'
    now = datetime.utcnow()
    now_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    job_data = {
        'template_name': template_name,
        'now_str': now_str,

        'rosdistro_index_url': args.rosdistro_index_url,
        'rosdistro_name': args.rosdistro,
        'source_build_name': args.source_build,

        'ros_buildfarm_url': get_repository_url('.'),

        'recipients': build_file.notify_emails,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


if __name__ == '__main__':
    main()
