#!/usr/bin/env python3

import argparse
from em import BANGPATH_OPT
import sys

from ros_buildfarm import templates
from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_repository_name
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.devel_job import configure_devel_job
from ros_buildfarm.devel_job import get_devel_job_name
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    global templates
    parser = argparse.ArgumentParser(
        description="Generate a 'devel' script")
    add_argument_rosdistro_index_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'source')
    add_argument_repository_name(parser)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)
    args = parser.parse_args(argv)

    # collect all template snippets of specific types
    scms = []
    scripts = []

    def template_hook(template_name, data, content):
        if template_name == 'snippet/scm.xml.em':
            scms.append((data['repo_spec'], data['path']))
        if template_name == 'snippet/builder_shell.xml.em':
            scripts.append(data['script'])
    templates.template_hook = template_hook

    configure_devel_job(
        args.rosdistro_index_url, args.rosdistro_name, args.source_build_name,
        args.repository_name, args.os_name, args.os_code_name, args.arch,
        jenkins=False, view=False)

    templates.template_hook = None

    devel_job_name = get_devel_job_name(
        args.rosdistro_name, args.source_build_name,
        args.repository_name, args.os_name, args.os_code_name, args.arch)
    value = expand_template(
        'devel/devel_script.sh.em', {
            'devel_job_name': devel_job_name,
            'scms': scms,
            'scripts': scripts},
        options={BANGPATH_OPT: False})
    print(value)


if __name__ == '__main__':
    sys.exit(main())
