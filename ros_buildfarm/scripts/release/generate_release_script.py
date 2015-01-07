#!/usr/bin/env python3

import argparse
from em import BANGPATH_OPT
import sys

from ros_buildfarm import templates
from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_package_name
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.release_job import configure_release_job
from ros_buildfarm.release_job import get_binarydeb_job_name
from ros_buildfarm.release_job import get_sourcedeb_job_name
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    global templates
    parser = argparse.ArgumentParser(
        description="Generate a 'release' script")
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'release')
    add_argument_package_name(parser)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)
    parser.add_argument(
        '--skip-install',
        action='store_true',
        help='Skip trying to install binarydeb')
    args = parser.parse_args(argv)

    # collect all template snippets of specific types
    scripts = []

    def template_hook(template_name, data, content):
        if template_name == 'release/sourcedeb_job.xml.em':
            # add separator after finishing source part
            scripts.append('--')
        if template_name == 'snippet/builder_shell.xml.em':
            scripts.append(data['script'])
    templates.template_hook = template_hook

    configure_release_job(
        args.config_url, args.rosdistro_name, args.release_build_name,
        args.package_name, args.os_name, args.os_code_name,
        jenkins=False, view=False, generate_import_package_job=False,
        filter_arches=args.arch)

    templates.template_hook = None

    source_job_name = get_sourcedeb_job_name(
        args.rosdistro_name, args.release_build_name,
        args.package_name, args.os_name, args.os_code_name)

    binary_job_name = get_binarydeb_job_name(
        args.rosdistro_name, args.release_build_name,
        args.package_name, args.os_name, args.os_code_name, args.arch)

    separator_index = scripts.index('--')
    source_scripts = scripts[:separator_index]
    binary_scripts = scripts[separator_index + 1:]

    # inject additional argument to skip fetching sourcedeb from repo
    script_name = '/run_binarydeb_job.py '
    additional_argument = '--skip-download-sourcedeb '
    for i, script in enumerate(binary_scripts):
        offset = script.find(script_name)
        if offset != -1:
            offset += len(script_name)
            script = script[:offset] + additional_argument + script[offset:]
            binary_scripts[i] = script
            break

    # remove rm command for sourcedeb location
    rm_command = 'rm -fr $WORKSPACE/binarydeb'
    for i, script in enumerate(binary_scripts):
        offset = script.find(rm_command)
        if offset != -1:
            script = script[:offset] + script[offset + len(rm_command):]
            binary_scripts[i] = script
            break

    if args.skip_install:
        # remove install step
        script_name = '/create_binarydeb_install_task_generator.py '
        for i, script in enumerate(binary_scripts):
            offset = script.find(script_name)
            if offset != -1:
                del binary_scripts[i]
                break

    value = expand_template(
        'release/release_script.sh.em', {
            'source_job_name': source_job_name,
            'binary_job_name': binary_job_name,
            'source_scripts': source_scripts,
            'binary_scripts': binary_scripts},
        options={BANGPATH_OPT: False})
    print(value)


if __name__ == '__main__':
    sys.exit(main())
