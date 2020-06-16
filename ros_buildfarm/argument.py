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

from __future__ import print_function

import argparse
from collections import OrderedDict
import os

from ros_buildfarm.config import get_index as get_config_index


def add_argument_config_url(parser, action=None):
    parser.add_argument(
        'config_url',
        action=action,
        help='The url of the ROS buildfarm configuration index')


def add_argument_rosdistro_index_url(parser, required=False):
    help_msg = 'The URL to the ROS distro index'
    if not required:
        from rosdistro import get_index_url
        parser.add_argument(
            '--rosdistro-index-url',
            default=get_index_url(),
            help=("%s (default: '%s', based on the environment variable " +
                  "ROSDISTRO_INDEX_URL") % (help_msg, get_index_url()))
    else:
        parser.add_argument(
            '--rosdistro-index-url',
            required=True,
            help=help_msg)


def add_argument_rosdistro_name(parser, action=None):
    parser.add_argument(
        'rosdistro_name',
        action=action,
        help="The name of the ROS distro from the index")


def add_argument_other_rosdistro_name(parser):
    parser.add_argument(
        'other_rosdistro_name',
        help="The name of the other ROS distro from the index")


def add_argument_older_rosdistro_names(parser):
    parser.add_argument(
        'older_rosdistro_names',
        nargs='+',
        help='List of older rosdistro names to compare with')


def add_argument_build_name(parser, build_file_type, nargs=None, action=None):
    parser.add_argument(
        '%s_build_name' % build_file_type,
        action=action, nargs=nargs,
        help="The name / key of the '%s-build' file from the index" %
             build_file_type)


def add_argument_env_vars(parser):
    parser.add_argument(
        '--env-vars', action=OrderedDictAction,
        nargs='*', default=OrderedDict(),
        help="Environment variables as 'key=value' for Dockerfile "
             'ENV directives')


def add_argument_repository_name(parser):
    parser.add_argument(
        'repository_name',
        help="The name of the 'repository' from the distribution file")


def add_argument_package_name(parser):
    parser.add_argument(
        'package_name',
        help="The name of the 'package' from the distribution file")


def add_argument_os_name(parser):
    parser.add_argument(
        'os_name',
        help='An OS name from the build file')


def add_argument_os_code_name(parser):
    parser.add_argument(
        'os_code_name',
        help='An OS code name from the build file')


def add_argument_arch(parser):
    parser.add_argument(
        'arch',
        help='An architecture from the build file')


def add_argument_source_dir(parser):
    parser.add_argument(
        '--source-dir',
        required=True,
        help='The path to the package sources')


def add_argument_sourcepkg_dir(parser):
    parser.add_argument(
        '--sourcepkg-dir', '--sourcedeb-dir',
        required=True,
        help='The path to the source package')


def add_argument_binarypkg_dir(parser):
    parser.add_argument(
        '--binarypkg-dir', '--binarydeb-dir',
        required=True,
        help='The path to the binary package')


def add_argument_skip_download_sourcepkg(parser):
    parser.add_argument(
        '--skip-download-sourcepkg', '--skip-download-sourcedeb',
        action='store_true',
        help='Skip downloading source package and expect it to be already there')


def add_argument_append_timestamp(parser):
    parser.add_argument(
        '--append-timestamp',
        action='store_true',
        help='Append timestamp to binary package version')


def add_argument_output_dir(parser, required=False):
    parser.add_argument(
        '--output-dir',
        default=os.curdir,
        required=required,
        help='The output directory')


def add_argument_dockerfile_dir(parser):
    parser.add_argument(
        '--dockerfile-dir',
        default=os.curdir,
        help="The directory where the 'Dockerfile' will be generated")


def add_argument_debian_repository_urls(parser, nargs='+'):
    parser.add_argument(
        'debian_repository_urls',
        nargs=nargs,
        help='The URLs of Debian repositories')


def add_argument_distribution_repository_urls(parser):
    parser.add_argument(
        '--distribution-repository-urls',
        nargs='*',
        default=[],
        help='The list of distribution repository URLs to use for installing '
             'dependencies')


def add_argument_distribution_repository_key_files(parser):
    parser.add_argument(
        '--distribution-repository-key-files',
        nargs='*',
        default=[],
        help='The list of distribution repository key files to verify the '
             'corresponding URLs')


def add_argument_target_repository(parser):
    parser.add_argument(
        '--target-repository',
        help='The target repository where generated packages are pushed to')


def add_argument_custom_rosdep_update_options(parser):
    parser.add_argument(
        '--custom-rosdep-update-options',
        nargs='*',
        default=[],
        help='A list of custom rosdep update options')


def add_argument_custom_rosdep_urls(parser):
    parser.add_argument(
        '--custom-rosdep-urls',
        nargs='*',
        default=[],
        help='The list of custom rosdep URLs to use for installing '
             'dependencies')


def add_argument_cache_dir(parser, default=None):
    parser.add_argument(
        '--cache-dir',
        default=default,
        required=default is None,
        help='The cache directory')


def add_argument_missing_only(parser):
    parser.add_argument(
        '--missing-only',
        action='store_true',
        help='Only trigger jobs with missing artifacts')


def add_argument_source_only(parser):
    parser.add_argument(
        '--source-only',
        action='store_true',
        help='Only trigger source jobs')


def add_argument_not_failed_only(parser):
    parser.add_argument(
        '--not-failed-only',
        action='store_true',
        help='Only trigger jobs for which the previous build did not fail')


def add_argument_os_code_name_and_arch_tuples(parser, required=True):
    class _AddUbuntuTupleAction(argparse.Action):

        def __call__(self, parser, args, values, option_string=None):
            import sys
            print('WARNING: ' + self.help, file=sys.stderr)
            for value in values:
                if value.count(':') != 1:
                    raise argparse.ArgumentError(
                        argument=self,
                        message='expected 2 parts separated by colons')
            setattr(
                args, 'os_name_and_os_code_name_and_arch_tuples',
                [('ubuntu:' + value).split(':') for value in values])
            setattr(args, self.dest, values)

    parser.add_argument(
        '--os-code-name-and-arch-tuples',
        nargs='+',
        required=required, action=_AddUbuntuTupleAction,
        help="DEPRECATED: Use '--os-name-and-os-code-name-and-arch-tuples'")


def add_argument_os_name_and_os_code_name_and_arch_tuples(parser, required=True):
    parser.add_argument(
        '--os-name-and-os-code-name-and-arch-tuples',
        nargs='+', metavar='OS_NAME:OS_CODE_NAME:ARCH',
        required=required, action=colon_separated_tuple_action(3),
        help='The colon separated tuple containing an OS name, OS code name, ' +
             "and an architecture (e.g. 'ubuntu:focal:amd64')")


def add_argument_output_name(parser):
    parser.add_argument(
        '--output-name',
        required=True,
        help='The name of the generated file (without the extensions)')


def add_argument_cause(parser):
    parser.add_argument(
        '--cause',
        help='The cause of the build trigger')


def add_argument_groovy_script(parser):
    parser.add_argument(
        '--groovy-script',
        help='The path of the generated groovy script file')


def add_argument_force(parser):
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force running the documentation generation')


def add_argument_vcs_information(parser):
    parser.add_argument(
        '--vcs-info',
        required=True,
        help='The vcs type, version and url separated by a space')


def add_argument_dry_run(parser):
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Only show the changes without apply them to Jenkins')


def add_argument_package_names(parser):
    parser.add_argument(
        '--package-names',
        nargs='+',
        help='A space separated list of package names')


def add_argument_repository_names(parser, optional=False):
    parser.add_argument(
        '--repository-names',
        nargs='*' if optional else '+',
        help='A space separated list of repository names')


def add_argument_build_tool(parser, required=False):
    default_help = '' if required else ' (default: as set in the build file)'
    parser.add_argument(
        '--build-tool',
        choices=('catkin_make_isolated', 'colcon'),
        required=required,
        help='The build tool to use' + default_help)


def add_argument_ros_version(parser):
    parser.add_argument(
        '--ros-version', type=int, required=True,
        help='The major ROS version')


def add_argument_install_apt_packages(parser):
    parser.add_argument(
        '--install-apt-packages',
        nargs='*',
        default=[],
        help='The list of packages to install with apt')


def add_argument_install_pip_packages(parser):
    parser.add_argument(
        '--install-pip-packages',
        nargs='*',
        default=[],
        help='The list of packages to install with pip')


def add_argument_install_packages(parser):
    parser.add_argument(
        '--install-packages', nargs='*',
        help='The specified package(s) will be installed prior to any '
             'packages detected for installation by rosdep.')


def add_argument_invalidate(parser):
    parser.add_argument(
        '--invalidate', action='store_true',
        help='Invalidate or remove any packages which recursively '
             'depend on the target package(s).')


def add_argument_package_selection_args(parser):
    return parser.add_argument(
        '--package-selection-args', nargs=argparse.REMAINDER,
        help='Package selection arguments passed to colcon '
             'to specify which packages should be built and tested.')


def add_argument_build_tool_args(parser):
    return parser.add_argument(
        '--build-tool-args', nargs=argparse.REMAINDER,
        help='Arbitrary arguments passed to the build tool.')


def add_argument_build_tool_test_args(parser):
    return parser.add_argument(
        '--build-tool-test-args', nargs=argparse.REMAINDER,
        help='Arbitrary arguments passed to the build tool during testing.')


def add_argument_pulp_base_url(parser):
    from_env = os.environ.get('PULP_BASE_URL')
    return parser.add_argument(
        '--pulp-base-url',
        default=from_env, required=not bool(from_env),
        help='URL of the pulp API endpoint')


def add_argument_pulp_distribution_name(parser):
    return parser.add_argument(
        '--pulp-distribution-name', required=True,
        help='Name of the pulp distribution to target with changes')


def add_argument_pulp_password(parser):
    from_env = os.environ.get('PULP_PASSWORD')
    return parser.add_argument(
        '--pulp-password',
        default=from_env, required=not bool(from_env),
        help='Password used to access the pulp API endpoint')


def add_argument_pulp_resource_record(parser):
    return parser.add_argument(
        '--pulp-resource-record', default=None, metavar='FILE',
        help='File in which to record the pulp HREFs of package resources')


def add_argument_pulp_task_timeout(parser):
    return parser.add_argument(
        '--pulp-task-timeout',
        default=60.0,
        help='Duration to wait (in seconds) for a pulp task to complete')


def add_argument_pulp_username(parser):
    from_env = os.environ.get('PULP_USERNAME')
    return parser.add_argument(
        '--pulp-username',
        default=from_env, required=not bool(from_env),
        help='Username used to access the pulp API endpoint')


def add_argument_repos_file_urls(parser):
    parser.add_argument(
        '--repos-file-urls', nargs='*', metavar='URL',
        help='URLs of repos files to import with vcs.')


def add_argument_run_abichecker(parser):
    parser.add_argument(
        '--run-abichecker', action='store_true',
        help='Run the ABI checker when compiling packages')


def add_argument_require_gpu_support(parser):
    parser.add_argument(
        '--require-gpu-support', action='store_true',
        help='GPU acceleration is needed in the build container')


def add_argument_skip_cleanup(parser):
    parser.add_argument(
        '--skip-cleanup', action='store_true',
        help='Skip cleanup of build artifacts')


def add_argument_skip_rosdep_keys(parser):
    parser.add_argument(
        '--skip-rosdep-keys', nargs='*',
        help='The specified rosdep keys will be ignored, i.e. not resolved '
             'and not installed.')


def add_argument_test_branch(parser):
    parser.add_argument(
        '--test-branch', default=None,
        help='Branch to attempt to checkout before doing batch job.')


def add_argument_testing(parser):
    parser.add_argument(
        '--testing', action='store_true',
        help='Generate a task for testing packages rather than installing '
             'them.')


def add_argument_return_zero(parser):
    parser.add_argument(
        '--return-zero', action='store_true',
        help='Always return zero, success, even if there are errors. '
             'This is used for testing, and scripting. It is not generally'
             ' recommended for use.')


def check_len_action(minargs, maxargs):
    class CheckLength(argparse.Action):

        def __call__(self, parser, args, values, option_string=None):
            if len(values) < minargs:
                raise argparse.ArgumentError(
                    argument=self,
                    message='expected at least %s arguments' % (minargs))
            elif len(values) > maxargs:
                raise argparse.ArgumentError(
                    argument=self,
                    message='expected at most %s arguments' % (minargs))
            setattr(args, self.dest, values)
    return CheckLength


def colon_separated_tuple_action(numparts):
    class ColonSeparatedTupleAction(argparse.Action):

        def __call__(self, parser, args, values, option_string=None):
            for value in values:
                if value.count(':') + 1 != numparts:
                    raise argparse.ArgumentError(
                        argument=self,
                        message='expected %d parts separated by colons' % (numparts))
                setattr(args, self.dest, [value.split(':') for value in values])
    return ColonSeparatedTupleAction


def extract_multiple_remainders(argv, arguments):
    # the following logic only works for arguments with a single option string
    for a in arguments:
        assert len(a.option_strings) == 1
    indexes = {
        argv.index(a.option_strings[0]): a
        for a in arguments if a.option_strings[0] in argv}
    remainders = {}
    # only necessary if there is more than one remainder argument
    # otherwise argparse can handle it just fine
    if len(indexes) > 1:
        for index in sorted(indexes.keys(), reverse=True):
            argument = indexes[index]
            remainders[argument.dest] = argv[index + 1:]
            del argv[index:]
    return remainders


class OrderedDictAction(argparse.Action):

    def __call__(self, parser, args, values, option_string=None):
        dest = OrderedDict()
        for value in values:
            value_parts = value.split('=', 1)
            if len(value_parts) != 2:
                raise argparse.ArgumentError(
                    argument=self,
                    message="invalid key/value pair: '%s'" % value)
            dest[value_parts[0].strip()] = value_parts[1].strip()
        setattr(args, self.dest, dest)


def build_tool_args_epilog_action(build_file_type, build_file_getter):
    build_name = '%s_build_name' % build_file_type

    class BuildToolArgsEpilogAction(argparse.Action):

        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, values)
            if None not in (
                getattr(namespace, 'rosdistro_name', None),
                getattr(namespace, 'config_url', None),
                getattr(namespace, build_name, None),
            ):
                try:
                    config = get_config_index(namespace.config_url)
                    build_files = build_file_getter(config, namespace.rosdistro_name)
                    build_file = build_files[getattr(namespace, build_name)]

                    if parser.epilog is None:
                        parser.epilog = ''
                    elif parser.epilog:
                        parser.epilog = parser.epilog.rstrip('\r\n') + '\n\n'
                    parser.epilog += '\n'.join([
                        'default build tool arguments:',
                        '  --build-tool-args ' + (build_file.build_tool_args or '(none)'),
                        '  --build-tool-test-args ' + (build_file.build_tool_test_args or '(none)'),
                    ])
                except Exception:
                    pass
    return BuildToolArgsEpilogAction
