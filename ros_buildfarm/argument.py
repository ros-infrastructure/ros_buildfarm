def add_argument_rosdistro_index_url(parser, required=False):
    help_msg = 'The URL to the ROS distro index'
    if not required:
        from rosdistro import get_index_url
        parser.add_argument(
            '--rosdistro-index-url',
            default=get_index_url(),
            required=required,
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


def add_argument_build_name(parser, build_file_type):
    parser.add_argument(
        '%s_build_name' % build_file_type,
        help="The name of the '%s-build' file from the index" %
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
