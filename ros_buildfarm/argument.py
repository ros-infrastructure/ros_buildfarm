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

import os


def add_argument_config_url(parser):
    parser.add_argument(
        'config_url',
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


def add_argument_rosdistro_name(parser):
    parser.add_argument(
        'rosdistro_name',
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


def add_argument_build_name(parser, build_file_type):
    parser.add_argument(
        '%s_build_name' % build_file_type,
        help="The name / key of the '%s-build' file from the index" %
             build_file_type)


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


def add_argument_sourcedeb_dir(parser):
    parser.add_argument(
        '--sourcedeb-dir',
        required=True,
        help='The path to the package sourcedeb')


def add_argument_binarydeb_dir(parser):
    parser.add_argument(
        '--binarydeb-dir',
        required=True,
        help='The path to the package binarydeb')


def add_argument_skip_download_sourcedeb(parser):
    parser.add_argument(
        '--skip-download-sourcedeb',
        action='store_true',
        help='Skip downloading sourcedeb and expect it to be already there')


def add_argument_append_timestamp(parser):
    parser.add_argument(
        '--append-timestamp',
        action='store_true',
        help='Append timestamp to binarydeb version')


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


def add_argument_os_code_name_and_arch_tuples(parser):
    parser.add_argument(
        '--os-code-name-and-arch-tuples',
        nargs='+',
        required=True,
        help="The colon separated tuple containing an OS code name and an " +
             "architecture (e.g. 'trusty:amd64')")


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


def add_argument_repository_names(parser):
    parser.add_argument(
        '--repository-names',
        nargs='+',
        help='A space separated list of repository names')
