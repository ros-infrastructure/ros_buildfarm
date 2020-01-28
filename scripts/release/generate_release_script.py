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
import sys

from em import BANGPATH_OPT
from em import Hook
from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_package_name
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.common import get_binarydeb_job_name
from ros_buildfarm.common import get_sourcedeb_job_name
from ros_buildfarm.release_job import configure_release_job
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
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
    class IncludeHook(Hook):

        def __init__(self):
            Hook.__init__(self)
            self.scripts = []

        def beforeFile(self, *args, **kwargs):
            template_path = kwargs['file'].name
            if template_path.endswith('/release/deb/binarypkg_job.xml.em'):
                self.scripts.append('--')

        def beforeInclude(self, *args, **kwargs):
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
                self.scripts.append(script)

    hook = IncludeHook()
    from ros_buildfarm import templates
    templates.template_hooks = [hook]

    configure_release_job(
        args.config_url, args.rosdistro_name, args.release_build_name,
        args.package_name, args.os_name, args.os_code_name,
        jenkins=False, views=[], generate_import_package_job=False,
        generate_sync_packages_jobs=False, filter_arches=args.arch)

    templates.template_hooks = None

    source_job_name = get_sourcedeb_job_name(
        args.rosdistro_name, args.release_build_name,
        args.package_name, args.os_name, args.os_code_name)

    binary_job_name = get_binarydeb_job_name(
        args.rosdistro_name, args.release_build_name,
        args.package_name, args.os_name, args.os_code_name, args.arch)

    separator_index = hook.scripts.index('--')
    source_scripts = hook.scripts[:separator_index]
    binary_scripts = hook.scripts[separator_index + 1:]

    # inject additional argument to skip fetching sourcedeb from repo
    script_name = '/run_binarydeb_job.py '
    additional_argument = '--skip-download-sourcepkg '
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
    value = value.replace('python3', sys.executable)
    print(value)


if __name__ == '__main__':
    sys.exit(main())
